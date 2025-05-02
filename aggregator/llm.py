"""Unified interface for Ollama & Groq"""
from __future__ import annotations
import requests, os
from .config import OLLAMA_URL, OLLAMA_MODEL, GROQ_API_KEY, GROQ_MODEL, GEMINI_API_KEY, GEMINI_MODEL
import logging

logger = logging.getLogger(__name__)

class LLM:
    def __init__(self, backend: str = "gemini"):
        assert backend in {"ollama", "groq", "gemini"}
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
                {
                    "role": "system", 
                    "content": """You are a helpful AI news assistant specialized in Arabic summarization. 
                    When summarizing technical content:
                    1. Write the summary in Arabic
                    2. Keep all technical terms, scientific terms, and proper nouns in English
                    3. Maintain the original meaning and context
                    4. Use clear and professional Arabic language
                    5. Preserve any numerical values and measurements as is
                    6. Keep company names, product names, and technology names in English"""
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
        }
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers, timeout=600)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    def _generate_gemini(self, prompt: str, max_tokens: int = 512) -> str:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens}
        }
        r = requests.post(url, json=data, headers=headers, timeout=60)
        r.raise_for_status()
        resp = r.json()
        # Gemini API returns candidates[0].content.parts[0].text
        return resp["candidates"][0]["content"]["parts"][0]["text"].strip()

    def summarize_arabic(self, text: str, max_tokens: int = 512) -> str:
        """Generate an Arabic summary while preserving technical terms in English."""
        prompt = f"""Please provide a concise summary of the following text in Arabic. 
        Keep all technical terms, scientific terms, and proper nouns in English.
        Do not translate any technical or scientific terminology.

        Text to summarize:
        {text}

        Summary:"""
        try:
            if self.backend == "gemini":
                try:
                    return self._generate_gemini(prompt, max_tokens)
                except Exception as e:
                    logger.warning(f"Gemini API failed ({str(e)}), falling back to Groq")
                    self.backend = "groq"
            if self.backend == "groq":
                try:
                    return self._generate_groq(prompt, max_tokens)
                except Exception as e:
                    logger.warning(f"Groq API failed ({str(e)}), falling back to Ollama")
                    self.backend = "ollama"
            return self._generate_ollama(prompt, max_tokens)
        except Exception as e:
            logger.error(f"Arabic summarization failed: {str(e)}")
            return f"Error generating Arabic summary: {str(e)}"

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        try:
            if self.backend == "gemini":
                try:
                    return self._generate_gemini(prompt, max_tokens)
                except Exception as e:
                    logger.warning(f"Gemini API failed ({str(e)}), falling back to Groq")
                    self.backend = "groq"
            if self.backend == "groq":
                try:
                    return self._generate_groq(prompt, max_tokens)
                except Exception as e:
                    logger.warning(f"Groq API failed ({str(e)}), falling back to Ollama")
                    self.backend = "ollama"
            return self._generate_ollama(prompt, max_tokens)
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            return f"Error generating response: {str(e)}" 