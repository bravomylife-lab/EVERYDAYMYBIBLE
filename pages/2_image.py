import io
import os
import zipfile
import time

import streamlit as st

from utils.session_state import get_state, update_state
from core.image_generator import ImageGenerator

st.title("Step 2: 이미지")
state = get_state()

if not state.script:
    st.warning("먼저 Step 1에서 스크립트를 생성하고 확정해주세요.")
    st.stop()

# ──────────────────────────────────────────────
# 1. 아트 스타일 선택
# ──────────────────────────────────────────────
st.header("1. 이미지 스타일 선택")

STYLE_PRESETS = {
    "수채화 (따뜻한 파스텔)": "warm, pastel-toned watercolor style, soft lighting, peaceful atmosphere, wet-on-wet technique",
    "유화 (인상주의)": "textured oil painting, impressionist style, vibrant brushstrokes, van gogh style, thick paint",
    "일러스트 (미니멀)": "clean lines, minimal colors, flat design illustration, modern look, vector art",
    "실사 (시네마틱)": "photorealistic, cinematic lighting, 8k resolution, highly detailed, dramatic atmosphere, depth of field",
    "애니메이션 (감성적인)": "anime style, makoto shinkai style, vibrant colors, detailed background, emotional atmosphere, lens flare",
    "3D 렌더링 (귀여운)": "3d render, pixar style, cute, soft lighting, high quality, octane render, clay material",
    "빈티지 (레트로 필름)": "vintage photo, film grain, retro aesthetic, 1980s style, nostalgic feel, faded colors",
    "연필 스케치 (흑백)": "pencil sketch, charcoal drawing, black and white, detailed shading, rough texture, artistic",
    "디지털 판타지 (몽환적)": "digital art, fantasy style, magical atmosphere, glowing effects, dreamy, ethereal",
    "스테인드 글라스 (성스러운)": "stained glass art, vibrant colors, intricate patterns, light shining through, holy atmosphere, cathedral window",
    "페이퍼 아트 (종이 공예)": "paper cutout art, layered paper, depth of field, soft shadows, craft style, handmade feel",
    "직접 입력": "custom"
}

current_preset = "직접 입력"
for name, prompt in STYLE_PRESETS.items():
    if prompt == state.script.art_style:
        current_preset = name
        break

selected_preset = st.selectbox(
    "스타일 프리셋 선택",
    options=list(STYLE_PRESETS.keys()),
    index=list(STYLE_PRESETS.keys()).index(current_preset)
)

if selected_preset == "직접 입력":
    new_art_style = st.text_input("스타일 프롬프트 직접 입력", value=state.script.art_style)
else:
    new_art_style = STYLE_PRESETS[selected_preset]
    st.caption(f"적용 프롬프트: `{new_art_style}`")

if new_art_style != state.script.art_style:
    state.script.art_style = new_art_style
    update_state(state)

# ──────────────────────────────────────────────
# 2. 이미지 프롬프트 검수 & 편집
# ──────────────────────────────────────────────
st.divider()
st.header("2. 이미지 프롬프트 검수")
st.info(f"총 {state.script.total_image_count}개의 이미지 프롬프트가 생성되었습니다. 한글 설명을 수정 후 '프롬프트 수정' 버튼을 눌러 AI가 영어 프롬프트를 자동 생성합니다.")

