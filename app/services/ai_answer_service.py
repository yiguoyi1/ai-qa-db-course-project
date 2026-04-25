from dataclasses import dataclass

from app.integrations.llm.openai_client import DeepSeekClient
from app.prompts.question_answer_prompt import (
    build_follow_up_messages,
    build_question_answer_messages,
    render_prompt_text,
)


@dataclass
class GeneratedAnswer:
    content: str
    model_name: str
    provider_name: str
    token_usage: int
    prompt_text: str


class AIAnswerService:
    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self._client = client or DeepSeekClient()

    def generate_single_answer(self, title: str, content: str) -> GeneratedAnswer:
        messages = build_question_answer_messages(title=title, content=content)
        llm_result = self._client.generate_answer(messages)

        return GeneratedAnswer(
            content=llm_result.content,
            model_name=llm_result.model_name,
            provider_name="DeepSeek",
            token_usage=llm_result.token_usage,
            prompt_text=render_prompt_text(messages),
        )

    def generate_follow_up_answer(
        self,
        *,
        title: str,
        content: str,
        seed_answer_content: str,
        history_messages: list[dict[str, str]],
    ) -> GeneratedAnswer:
        messages = build_follow_up_messages(
            title=title,
            content=content,
            seed_answer_content=seed_answer_content,
            history_messages=history_messages,
        )
        llm_result = self._client.generate_answer(messages)

        return GeneratedAnswer(
            content=llm_result.content,
            model_name=llm_result.model_name,
            provider_name="DeepSeek",
            token_usage=llm_result.token_usage,
            prompt_text=render_prompt_text(messages),
        )
