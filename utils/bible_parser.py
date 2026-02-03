import re


def parse_bible_reference(text: str) -> str:
    """
    사용자 입력 성경 구절 문자열을 정제합니다.
    """
    cleaned = text.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned