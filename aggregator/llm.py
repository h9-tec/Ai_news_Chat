"""Unified interface for Ollama & Groq"""
from __future__ import annotations
import requests, os
from .config import OLLAMA_URL, OLLAMA_MODEL, GROQ_API_KEY, GROQ_MODEL
import logging

logger = logging.getLogger(__name__)

class LLM:
    def __init__(self, backend: str = "ollama"):
        assert backend in {"ollama", "groq"}
        self.backend = backend

    def _generate_ollama(self, prompt: str, max_tokens: int = 512) -> str:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        r = requests.post(OLLAMA_URL, json=payload, timeout=600)
        r.raise_for_status()
        return r.json().get("response", "")

    def _generate_groq(self, prompt: str, max_tokens: int = 512) -> str:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set")
            
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful AI news assistant."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
        }
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers, timeout=600)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    # simple, blocking generation
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        try:
            if self.backend == "ollama":
                return self._generate_ollama(prompt, max_tokens)
            else:
                try:
                    return self._generate_groq(prompt, max_tokens)
                except (requests.exceptions.HTTPError, ValueError) as e:
                    logger.warning(f"Groq API failed ({str(e)}), falling back to Ollama")
                    self.backend = "ollama"
                    return self._generate_ollama(prompt, max_tokens)
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            return f"Error generating response: {str(e)}" 