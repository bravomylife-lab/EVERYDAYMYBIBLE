import json
from typing import Any

from anthropic import Anthropic

from models.data_models import ScriptData, ScriptSection
from prompts.script_prompt import SYSTEM_PROMPT, get_user_prompt
from utils.config import load_env, require_env


class ScriptGenerator:
    def __init__(self, model: str = "claude-sonnet-4-20250514") -> None:
        load_env()
        api_key = require_env("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate_script(self, bible_reference: str) -> ScriptData:
        """
        Claude API를 호출하여 성경 구절에 대한 스크립트를 생성하고 ScriptData 객체를 반환합니다.
        """
        user_prompt = get_user_prompt(bible_reference)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.7,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        text = self._extract_text(response)
        data = self._parse_json(text)

        sections = [
            ScriptSection(
                section_type=item["section_type"],
                content=item["content"],
                image_prompt_english=item["image_prompt_english"],
                image_prompt_korean=item["image_prompt_korean"],
            )
            for item in data["sections"]
        ]

        return ScriptData(bible_reference=bible_reference, sections=sections)

    @staticmethod
    def _extract_text(response: Any) -> str:
        if hasattr(response, "content") and response.content:
            first = response.content[0]
            if hasattr(first, "text"):
                return first.text
        raise ValueError("Claude response has no text content.")

    @staticmethod
    def _parse_json(text: str) -> dict:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in Claude response.")
        payload = text[start : end + 1]
        return json.loads(payload)