# Claude API를 사용한 프롬프트 번역 함수
def translate_prompt_to_english(korean_text: str, art_style: str) -> str:
    """한글 이미지 설명을 영어 Gemini 프롬프트로 변환"""
    from anthropic import Anthropic
    from utils.config import require_env

    api_key = require_env("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key)

    prompt = f"""Convert this Korean image description into a detailed English prompt for Gemini image generation.
Keep it concise but vivid. Focus on visual elements, composition, and atmosphere.

Korean description: {korean_text}
Art style context: {art_style}

Return ONLY the English prompt, nothing else."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()

global_idx = 0
for i, section in enumerate(state.script.sections):
    with st.expander(f"📌 {section.section_type} ({len(section.image_prompts)}장)", expanded=False):
        # 대본 내용 미리보기
        st.markdown(f"**대본:** {section.content[:150]}{'...' if len(section.content) > 150 else ''}")
        st.markdown("---")

        for j, ip in enumerate(section.image_prompts):
            col_info, col_edit, col_action = st.columns([1, 2, 1])

            with col_info:
                st.markdown(f"**이미지 #{global_idx + 1}**")
                st.caption(f"대상 텍스트:")
                st.text(ip.text_segment[:100] + ("..." if len(ip.text_segment) > 100 else ""))

                if ip.image_path and os.path.exists(ip.image_path):
                    st.image(ip.image_path, width=150)
                    st.success("생성 완료")

            with col_edit:
                # 한글 프롬프트 편집
                new_kr = st.text_area(
                    "이미지 설명 (한글)",
                    value=ip.prompt_korean,
                    height=100,
                    key=f"kr_{i}_{j}",
                    help="이미지에 표현할 장면을 한글로 설명하세요"
                )

                # 영어 프롬프트 보기 (토글)
                if st.toggle("영어 프롬프트 보기", key=f"toggle_{i}_{j}"):
                    st.text_area(
                        "English Prompt (Gemini용)",
                        value=ip.prompt_english,
                        height=80,
                        key=f"en_{i}_{j}",
                        disabled=True,
                        help="AI가 자동 생성한 영어 프롬프트입니다"
                    )

            with col_action:
                st.markdown("###")  # 정렬용 공백
                if st.button("✨ 프롬프트 수정", key=f"update_{i}_{j}", use_container_width=True, type="primary"):
                    with st.spinner("AI가 영어 프롬프트를 생성 중..."):
                        try:
                            # 현재 텍스트 영역의 값을 먼저 저장
                            ip.prompt_korean = new_kr
                            update_state(state)

                            # AI로 영어 프롬프트 생성
                            new_en = translate_prompt_to_english(new_kr, state.script.art_style)
                            ip.prompt_english = new_en
                            update_state(state)
                            st.success("완료!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"오류: {e}")

            global_idx += 1

# 전체 저장 버튼
if st.button("💾 모든 변경사항 저장", use_container_width=True):
    update_state(state)
    st.toast("프롬프트가 저장되었습니다.", icon="✅")

# ──────────────────────────────────────────────
# 3. 이미지 갤러리 (생성 + 확인)
# ──────────────────────────────────────────────
st.divider()
st.header("3. 이미지 갤러리")

total_images = state.script.total_image_count
generated_count = sum(
    1 for s in state.script.sections
    for ip in s.image_prompts
    if ip.generated and ip.image_path and os.path.exists(ip.image_path)
)

# 상단 컨트롤
col_metric, col_btn = st.columns([1, 2])
with col_metric:
    st.metric("생성 진행률", f"{generated_count} / {total_images}",
              delta=f"{int(generated_count/total_images*100)}%" if total_images > 0 else "0%")

with col_btn:
    if generated_count < total_images:
        generate_all = st.button("🎨 전체 이미지 생성 시작", type="primary", use_container_width=True)
    else:
        st.success("✅ 모든 이미지 생성 완료!")
        generate_all = False

# 전체 이미지 목록 구성
all_prompts = []
for section in state.script.sections:
    for ip in section.image_prompts:
        all_prompts.append((section, ip))

# 이미지 확대 보기 다이얼로그
@st.dialog("이미지 상세 보기", width="large")
def show_image_detail(img_path: str, idx: int, section_type: str, prompt_kr: str):
    st.image(img_path, use_container_width=True)
    st.caption(f"**이미지 #{idx + 1}** | 섹션: {section_type}")
    st.caption(f"설명: {prompt_kr}")

# 갤러리 그리드 (3열 - 더 큰 썸네일)
st.markdown("### 📸 이미지 미리보기")
cols_per_row = 3

for row_start in range(0, len(all_prompts), cols_per_row):
    cols = st.columns(cols_per_row)
    for col_idx in range(cols_per_row):
        idx = row_start + col_idx
        if idx >= len(all_prompts):
            break

        section, ip = all_prompts[idx]
        with cols[col_idx]:
            # 카드 스타일 컨테이너
            with st.container(border=True):
                st.caption(f"**#{idx + 1}** | {section.section_type}")

                if ip.image_path and os.path.exists(ip.image_path):
                    # 이미지 표시
                    st.image(ip.image_path, use_container_width=True)

                    # 버튼 그룹 (2열)
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("🔍 확대", key=f"view_{idx}", use_container_width=True):
                            show_image_detail(ip.image_path, idx, section.section_type, ip.prompt_korean)

                    with btn_col2:
                        # 재생성 버튼
                        if st.button("🔄 재생성", key=f"regen_{idx}", use_container_width=True):
                            with st.spinner(f"이미지 #{idx + 1} 재생성 중..."):
                                try:
                                    img_gen = ImageGenerator()
                                    full_prompt = f"{state.script.art_style}. {ip.prompt_english}"
                                    filename = img_gen.get_output_path(idx, section.section_type,
                                                                       all_prompts[:idx+1].count((section, ip)) - 1)
                                    img_path = img_gen.generate_image(full_prompt, filename)
                                    ip.image_path = img_path
                                    ip.generated = True
                                    update_state(state)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"재생성 실패: {e}")

                    # 다운로드 버튼
                    with open(ip.image_path, "rb") as f:
                        st.download_button(
                            "⬇️ 다운로드",
                            data=f.read(),
                            file_name=f"{idx + 1:02d}_{section.section_type}.png",
                            mime="image/png",
                            key=f"dl_{idx}",
                            use_container_width=True
                        )

                    st.caption(f"💭 {ip.prompt_korean[:50]}..." if len(ip.prompt_korean) > 50 else ip.prompt_korean)
                else:
                    # 미생성 상태
                    st.info("🖼️ 생성 대기 중", icon="⏳")
                    st.caption(f"{ip.prompt_korean[:40]}..." if len(ip.prompt_korean) > 40 else ip.prompt_korean)

# 전체 이미지 생성 로직
if generate_all:
    st.divider()
    st.subheader("🎨 이미지 생성 중...")

    img_gen = ImageGenerator()
    progress_bar = st.progress(0, text="이미지 생성 준비 중...")
    status_container = st.container()
    gallery_preview = st.container()

    global_idx = 0
    for i, section in enumerate(state.script.sections):
        for j, ip in enumerate(section.image_prompts):
            if ip.generated and ip.image_path:
                global_idx += 1
                continue

            progress_bar.progress(
                global_idx / total_images,
                text=f"이미지 {global_idx + 1}/{total_images} 생성 중... ({section.section_type})"
            )

            with status_container:
                st.caption(f"🎨 프롬프트: {ip.prompt_korean[:80]}...")

            try:
                full_prompt = f"{state.script.art_style}. {ip.prompt_english}"
                filename = img_gen.get_output_path(global_idx, section.section_type, j)
                img_path = img_gen.generate_image(full_prompt, filename)

                ip.image_path = img_path
                ip.generated = True
                update_state(state)

                # 갤러리 미리보기 업데이트
                with gallery_preview:
                    cols = st.columns(4)
                    with cols[global_idx % 4]:
                        st.image(img_path, caption=f"✅ #{global_idx + 1}", use_container_width=True)

            except Exception as e:
                st.error(f"이미지 #{global_idx + 1} 생성 실패: {e}")

            global_idx += 1
            time.sleep(1)  # API 레이트 리밋 방지

    progress_bar.progress(1.0, text="모든 이미지 생성 완료!")
    st.balloons()
    st.rerun()

# 전체 ZIP 다운로드
if generated_count > 0:
    st.divider()
    if st.button("📦 전체 이미지 ZIP 다운로드", type="primary", use_container_width=True):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, (section, ip) in enumerate(all_prompts):
                if ip.image_path and os.path.exists(ip.image_path):
                    filename = f"{idx + 1:02d}_{section.section_type}.png"
                    with open(ip.image_path, "rb") as f:
                        zf.writestr(filename, f.read())

        st.download_button(
            "💾 ZIP 파일 저장",
            data=zip_buffer.getvalue(),
            file_name=f"{state.script.bible_reference}_images.zip",
            mime="application/zip",
            use_container_width=True
        )

# ──────────────────────────────────────────────
# 5. 다음 단계
# ──────────────────────────────────────────────
st.divider()
if st.button("다음 단계 (음성 생성) 👉", type="primary"):
    if generated_count < total_images:
        st.warning(f"아직 {total_images - generated_count}개의 이미지가 생성되지 않았습니다.")
        if st.button("그래도 진행하기"):
            st.switch_page("pages/3_voice.py")
    else:
        st.switch_page("pages/3_voice.py")
