import json
from typing import Any

from anthropic import Anthropic

from models.data_models import ImagePrompt, ScriptData, ScriptSection
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
            max_tokens=8000,
            temperature=0.7,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        text = self._extract_text(response)

        # 디버깅: 원본 응답 저장
        debug_file = "/tmp/claude_response_debug.txt"
        try:
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass

        # JSON 파싱 시도
        try:
            data = self._parse_json(text)
        except Exception as e1:
            try:
                sanitized = self._sanitize_json_text(text)
                data = self._parse_json(sanitized)
            except Exception as e2:
                try:
                    repaired = self._repair_json(text)
                    data = self._parse_json(repaired)
                except Exception as e3:
                    error_msg = (
                        f"JSON 파싱 실패.\n"
                        f"원본 오류: {str(e1)}\n"
                        f"Sanitize 후 오류: {str(e2)}\n"
                        f"Repair 후 오류: {str(e3)}\n"
                        f"디버그 파일: {debug_file}"
                    )
                    raise ValueError(error_msg)

        sections = self._build_sections(data)
        return ScriptData(bible_reference=bible_reference, sections=sections)

    @staticmethod
    def _build_sections(data: dict) -> list:
        """파싱된 JSON에서 ScriptSection 리스트를 생성합니다."""
        sections = []
        for item in data["sections"]:
            image_prompts = []
            for ip in item.get("image_prompts", []):
                image_prompts.append(
                    ImagePrompt(
                        text_segment=ip.get("text_segment", ""),
                        prompt_korean=ip.get("prompt_korean", ""),
                        prompt_english=ip.get("prompt_english", ""),
                    )
                )

            # 하위 호환: 기존 단일 image_prompt 형식도 처리
            if not image_prompts and "image_prompt_english" in item:
                image_prompts.append(
                    ImagePrompt(
                        text_segment=item.get("content", ""),
                        prompt_korean=item.get("image_prompt_korean", ""),
                        prompt_english=item.get("image_prompt_english", ""),
                    )
                )

            sections.append(
                ScriptSection(
                    section_type=item["section_type"],
                    content=item["content"],
                    image_prompts=image_prompts,
                )
            )
        return sections

    @staticmethod
    def _extract_text(response: Any) -> str:
        if hasattr(response, "content") and response.content:
            first = response.content[0]
            if hasattr(first, "text"):
                return first.text
        raise ValueError("Claude response has no text content.")

    @staticmethod
    def _parse_json(text: str) -> dict:
        # 마크다운 코드 블록 제거
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in Claude response.")
        payload = text[start : end + 1]

        try:
            return json.loads(payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON decode error at position {e.pos}: {e.msg}")

    @staticmethod
    def _sanitize_json_text(text: str) -> str:
        """JSON 문자열 내부의 개행/따옴표 문제를 완화합니다."""
        replacements = {
            "\u201c": '"',
            "\u201d": '"',
            "\u2018": "'",
            "\u2019": "'",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)

        out = []
        in_string = False
        escape = False
        for ch in text:
            if in_string:
                if escape:
                    out.append(ch)
                    escape = False
                    continue
                if ch == "\\":
                    out.append(ch)
                    escape = True
                    continue
                if ch == '"':
                    in_string = False
                    out.append(ch)
                    continue
                if ch == "\n":
                    out.append("\\n")
                    continue
                out.append(ch)
            else:
                if ch == '"':
                    in_string = True
                out.append(ch)
        return "".join(out)

    def _repair_json(self, text: str) -> str:
        """Claude가 반환한 텍스트를 JSON으로 복구합니다."""
        repair_prompt = (
            "Fix the following text into a valid JSON object.\n\n"
            "CRITICAL RULES:\n"
            "1. Return ONLY the JSON object - no markdown, no explanations\n"
            "2. All content must be on SINGLE LINES - replace any line breaks in content with spaces\n"
            "3. Properly escape quotes inside strings with \\\" \n"
            "4. Do NOT use raw newlines inside JSON string values\n"
            "5. The JSON must have this exact structure:\n"
            '{"sections": [{"section_type": "...", "content": "...", '
            '"image_prompts": [{"text_segment": "...", "prompt_korean": "...", "prompt_english": "..."}, ...]}, ...]}\n\n'
            f"TEXT TO FIX:\n{text}\n\n"
            "Return the fixed JSON now:"
        )
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            temperature=0.0,
            system="You are a strict JSON fixer. Return only valid JSON with no markdown formatting.",
            messages=[{"role": "user", "content": repair_prompt}],
        )
        return self._extract_text(response)
