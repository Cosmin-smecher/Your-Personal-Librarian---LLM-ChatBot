# -*- coding: utf-8 -*-
"""
tts_utils.py — helper pentru Text-to-Speech
Prioritate:
  1) OpenAI TTS (gpt-4o-mini-tts) -> MP3
  2) Fallback offline: pyttsx3 (SAPI5/Windows) -> WAV
  3) (Opțional) gTTS, dacă e instalat și există conexiune la internet
Returnează (audio_bytes, mime). Dacă nu reușește, întoarce (b"", "audio/mp3").
"""
from __future__ import annotations
from pathlib import Path
from typing import Tuple

def _openai_tts(text: str, voice: str = "alloy") -> Tuple[bytes, str]:
    try:
        from openai import OpenAI
        client = OpenAI()
        speech_path = Path("tts_output.mp3")
        try:
            with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts", voice=voice, input=text
            ) as response:
                response.stream_to_file(str(speech_path))
        except Exception:
            # Non-streaming fallback
            resp = client.audio.speech.create(model="gpt-4o-mini-tts", voice=voice, input=text)
            # Best-effort write
            if hasattr(resp, "content"):
                speech_path.write_bytes(resp.content)
            else:
                try:
                    speech_path.write_bytes(bytes(resp))
                except Exception:
                    return b"", "audio/mp3"
        data = speech_path.read_bytes()
        try:
            speech_path.unlink()
        except Exception:
            pass
        return data, "audio/mp3"
    except Exception:
        return b"", "audio/mp3"

def _pyttsx3_tts(text: str) -> Tuple[bytes, str]:
    # Offline fallback (Windows: SAPI5; macOS: NSSpeechSynthesizer; Linux: espeak)
    try:
        import pyttsx3
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_path = Path(tmp.name)
        engine = pyttsx3.init()  # may raise if backend missing
        engine.save_to_file(text, str(tmp_path))
        engine.runAndWait()
        data = tmp_path.read_bytes()
        try:
            tmp_path.unlink()
        except Exception:
            pass
        return data, "audio/wav"
    except Exception:
        return b"", "audio/wav"

def _gtts_tts(text: str, gtts=None) -> Tuple[bytes, str]:
    # Optional online fallback (necesită gTTS instalat + internet)
    try:
        from gtts import gTTS
        import io
        buf = io.BytesIO()
        gTTS(text, lang="ro").write_to_fp(buf)
        return buf.getvalue(), "audio/mp3"
    except Exception:
        return b"", "audio/mp3"

def tts_bytes(text: str, voice: str = "alloy") -> Tuple[bytes, str]:
    """Returnează (audio_bytes, mime) fără a depinde de gTTS.
    Încearcă OpenAI, apoi pyttsx3 (offline). gTTS este doar un fallback opțional.
    """
    if not text or not text.strip():
        return b"", "audio/mp3"
    # 1) OpenAI
    data, mime = _openai_tts(text, voice=voice)
    if data:
        return data, mime
    # 2) Offline pyttsx3
    data, mime = _pyttsx3_tts(text)
    if data:
        return data, mime
    # 3) gTTS (opțional)
    data, mime = _gtts_tts(text)
    return data, mime
