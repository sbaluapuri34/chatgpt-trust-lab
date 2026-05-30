from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx

from phase3.config import GeminiConfig, GroqConfig

logger = logging.getLogger(__name__)

MAX_RETRIES = 6
DEFAULT_RETRY_SECONDS = 30


class LLMClient(ABC):
    name: str

    @abstractmethod
    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


class GroqClient(LLMClient):
    """Groq OpenAI-compatible chat completions API with automatic key rotation."""

    name = "groq"

    def __init__(self, api_key: str | list[str] | tuple[str, ...], config: GroqConfig, *, timeout: float = 120.0) -> None:
        if isinstance(api_key, str):
            self._api_keys = [api_key]
        else:
            self._api_keys = list(api_key)
        self._current_key_index = 0
        self._config = config
        self._timeout = timeout

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        url = f"{self._config.base_url}/chat/completions"
        payload = {
            "model": self._config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        last_error: Exception | None = None
        attempt = 0
        while attempt < len(self._api_keys):
            if not self._api_keys:
                raise RuntimeError("All Groq API keys have been disabled due to daily limits.")
            api_key = self._api_keys[self._current_key_index]
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(url, headers=headers, json=payload)
                    if response.status_code != 200:
                        logger.error("HTTP error %s: %s", response.status_code, response.text)
                    response.raise_for_status()
                    data = response.json()
                return str(data["choices"][0]["message"]["content"])
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code in (413, 429, 503):
                    err_msg = exc.response.text
                    if "tokens per day" in err_msg or "TPD" in err_msg or "daily" in err_msg.lower():
                        logger.warning(
                            "Groq API key at index %s has exhausted its daily token limit (TPD) — permanently disabling it for this run",
                            self._current_key_index,
                        )
                        self._api_keys.pop(self._current_key_index)
                        if not self._api_keys:
                            raise RuntimeError("All Groq API keys exhausted their daily limits.")
                        self._current_key_index = self._current_key_index % len(self._api_keys)
                        # We don't increment attempt, we just try the next active key
                        continue

                    if len(self._api_keys) > 1:
                        prev_index = self._current_key_index
                        self._current_key_index = (self._current_key_index + 1) % len(self._api_keys)
                        logger.warning(
                            "Groq API key at index %s rate limited (HTTP %s) — rotating to index %s and retrying immediately",
                            prev_index,
                            exc.response.status_code,
                            self._current_key_index,
                        )
                        attempt += 1
                        continue
                raise
        if last_error is not None:
            raise last_error
        raise RuntimeError("All Groq API keys failed")


class GeminiClient(LLMClient):
    name = "gemini"

    def __init__(self, api_key: str, config: GeminiConfig, *, timeout: float = 120.0) -> None:
        self._api_key = api_key
        self._config = config
        self._timeout = timeout

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._config.model}:generateContent"
        )
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        params = {"key": self._api_key}
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini returned no candidates")
        parts = candidates[0].get("content", {}).get("parts") or []
        return "".join(str(part.get("text", "")) for part in parts)


class MockLLMClient(LLMClient):
    """Deterministic offline client for development without API keys."""

    name = "mock"

    def __init__(self, *, stage: str) -> None:
        self._stage = stage

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        del system_prompt
        start = user_prompt.find("[")
        end = user_prompt.rfind("]")
        posts = json.loads(user_prompt[start : end + 1])
        results: list[dict[str, Any]] = []
        for post in posts:
            post_id = post["id"]
            text = post.get("text", "")
            if self._stage == "relevance":
                relevant = any(
                    word in text.lower()
                    for word in ("trust", "hallucination", "wrong", "confident", "verify", "accountability")
                )
                results.append(
                    {
                        "id": post_id,
                        "relevant": relevant,
                        "relevance_score": 0.85 if relevant else 0.15,
                        "reason": "Mock: substantive research-topic language detected."
                        if relevant
                        else "Mock: general discussion without research focus.",
                    }
                )
            else:
                lower = text.lower()
                if "hallucination" in lower or "fabricated" in lower:
                    theme = "overconfident_incorrect_outputs"
                elif "lost trust" in lower or "skeptical" in lower:
                    theme = "user_trust_breakdown"
                elif "verify" in lower or "checked" in lower:
                    theme = "user_evaluation_verification_behavior"
                elif "trusted" in lower or "relied" in lower:
                    theme = "over_reliance_on_ai_outputs"
                elif any(w in lower for w in ("health", "grade", "work", "money", "legal")):
                    theme = "real_world_impact_of_ai_outputs"
                else:
                    theme = "needs_manual_review"
                quote = text[:120] if text else post_id
                if quote not in text and text:
                    quote = text[: min(len(text), 80)]
                results.append(
                    {
                        "id": post_id,
                        "primary_theme": theme,
                        "secondary_themes": [],
                        "theme_rationale": f"Mock assignment based on dominant narrative cues for {post_id}.",
                        "evidence_quote": quote,
                        "severity": "medium",
                        "model_confidence": 0.75,
                        "secondary_labels": [],
                    }
                )
        return json.dumps(results, ensure_ascii=False)


def build_llm_clients(
    *,
    stage: str,
    primary: str,
    fallback: str,
    groq_api_key: str | None,
    gemini_api_key: str | None,
    groq_config: GroqConfig,
    gemini_config: GeminiConfig,
    use_mock: bool = False,
) -> list[LLMClient]:
    if use_mock or (not groq_api_key and not gemini_api_key):
        logger.warning("No LLM API keys found — using MockLLMClient for stage=%s", stage)
        return [MockLLMClient(stage=stage)]

    # Load all available Groq API keys from env
    import os
    groq_keys: list[str] = []
    if groq_api_key:
        groq_keys.append(groq_api_key)
    for suffix in ("2", "3", "4", "5"):
        k = os.getenv(f"GROQ_API_KEY_{suffix}") or os.getenv(f"GROK_API_KEY_{suffix}")
        if k:
            groq_keys.append(k)

    clients: list[LLMClient] = []
    order = [primary, fallback]
    for name in order:
        if name in ("groq", "grok") and groq_keys:
            clients.append(GroqClient(groq_keys, groq_config))
        elif name == "gemini" and gemini_api_key:
            clients.append(GeminiClient(gemini_api_key, gemini_config))
    if not clients:
        return [MockLLMClient(stage=stage)]
    return clients


def _retry_after_seconds(exc: httpx.HTTPStatusError) -> float:
    header = exc.response.headers.get("retry-after")
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    return DEFAULT_RETRY_SECONDS


def _complete_with_retries(client: LLMClient, *, system_prompt: str, user_prompt: str) -> str:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        except httpx.HTTPStatusError as exc:
            last_error = exc
            if exc.response.status_code in (413, 429, 503) and attempt < MAX_RETRIES:
                wait = _retry_after_seconds(exc)
                if wait > 60:
                    logger.warning(
                        "%s rate limited (HTTP %s) with long wait (%.0fs) — raising to trigger fallback",
                        client.name,
                        exc.response.status_code,
                        wait,
                    )
                    raise
                logger.warning(
                    "%s rate limited (HTTP %s) — retry %s/%s in %.0fs",
                    client.name,
                    exc.response.status_code,
                    attempt,
                    MAX_RETRIES,
                    wait,
                )
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"{client.name} failed after {MAX_RETRIES} retries") from last_error


def complete_with_fallback(
    clients: list[LLMClient],
    *,
    system_prompt: str,
    user_prompt: str,
) -> tuple[str, str]:
    last_error: Exception | None = None
    for client in clients:
        try:
            return _complete_with_retries(
                client,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            ), client.name
        except Exception as exc:
            last_error = exc
            logger.warning("LLM client %s failed: %s", client.name, exc)
    raise RuntimeError("All LLM clients failed") from last_error
