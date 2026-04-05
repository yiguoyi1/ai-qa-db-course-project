from dataclasses import dataclass

from openai import OpenAI

from app.core.errors import ConfigurationError, ExternalServiceError
from app.core.settings import get_settings


@dataclass
class LLMAnswerResult:
    content: str
    model_name: str
    token_usage: int


class DeepSeekClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.deepseek_api_key:
            raise ConfigurationError(
                "DEEPSEEK_API_KEY is not set. Add it to .env before calling the AI endpoint."
            )

        self._model = settings.deepseek_model
        self._client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )

    def generate_answer(
        self,
        messages: list[dict[str, str]],
    ) -> LLMAnswerResult:
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
            )
        except Exception as exc:  # noqa: BLE001
            raise ExternalServiceError(f"DeepSeek API call failed: {exc}") from exc

        content = completion.choices[0].message.content or ""
        usage = getattr(completion, "usage", None)
        token_usage = int(getattr(usage, "total_tokens", 0) or 0)
        model_name = completion.model or self._model

        return LLMAnswerResult(
            content=content.strip(),
            model_name=model_name,
            token_usage=token_usage,
        )
