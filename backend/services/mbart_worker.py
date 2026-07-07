"""
Worker process for running mBART translation (offline).

Why a worker?
- On some Windows setups, torch/transformers can hard-crash the Python process
  (access violation) when loading or running large models.
- By isolating translation in a separate process, the Flask server can stay up
  and return a JSON error instead of resetting the connection.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

_STATE: Dict[str, Any] = {
    "tokenizer": None,
    "model": None,
    "generation_config": None,
}

_LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "mbart_worker.log"


def _log(msg: str) -> None:
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        _LOG_PATH.open("a", encoding="utf-8").write(f"[{ts}] {msg}\n")
    except Exception:
        # Logging must never crash the worker.
        pass


def _set_stability_env() -> None:
    # Reduce threading / OpenMP surprises on Windows.
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")


def init_worker(model_dir: str) -> None:
    """
    Initializer for the worker process. Loads tokenizer + model once and keeps
    them in-process for subsequent translation calls.
    """
    _set_stability_env()
    _log(f"init_worker: starting; pid={os.getpid()}; model_dir={model_dir}")

    model_path = Path(model_dir)
    if not model_path.exists():
        _log("init_worker: model dir missing")
        raise FileNotFoundError(f"mBART model folder not found at: {model_path}")

    # Import heavy deps only inside the worker process.
    _log("init_worker: importing torch/transformers")
    import torch
    from transformers import GenerationConfig, MBart50TokenizerFast, MBartForConditionalGeneration

    try:
        torch.set_num_threads(1)
    except Exception:
        pass

    try:
        torch.backends.mkldnn.enabled = False  # type: ignore[attr-defined]
        _log("init_worker: disabled mkldnn")
    except Exception:
        pass

    _log("init_worker: loading tokenizer")
    tokenizer = MBart50TokenizerFast.from_pretrained(str(model_path), local_files_only=True)
    _log("init_worker: tokenizer loaded")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float16 if device.type == "cuda" else torch.float32

    # Optional: if accelerate exists, device_map="auto" can reduce CPU peak RAM.
    device_map = None
    try:
        import accelerate  # noqa: F401

        device_map = "auto"
    except Exception:
        device_map = None

    # transformers 4.57 deprecates torch_dtype in favor of dtype; support both.
    model = None
    _log(f"init_worker: loading model; device={device.type}; dtype={dtype}; device_map={device_map}")
    try:
        model = MBartForConditionalGeneration.from_pretrained(
            str(model_path),
            local_files_only=True,
            low_cpu_mem_usage=True,
            dtype=dtype,
            device_map=device_map,
        )
    except TypeError:
        model = MBartForConditionalGeneration.from_pretrained(
            str(model_path),
            local_files_only=True,
            low_cpu_mem_usage=True,
            torch_dtype=dtype,
            device_map=device_map,
        )

    model.eval()
    if device_map is None:
        model.to(device)
    _log("init_worker: model loaded")

    generation_config = GenerationConfig.from_pretrained(str(model_path), local_files_only=True)
    _log("init_worker: generation_config loaded")

    _STATE["tokenizer"] = tokenizer
    _STATE["model"] = model
    _STATE["generation_config"] = generation_config
    _log("init_worker: ready")


def translate_text(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Translate `text` from `src_lang` to `tgt_lang` using already-loaded mBART.
    Language codes are mBART50 codes like: en_XX, hi_IN, te_IN, ja_XX, zh_CN, es_XX.
    
    Uses a context memory mechanism:
    - Splits text into sentences
    - Processes sentences sequentially
    - Maintains a sliding context buffer (last 2-3 sentences)
    - Includes context when translating each sentence for better coherence
    """
    if not text or not isinstance(text, str):
        raise ValueError("Invalid input text")

    tokenizer = _STATE.get("tokenizer")
    model = _STATE.get("model")
    generation_config = _STATE.get("generation_config")

    if tokenizer is None or model is None:
        raise RuntimeError("Translation worker not initialized (model/tokenizer missing)")

    if not hasattr(tokenizer, "lang_code_to_id"):
        raise RuntimeError("Loaded tokenizer does not support mBART language codes")

    if src_lang not in tokenizer.lang_code_to_id:
        raise ValueError(f"Unsupported source language code: {src_lang}")
    if tgt_lang not in tokenizer.lang_code_to_id:
        raise ValueError(f"Unsupported target language code: {tgt_lang}")

    import torch
    import re

    tokenizer.src_lang = src_lang
    
    max_input_length = 1024  # mBART-50's typical max input length
    max_output_length = 512  # Allow longer outputs than the default 200
    context_window_size = 2  # Number of previous sentences to include as context
    
    # Tokenize to check if entire text fits
    test_encoded = tokenizer(text, return_tensors="pt", truncation=False, add_special_tokens=True)
    input_length = len(test_encoded["input_ids"][0])
    
    # If entire text fits, translate directly (no context needed)
    if input_length <= max_input_length:
        # Split text into sentences while preserving sentence boundaries
        # Pattern: sentence ending (. ! ?) followed by whitespace or end of string
        sentence_pattern = r'([.!?]+(?:\s+|$))'
        parts = re.split(sentence_pattern, text)
        
        # Reconstruct sentences with their punctuation
        sentences = []
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and re.match(r'^[.!?]+', parts[i + 1]):
                # Sentence + punctuation
                sentences.append((parts[i] + parts[i + 1]).strip())
                i += 2
            else:
                if parts[i].strip():
                    sentences.append(parts[i].strip())
                i += 1
        
        # Filter out empty sentences
        sentences = [s for s in sentences if s.strip()]
        
        if not sentences:
            return ""
        
        # Context Memory Mechanism: Sequential translation with sliding context buffer
        model_device = next(model.parameters()).device
        forced_bos_token_id = tokenizer.lang_code_to_id[tgt_lang]
        translated_sentences = []
        context_buffer = []  # Stores recent source sentences for context
        
        for i, current_sentence in enumerate(sentences):
            if not current_sentence.strip():
                continue
            
            # Build context: include last N sentences + current sentence
            context_sentences = context_buffer[-context_window_size:] + [current_sentence]
            context_text = " ".join(context_sentences)
            
            # Check if context + current sentence fits within token limit
            context_encoded = tokenizer(context_text, return_tensors="pt", truncation=False, add_special_tokens=True)
            context_length = len(context_encoded["input_ids"][0])
            
            # If context is too long, reduce it or use just current sentence
            if context_length > max_input_length:
                # Try with just current sentence
                if len(context_buffer) > 0:
                    # Try with last 1 sentence + current
                    reduced_context = context_buffer[-1:] + [current_sentence]
                    reduced_text = " ".join(reduced_context)
                    reduced_encoded = tokenizer(reduced_text, return_tensors="pt", truncation=False, add_special_tokens=True)
                    if len(reduced_encoded["input_ids"][0]) <= max_input_length:
                        context_text = reduced_text
                    else:
                        # Just use current sentence if even that's too long
                        context_text = current_sentence
                else:
                    context_text = current_sentence
            
            # Translate with context
            encoded = tokenizer(context_text, return_tensors="pt", truncation=True, max_length=max_input_length)
            encoded = {k: (v.to(model_device) if isinstance(v, torch.Tensor) else v) for k, v in encoded.items()}
            
            with torch.no_grad():
                generated_tokens = model.generate(
                    **encoded,
                    forced_bos_token_id=forced_bos_token_id,
                    max_length=max_output_length,
                    num_beams=5,
                    early_stopping=True,
                )
            
            full_translation = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0].strip()
            
            # Extract only the current sentence's translation
            # Strategy: If we translated with context, the output includes all context sentences
            # We need to extract just the last sentence (current one)
            # Simple heuristic: split by sentence boundaries and take the last part
            if len(context_sentences) > 1:
                # Try to extract the last sentence from translation
                # Split translation by common sentence endings
                translation_parts = re.split(r'([.!?]+(?:\s+|$))', full_translation)
                # Take the last meaningful part (last sentence)
                if len(translation_parts) >= 2:
                    # Last sentence is typically the last 2 parts (text + punctuation)
                    current_translation = "".join(translation_parts[-2:]).strip()
                else:
                    # Fallback: use the full translation
                    current_translation = full_translation
            else:
                # No context, use full translation
                current_translation = full_translation
            
            translated_sentences.append(current_translation)
            
            # Update context buffer: add current sentence (keep last N sentences)
            context_buffer.append(current_sentence)
            if len(context_buffer) > context_window_size:
                context_buffer.pop(0)
        
        # Join all translated sentences
        return " ".join(translated_sentences)
    
    # For shorter text, translate directly
    encoded = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_input_length)

    # Move tensors to model device.
    model_device = next(model.parameters()).device
    encoded = {k: (v.to(model_device) if isinstance(v, torch.Tensor) else v) for k, v in encoded.items()}

    forced_bos_token_id = tokenizer.lang_code_to_id[tgt_lang]

    with torch.no_grad():
        generated_tokens = model.generate(
            **encoded,
            forced_bos_token_id=forced_bos_token_id,
            max_length=max_output_length,  # Override generation_config's 200 limit
            num_beams=5,
            early_stopping=True,
        )

    out = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
    return (out[0] if out else "").strip()


