import io
import static_ffmpeg
from typing import List, Tuple

from pydub import AudioSegment

from models.data_models import AudioBlock, TimestampedSection

# ffmpeg 경로 자동 설정
static_ffmpeg.add_paths()

class AudioProcessor:
    def __init__(self):
        # 섹션 간 0.5초(500ms) 묵음 추가
        self.silence = AudioSegment.silent(duration=500)

    def merge_audio_blocks(
        self, blocks: List[AudioBlock], sections_metadata: List[dict]
    ) -> Tuple[bytes, List[TimestampedSection]]:
        """
        여러 오디오 블록을 순서대로 병합하고 타임스탬프를 계산합니다.
        
        Args:
            blocks: 생성된 AudioBlock 리스트
            sections_metadata: ScriptSection 정보 (section_type 등)
            
        Returns:
            (final_audio_bytes, timestamps_list)
        """
        final_audio = AudioSegment.empty()
        timestamps = []
        current_time_ms = 0.0

        # 블록을 인덱스 순서대로 정렬
        sorted_blocks = sorted(blocks, key=lambda x: x.section_index)

        for block in sorted_blocks:
            if not block.audio_data:
                continue

            # bytes -> AudioSegment 변환
            try:
                segment = AudioSegment.from_mp3(io.BytesIO(block.audio_data))
            except Exception:
                # MP3 디코딩 실패 시 건너뛰기 혹은 에러 처리
                continue

            duration_ms = len(segment)
            
            # 타임스탬프 기록 (초 단위)
            start_sec = current_time_ms / 1000.0
            end_sec = (current_time_ms + duration_ms) / 1000.0
            
            # 해당 블록의 섹션 타입 찾기
            section_type = "Unknown"
            if 0 <= block.section_index < len(sections_metadata):
                section_type = sections_metadata[block.section_index].get(
                    "section_type", "Unknown"
                )

            timestamps.append(TimestampedSection(
                section_type=section_type,
                start_time_seconds=start_sec,
                end_time_seconds=end_sec
            ))

            # 오디오 병합
            final_audio += segment
            final_audio += self.silence # 섹션 간 간격 추가
            current_time_ms += duration_ms + 500 # 묵음 시간 포함

        # Export to bytes (MP3)
        if len(final_audio) == 0:
            return b"", timestamps

        buffer = io.BytesIO()
        final_audio.export(buffer, format="mp3")
        return buffer.getvalue(), timestamps