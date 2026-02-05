import io
from typing import List, Optional

import google.generativeai as genai
from pydub import AudioSegment

from models.data_models import AudioBlock, ScriptSection, TimestampedSection
from utils.config import load_env, get_env


class SubtitleGenerator:
    def __init__(self, model: str = "gemini-2.0-flash") -> None:
        load_env()
        self.api_key = get_env("GOOGLE_API_KEY")
        self.model = model
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def generate_srt(
        self,
        audio_bytes: Optional[bytes],
        sections: List[ScriptSection],
        audio_blocks: List[AudioBlock],
        timestamps: Optional[List[TimestampedSection]] = None,
    ) -> str:
        if audio_bytes and self.api_key:
            try:
                return self._generate_srt_with_gemini(audio_bytes, sections)
            except Exception:
                pass

        if timestamps:
            return self._generate_srt_from_timestamps(sections, timestamps)

        computed = self._compute_timestamps_from_audio(audio_blocks, sections)
        return self._generate_srt_from_timestamps(sections, computed)

    def _generate_srt_with_gemini(
        self, audio_bytes: bytes, sections: List[ScriptSection]
    ) -> str:
        model = genai.GenerativeModel(self.model)
        prompt = (
            "Generate SRT subtitles for this Korean narration. "
            "Use the provided script sections to guide segmentation. "
            "Return only valid SRT text."
        )
        script_text = "\n\n".join(
            f"[{s.section_type}] {s.content}" for s in sections
        )
        response = model.generate_content(
            [
                prompt,
                script_text,
                {"mime_type": "audio/mpeg", "data": audio_bytes},
            ]
        )
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned empty SRT.")
        return text.strip()

    def _compute_timestamps_from_audio(
        self, audio_blocks: List[AudioBlock], sections: List[ScriptSection]
    ) -> List[TimestampedSection]:
        timestamps: List[TimestampedSection] = []
        current_time = 0.0

        for idx, block in enumerate(audio_blocks):
            duration = block.duration_seconds
            if block.audio_data:
                try:
                    segment = AudioSegment.from_mp3(io.BytesIO(block.audio_data))
                    duration = max(duration, len(segment) / 1000.0)
                except Exception:
                    pass

            section_type = sections[idx].section_type if idx < len(sections) else "Unknown"
            start_time = current_time
            end_time = current_time + duration
            timestamps.append(
                TimestampedSection(
                    section_type=section_type,
                    start_time_seconds=start_time,
                    end_time_seconds=end_time,
                )
            )
            current_time = end_time

        return timestamps

    def _generate_srt_from_timestamps(
        self, sections: List[ScriptSection], timestamps: List[TimestampedSection]
    ) -> str:
        lines: List[str] = []
        for i, ts in enumerate(timestamps, start=1):
            content = sections[i - 1].content if i - 1 < len(sections) else ""
            lines.append(str(i))
            lines.append(f"{_format_ts(ts.start_time_seconds)} --> {_format_ts(ts.end_time_seconds)}")
            lines.append(content.strip())
            lines.append("")
        return "\n".join(lines).strip()


def _format_ts(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    ms = int((seconds - int(seconds)) * 1000)
    total = int(seconds)
    hh = total // 3600
    mm = (total % 3600) // 60
    ss = total % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"