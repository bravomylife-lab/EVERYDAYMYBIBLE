from typing import List, Optional

from pydantic import BaseModel, Field


class ScriptSection(BaseModel):
    section_type: str = Field(
        ..., description="Opening, Reading, Explanation, Application, Prayer, Ending"
    )
    content: str = Field(..., description="스크립트 텍스트 본문")
    bible_verse: Optional[str] = Field(
        None, description="성경 구절 (Reading 섹션용)"
    )
    image_prompt_korean: str = Field(..., description="사용자 수정용 한국어 이미지 설명")
    image_prompt_english: str = Field(..., description="Gemini API 호출용 영문 프롬프트")


class ScriptData(BaseModel):
    bible_reference: str = Field(..., description="입력된 성경 구절 (예: 시편 23편)")
    sections: List[ScriptSection]
    art_style: str = Field(
        "warm, pastel-toned watercolor", description="이미지 생성 스타일 프롬프트"
    )


class AudioBlock(BaseModel):
    section_index: int
    text: str
    audio_data: Optional[bytes] = None
    duration_seconds: float = 0.0
    voice_id: str = ""
    confirmed: bool = False


class TimestampedSection(BaseModel):
    section_type: str
    start_time_seconds: float
    end_time_seconds: float


class YouTubeMetadata(BaseModel):
    title_candidates: List[str] = Field(default_factory=list)
    selected_title: str = ""
    description: str = ""
    hashtags: str = ""
    tags: str = ""


class ProjectState(BaseModel):
    bible_passage: str = ""
    script: Optional[ScriptData] = None
    audio_blocks: List[AudioBlock] = Field(default_factory=list)
    timestamps: List[TimestampedSection] = Field(default_factory=list)
    final_audio_bytes: Optional[bytes] = None
    generated_images: List[str] = Field(default_factory=list)
    srt_content: Optional[str] = None
    selected_voice_id: str = ""
    youtube_metadata: Optional[YouTubeMetadata] = None
