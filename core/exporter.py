import io
import os
import re
import zipfile
from datetime import datetime
from typing import List, Optional

from models.data_models import ScriptData, TimestampedSection


def build_zip_package(
    bible_reference: str,
    script: ScriptData,
    final_audio_bytes: Optional[bytes],
    srt_content: str,
    timestamps: Optional[List[TimestampedSection]] = None,
) -> bytes:
    """
    모든 생성물을 하나의 ZIP 파일로 압축하여 바이트로 반환합니다.
    이미지는 ScriptData의 image_prompts에서 가져옵니다.
    """
    folder_name = _safe_folder_name(bible_reference)
    date_str = datetime.now().strftime("%Y%m%d")
    root = f"{folder_name}_{date_str}"

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        if final_audio_bytes:
            zf.writestr(f"{root}/Final_Audio.mp3", final_audio_bytes)

        zf.writestr(f"{root}/Script.srt", srt_content.encode("utf-8"))
        zf.writestr(f"{root}/Script.txt", _build_script_text(script).encode("utf-8"))

        # 다중 이미지 프롬프트에서 이미지 경로 추출
        global_idx = 0
        for section_idx, section in enumerate(script.sections):
            ts = timestamps[section_idx] if timestamps and section_idx < len(timestamps) else None
            for j, ip in enumerate(section.image_prompts):
                if ip.image_path and os.path.exists(ip.image_path):
                    filename = _build_image_filename(global_idx + 1, section.section_type, j, ts)
                    with open(ip.image_path, "rb") as f:
                        zf.writestr(f"{root}/Images/{filename}", f.read())
                global_idx += 1

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def _build_script_text(script: ScriptData) -> str:
    chunks = [f"{script.bible_reference}"]
    for section in script.sections:
        chunks.append(f"[{section.section_type}]\n{section.content}\n")
    return "\n".join(chunks).strip()


def _build_image_filename(
    index: int, section_type: str, sub_index: int, ts: Optional[TimestampedSection]
) -> str:
    minutes = 0
    seconds = 0
    if ts:
        total = int(ts.start_time_seconds)
        minutes = total // 60
        seconds = total % 60

    safe_section = re.sub(r"[^A-Za-z0-9가-힣_-]", "", section_type)
    return f"{minutes:02d}_{seconds:02d}_{index:02d}_{safe_section}.png"


def _safe_folder_name(text: str) -> str:
    cleaned = re.sub(r"\s+", "", text.strip())
    cleaned = re.sub(r"[^A-Za-z0-9가-힣_-]", "", cleaned)
    return cleaned or "EverydayBible"
