"""Thin Groq client wrapper with structured JSON output, model fallback and retries.

Product rule: deterministic code where possible; the LLM is used only for
language tasks (extraction, reasoning text, summaries, suggestions).
"""
import json

from groq import Groq

from app.core.config import Settings
from app.utils.json_safe import extract_json


class LLMError(RuntimeError):
    """Raised when no configured model could produce a usable response."""


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Groq | None = None
        self.last_model: str = ""
        if settings.GROQ_API_KEY:
            self.client = Groq(api_key=settings.GROQ_API_KEY, timeout=settings.LLM_REQUEST_TIMEOUT)

    @property
    def configured(self) -> bool:
        return self.client is not None

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int | None = None,
        repair_on_error: bool = True,
    ) -> dict:
        """Call the LLM and return parsed JSON.

        Strategy:
        1. Try the primary model with JSON response format.
        2. If output is unparseable, retry ONCE with a repair instruction.
        3. If the primary model errors (quota/unavailable), try the fallback model.
        Raises LLMError with a human-readable message if everything fails.
        """
        if not self.client:
            raise LLMError("Groq API key is not configured. Set GROQ_API_KEY in backend/.env")

        last_error: Exception | None = None
        for model in self.settings.llm_models:
            self.last_model = model
            try:
                return self._generate_with_model(
                    model, system_prompt, user_prompt, max_tokens, repair_on_error
                )
            except Exception as exc:  # noqa: BLE001 - collapse into a clean LLMError
                last_error = exc

        raise LLMError(
            "All configured Groq models failed. Last error: " + self._friendly(last_error)
        )

    def _generate_with_model(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None,
        repair_on_error: bool,
    ) -> dict:
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or self.settings.LLM_MAX_TOKENS,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content or ""
        try:
            return extract_json(text)
        except (ValueError, json.JSONDecodeError):
            if not repair_on_error:
                raise ValueError("Model returned malformed JSON")
            repair_prompt = (
                user_prompt
                + "\n\nYour previous response was not valid JSON. "
                  "Return ONLY the corrected JSON object, no prose."
            )
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": repair_prompt},
                ],
                temperature=0,
                max_tokens=max_tokens or self.settings.LLM_MAX_TOKENS,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content or ""
            return extract_json(text)  # raises ValueError if still broken

    @staticmethod
    def _friendly(exc: Exception | None) -> str:
        if exc is None:
            return "unknown error"
        msg = str(exc)
        if "401" in msg or "invalid_api_key" in msg:
            return "invalid Groq API key"
        if "429" in msg or "rate_limit" in msg:
            return "Groq rate limit exceeded"
        if "503" in msg or "overloaded" in msg or "unavailable" in msg.lower():
            return "Groq model unavailable"
        return msg[:200]
