
from flask import Blueprint, request, jsonify
from gtts import gTTS
import io
import tempfile
import os
import shutil

import whisper

bp = Blueprint("speech", __name__)

# Lazy-load a small Whisper model the first time we need it
_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        # Use a small CPU-friendly model to keep things lightweight.
        _whisper_model = whisper.load_model("tiny")
    return _whisper_model


@bp.route("/speak", methods=["POST"])
def speak():
    try:
        data = request.json
        text = data.get("text", "")
        language = data.get("language", "en")

        # Map frontend language codes to gTTS language codes
        language_map = {
            "en": "en",
            "te": "te",
            "hi": "hi",
            "ja": "ja",
            "zh": "zh-cn",
            "es": "es",
        }

        tts = gTTS(text=text, lang=language_map.get(language, "en"))

        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_io.seek(0)

        return audio_io.getvalue(), 200, {
            "Content-Type": "audio/mpeg",
            "Content-Disposition": "attachment; filename=speech.mp3",
        }

    except Exception as e:
        print(f"Error in speak: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route("/transcribe", methods=["POST"])
def transcribe():
    """
    Accepts an audio file (field name: 'audio') and returns JSON:
      { "text": "<transcribed text>" }
    
    Query parameter: ?language=<code> to specify the source language (e.g., "zh", "en", "hi").
    This helps Whisper transcribe more accurately by providing a language hint.
    
    Whisper language codes are ISO 639-1 (2-letter codes like "en", "zh", "hi", "te", "ja", "es").
    """
    try:
        # Whisper requires the ffmpeg binary to decode audio files.
        if shutil.which("ffmpeg") is None:
            return (
                jsonify(
                    {
                        "error": (
                            "ffmpeg is not installed or not available on PATH. "
                            "Install ffmpeg and restart the backend."
                        )
                    }
                ),
                500,
            )

        if "audio" not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        # Get language hint from query parameter (frontend sends selected source language)
        language_hint = request.args.get("language", None)
        
        # Map frontend short codes to Whisper language codes (ISO 639-1)
        # Most match, but some need conversion
        frontend_to_whisper = {
            "zh": "zh",  # Chinese
            "ja": "ja",  # Japanese
            "hi": "hi",  # Hindi
            "te": "te",  # Telugu
            "en": "en",  # English
            "es": "es",  # Spanish
            "ar": "ar",  # Arabic
            "de": "de",  # German
            "fr": "fr",  # French
            "it": "it",  # Italian
            "pt": "pt",  # Portuguese
            "ru": "ru",  # Russian
            "ko": "ko",  # Korean
            "vi": "vi",  # Vietnamese
            "th": "th",  # Thai
            "tr": "tr",  # Turkish
            "pl": "pl",  # Polish
            "nl": "nl",  # Dutch
            "id": "id",  # Indonesian
            "uk": "uk",  # Ukrainian
            "cs": "cs",  # Czech
            "ro": "ro",  # Romanian
            "sv": "sv",  # Swedish
            "fi": "fi",  # Finnish
            "he": "he",  # Hebrew
            "bn": "bn",  # Bengali
            "ta": "ta",  # Tamil
            "ur": "ur",  # Urdu
            "fa": "fa",  # Persian
            "mr": "mr",  # Marathi
            "gu": "gu",  # Gujarati
            "ml": "ml",  # Malayalam
            "ne": "ne",  # Nepali
            "si": "si",  # Sinhala
            "my": "my",  # Burmese
            "km": "km",  # Khmer
            "ka": "ka",  # Georgian
            "az": "az",  # Azerbaijani
            "kk": "kk",  # Kazakh
            "mn": "mn",  # Mongolian
            "ps": "ps",  # Pashto
            "sw": "sw",  # Swahili
            "xh": "xh",  # Xhosa
            "af": "af",  # Afrikaans
            "et": "et",  # Estonian
            "lv": "lv",  # Latvian
            "lt": "lt",  # Lithuanian
            "mk": "mk",  # Macedonian
            "sl": "sl",  # Slovene
            "hr": "hr",  # Croatian
            "gl": "gl",  # Galician
            "tl": "tl",  # Tagalog
        }
        
        whisper_lang = None
        if language_hint:
            whisper_lang = frontend_to_whisper.get(language_hint.lower())

        audio_file = request.files["audio"]

        # Save to a temporary file for Whisper to read
        with tempfile.TemporaryDirectory() as tmpdir:
            _, ext = os.path.splitext(audio_file.filename or "")
            ext = ext if ext else ".webm"
            tmp_path = os.path.join(tmpdir, f"input{ext}")
            audio_file.save(tmp_path)

            model = get_whisper_model()
            
            # Pass language hint to Whisper for better accuracy
            # If language is provided, Whisper will use it; otherwise it auto-detects
            transcribe_kwargs = {"fp16": False}
            if whisper_lang:
                transcribe_kwargs["language"] = whisper_lang
            
            result = model.transcribe(tmp_path, **transcribe_kwargs)

        text = result.get("text", "").strip()
        return jsonify({"text": text})

    except Exception as e:
        print(f"Error in transcribe: {str(e)}")
        return jsonify({"error": str(e)}), 500
