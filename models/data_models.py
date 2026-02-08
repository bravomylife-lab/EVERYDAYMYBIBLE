from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ImagePrompt(BaseModel):
    """대본의 특정 텍스트 구간에 매칭되는 이미지 프롬프트"""
    text_segment: str = Field(..., description="이 이미지가 커버하는 대본 텍스트 조각")
    prompt_korean: str = Field(..., description="사용자 수정용 한국어 이미지 설명")
    prompt_english: str = Field(..., description="Gemini API 호출용 영문 프롬프트")
    image_path: Optional[str] = Field(None, description="생성된 이미지 파일 경로")
    generated: bool = Field(False, description="이미지 생성 완료 여부")


class ScriptSection(BaseModel):
    section_type: str = Field(
        ...,
        description=(
            "Opening, PassageIntro, ReadingOne, ExplanationOne, ReadingTwo, "
            "ExplanationTwo, ReadingThree, ExplanationThree, Prayer, Ending"
        ),
    )
    content: str = Field(..., description="스크립트 텍스트 본문")
    bible_verse: Optional[str] = Field(
        None, description="성경 구절 (Reading 섹션용)"
    )
    image_prompts: List[ImagePrompt] = Field(
        default_factory=list, description="섹션별 다중 이미지 프롬프트"
    )


class ScriptData(BaseModel):
    bible_reference: str = Field(..., description="입력된 성경 구절 (예: 시편 23편)")
    sections: List[ScriptSection]
    art_style: str = Field(
        "warm, pastel-toned watercolor", description="이미지 생성 스타일 프롬프트"
    )

    @property
    def all_image_prompts(self) -> List[ImagePrompt]:
        """모든 섹션의 이미지 프롬프트를 순서대로 반환"""
        prompts = []
        for section in self.sections:
            prompts.extend(section.image_prompts)
        return prompts

    @property
    def all_image_paths(self) -> List[str]:
        """생성된 모든 이미지 경로를 순서대로 반환"""
        paths = []
        for section in self.sections:
            for ip in section.image_prompts:
                if ip.image_path:
                    paths.append(ip.image_path)
        return paths

    @property
    def total_image_count(self) -> int:
        return sum(len(s.image_prompts) for s in self.sections)


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
    model_config = ConfigDict(extra="ignore")

    bible_passage: str = ""
    script: Optional[ScriptData] = None
    audio_blocks: List[AudioBlock] = Field(default_factory=list)
    timestamps: List[TimestampedSection] = Field(default_factory=list)
    final_audio_bytes: Optional[bytes] = None
    srt_content: Optional[str] = None
    selected_voice_id: str = ""
    youtube_metadata: Optional[YouTubeMetadata] = None
