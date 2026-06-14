#!/usr/bin/env python3
"""CIEL Voice — Interface vocale conversationnelle.

Pipeline : Microphone → STT → LLM (CIEL API) → TTS → Haut-parleur.

Backends :
  STT : Google Web Speech (gratuit, aucune clé)
  TTS : Microsoft Edge TTS (gratuit, très bonne qualité)
  Enregistrement : sox (subprocess) — léger, fiable
"""

from __future__ import annotations

import os
import io
import sys
import json
import time
import math
import struct
import shutil
import asyncio
import tempfile
import subprocess
import http.client
import urllib.request
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable

# ── Configuration ──

CIEL_PORT = int(os.environ.get("CIEL_PORT", "8765"))
CIEL_URL = f"http://127.0.0.1:{CIEL_PORT}"
TMP_DIR = Path(tempfile.gettempdir()) / "ciel-voice"
TMP_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_LANG = "fr-FR"
DEFAULT_TTS_VOICE = "fr-FR-HenriNeural"
SILENCE_THRESHOLD = 1.0  # secondes de silence pour arrêter l'enregistrement
SILENCE_DB = 3.0  # seuil en % du pic (sox silence)

# ── Utilitaires ──

def _have_sox() -> bool:
    return shutil.which("sox") is not None

def _have_ffplay() -> bool:
    return shutil.which("ffplay") is not None

def _have_paplay() -> bool:
    return shutil.which("paplay") is not None

def _have_aplay() -> bool:
    return shutil.which("aplay") is not None

def _play_audio(path: str | Path) -> None:
    if _have_paplay():
        subprocess.run(["paplay", str(path)], check=False)
    elif _have_ffplay():
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)], check=False)
    elif _have_aplay():
        subprocess.run(["aplay", str(path)], check=False)
    else:
        raise RuntimeError("Aucun lecteur audio trouvé (paplay, ffplay, aplay)")

# ── STT ──

