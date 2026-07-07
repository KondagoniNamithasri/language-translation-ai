
"""
Local mBART translation service (offline).

This repo ships with a local copy of:
  facebook/mbart-large-50-many-to-many-mmt
under `backend/models/mbart_model/`.

To keep the Flask server startup snappy (and reduce crash risk on Windows),
we lazy-load torch + transformers + the model on the first translation request.

Additionally, on some Windows machines torch can hard-crash the Python process
(access violation) while loading/running large models. To prevent the Flask
server from dying (causing `ERR_CONNECTION_RESET` in the browser), we run the
translation inside a separate worker process and automatically restart it if
the worker crashes.
"""

from __future__ import annotations

import os
from pathlib import Path
import threading
from typing import Optional

from concurrent.futures import ProcessPoolExecutor, TimeoutError
from concurrent.futures.process import BrokenProcessPool
import multiprocessing as mp

from services.mbart_worker import init_worker, translate_text


class TranslationService:
    def __init__(self) -> None:
        self._pool_lock = threading.Lock()
        self._pool: Optional[ProcessPoolExecutor] = None

        self._model_dir = (
            Path(__file__).resolve().parent.parent / "models" / "mbart_model"
        )

    def _ensure_pool(self) -> ProcessPoolExecutor:
        # Double-checked locking to avoid multiple worker startups under load.
        if self._pool is not None:
            return self._pool

        with self._pool_lock:
            if self._pool is not None:
                return self._pool

            if not self._model_dir.exists():
                raise FileNotFoundError(f"mBART model folder not found at: {self._model_dir}")

            # Use spawn context explicitly (Windows default) for clarity.
            ctx = mp.get_context("spawn")

            # Single worker is enough; translation is GPU/CPU heavy and we want
            # to keep memory usage predictable.
            self._pool = ProcessPoolExecutor(
                max_workers=1,
                mp_context=ctx,
                initializer=init_worker,
                initargs=(str(self._model_dir),),
            )
            return self._pool

    def _reset_pool(self) -> None:
        with self._pool_lock:
            if self._pool is not None:
                try:
                    self._pool.shutdown(wait=False, cancel_futures=True)
                except Exception:
                    pass
            self._pool = None

    def translate(self, text: str, src_lang: str = "en_XX", tgt_lang: str = "te_IN"):
        """
        Translate `text` from `src_lang` to `tgt_lang` using local mBART-50.

        Expected language codes are the mBART50 codes like: en_XX, hi_IN, te_IN, ja_XX, zh_CN, es_XX.
        Returns:
          { "translation": "<translated text>" } on success
          { "error": "<message>" } on failure
        """
        if not text or not isinstance(text, str):
            return {"error": "Invalid input text"}

        try:
            pool = self._ensure_pool()
            # Long model loads can take time on first request; keep timeout generous.
            future = pool.submit(translate_text, text, src_lang, tgt_lang)
            translation = future.result(timeout=180)
            return {"translation": translation}
        except BrokenProcessPool:
            # Worker process died (e.g., torch access violation). Reset and return a clean error.
            self._reset_pool()
            return {
                "error": (
                    "Translation worker crashed while loading/running mBART. "
                    "The server stayed up; please retry. If it keeps crashing, "
                    "this machine likely doesn't have enough RAM/pagefile for mbart-large."
                )
            }
        except TimeoutError:
            return {"error": "Translation timed out while running mBART"}
        except OSError as e:
            # Windows commonly throws: "The paging file is too small..." (os error 1455)
            msg = str(e)
            if "os error 1455" in msg.lower() or "paging file" in msg.lower():
                return {
                    "error": (
                        "mBART model could not be loaded due to insufficient virtual memory "
                        "(Windows paging file too small). Increase your system paging file "
                        "or use a smaller translation model."
                    )
                }
            return {"error": msg}
        except Exception as e:
            return {"error": str(e)}