def record_audio(timeout: float = 10.0, silence_sec: float = SILENCE_THRESHOLD) -> str:
    """Enregistre le micro jusqu'à : timeout OU silence détecté.

    Retourne le chemin du fichier WAV.
    """
    if not _have_sox():
        raise RuntimeError("sox est requis pour l'enregistrement microphone")

    out = TMP_DIR / f"recording-{int(time.time())}.wav"
    out_str = str(out)

    proc = subprocess.Popen(
        ["sox", "-d", "-t", "wav", out_str,
         "silence", "1", "0.1", f"{SILENCE_DB}%",
         "1", f"{silence_sec}", f"{SILENCE_DB}%"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait(2)

    if not out.exists() or out.stat().st_size < 100:
        raise RuntimeError("Enregistrement vide — aucun son détecté")

    return out_str


def transcribe(audio_path: str) -> str:
    """Transcrit un fichier audio en texte via Google Web Speech."""
    try:
        import speech_recognition as sr
    except ImportError:
        raise RuntimeError("SpeechRecognition requis : pip install SpeechRecognition")

    r = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = r.record(source)

    try:
        text = r.recognize_google(audio, language=DEFAULT_LANG)
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        raise RuntimeError(f"Erreur STT Google : {e}")


# ── TTS ──

async def synthesize(text: str, voice: str = DEFAULT_TTS_VOICE) -> str:
    """Synthèse vocale via Microsoft Edge TTS.

    Retourne le chemin du fichier audio MP3.
    """
    out = TMP_DIR / f"tts-{int(time.time())}.mp3"
    out_str = str(out)

    proc = await asyncio.create_subprocess_exec(
        "edge-tts",
        "--text", text,
        "--write-media", out_str,
        "--voice", voice,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    await asyncio.wait_for(proc.wait(), timeout=30)

    if not out.exists():
        raise RuntimeError("Échec de la synthèse vocale")

    return out_str


def speak(text: str, voice: str = DEFAULT_TTS_VOICE, blocking: bool = True) -> None:
    """Synthèse + lecture vocale."""
    out = asyncio.run(synthesize(text, voice))
    _play_audio(out)
    if not blocking:
        Path(out).unlink(missing_ok=True)


def speak_async(text: str, voice: str = DEFAULT_TTS_VOICE) -> asyncio.Task:
    """Version async de speak()."""
    async def _run():
        out = await synthesize(text, voice)
        _play_audio(out)

    return asyncio.create_task(_run())


# ── Session de chat vocal ──

@dataclass
class VoiceChatConfig:
    stt_timeout: float = 10.0
    silence_sec: float = 1.0
    tts_voice: str = DEFAULT_TTS_VOICE
    lang: str = DEFAULT_LANG
    provider: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    wake_word: str | None = "ciel"
    continuous: bool = False

    def __post_init__(self):
        if self.wake_word:
            self.wake_word = self.wake_word.lower().strip()


class VoiceChatSession:
    """Boucle conversationnelle : Micro → STT → CIEL → TTS → Audio."""

    def __init__(self, cfg: VoiceChatConfig | None = None):
        self.cfg = cfg or VoiceChatConfig()
        self._running = False
        self._history: list[dict] = []
        self._on_transcribe: Callable[[str], None] | None = None
        self._on_response: Callable[[str], None] | None = None
        self._on_error: Callable[[Exception], None] | None = None

    def on_transcribe(self, cb: Callable[[str], None]):
        self._on_transcribe = cb

    def on_response(self, cb: Callable[[str], None]):
        self._on_response = cb

    def on_error(self, cb: Callable[[Exception], None]):
        self._on_error = cb

    def _check_server(self) -> bool:
        """Vérifie si le serveur CIEL est en ligne."""
        try:
            req = urllib.request.Request(f"{CIEL_URL}/v1/health", method="GET")
            resp = urllib.request.urlopen(req, timeout=3)
            return resp.status == 200
        except Exception:
            return False

    def _send_chat(self, text: str) -> str | None:
        """Envoie le texte au serveur CIEL et retourne la réponse."""
        if not self._check_server():
            raise RuntimeError("Serveur CIEL hors ligne")

        payload = {
            "message": text,
            "stream": False,
        }
        if self.cfg.provider:
            payload["provider"] = self.cfg.provider
        if self.cfg.model:
            payload["model"] = self.cfg.model
        if self.cfg.system_prompt:
            payload["system_prompt"] = self.cfg.system_prompt

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{CIEL_URL}/v1/chat",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        try:
            resp = urllib.request.urlopen(req, timeout=30)
            body = json.loads(resp.read().decode())
            return body.get("response") or body.get("message") or body.get("content")
        except Exception as e:
            raise RuntimeError(f"Erreur chat CIEL : {e}")

    def run_once(self) -> bool:
        """Un cycle : écoute → transcrit → envoie → répond.

        Retourne True si OK, False si aucun son détecté.
        """
        audio_path = record_audio(
            timeout=self.cfg.stt_timeout,
            silence_sec=self.cfg.silence_sec,
        )

        text = transcribe(audio_path)
        Path(audio_path).unlink(missing_ok=True)

        if not text:
            return False

        if self._on_transcribe:
            self._on_transcribe(text)

        # Vérification du wake word
        if self.cfg.wake_word:
            text_lower = text.lower().strip()
            if not text_lower.startswith(self.cfg.wake_word):
                return False
            text = text_lower[len(self.cfg.wake_word):].strip()
            if not text:
                return False

        response = self._send_chat(text)
        if not response:
            return False

        if self._on_response:
            self._on_response(response)

        self._history.append({"role": "user", "content": text})
        self._history.append({"role": "assistant", "content": response})

        speak(response, voice=self.cfg.tts_voice)

        return True

    def run(self):
        """Boucle infinie du chat vocal."""
        self._running = True

        if not _have_sox():
            print("Erreur : sox est requis. Installez-le :")
            print("  pacman -S sox    (Arch)")
            print("  apt install sox  (Debian/Ubuntu)")
            return

        if self.cfg.wake_word:
            print(f"🎤 En attente du mot-clé \"{self.cfg.wake_word}\"... (Ctrl+C pour quitter)")
        else:
            print("🎤 Écoute active... (Ctrl+C pour quitter)")

        try:
            while self._running:
                cycle_ok = self.run_once()
                if not cycle_ok:
                    if self.cfg.continuous:
                        time.sleep(0.3)
        except KeyboardInterrupt:
            print("\n👋 Fin de la session vocale")
        except Exception as e:
            if self._on_error:
                self._on_error(e)
            else:
                print(f"✗ {e}")

    def stop(self):
        self._running = False


# ── CLI helpers ──

def list_microphones() -> None:
    """Liste les microphones disponibles (via sox)."""
    try:
        result = subprocess.run(
            ["sox", "--help"],
            capture_output=True, text=True, timeout=2,
        )
    except FileNotFoundError:
        print("sox n'est pas installé")
        return

    try:
        result = subprocess.run(
            ["sox", "-d", "-t", "wav", "/dev/null"],
            capture_output=True, timeout=3,
        )
    except subprocess.TimeoutExpired:
        pass
    print("Microphone par défaut : 'default' (PulseAudio)")


def list_voices() -> None:
    """Liste les voix TTS disponibles."""
    try:
        result = subprocess.run(
            ["edge-tts", "--list-voices"],
            capture_output=True, text=True, timeout=10,
        )
        lines = result.stdout.strip().split("\n")
        print(f"{'Voix':<35} {'Langue':<10} {'Genre':<8}")
        print("-" * 55)
        for line in lines:
            if " " in line:
                parts = line.split()
                if len(parts) >= 3:
                    name = parts[0]
                    lang = parts[1]
                    gender = parts[2].split(",")[0] if "," in parts[2] else parts[2]
                    print(f"{name:<35} {lang:<10} {gender:<8}")
    except FileNotFoundError:
        print("edge-tts n'est pas installé (pip install edge-tts)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--voices":
        list_voices()
    elif len(sys.argv) > 1 and sys.argv[1] == "--mics":
        list_microphones()
    else:
        session = VoiceChatSession()
        session.run()
