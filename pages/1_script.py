import streamlit as st
from utils.session_state import get_state, update_state
from core.script_generator import ScriptGenerator
from utils.bible_parser import parse_bible_reference

st.title("Step 1: 스크립트")
state = get_state()

# --- Input Section ---
st.header("1. 성경 본문 입력")
bible_input = st.text_input(
    "묵상할 성경 구절을 입력하세요 (예: 시편 23편)", 
    value=state.bible_passage
)

if st.button("대본 생성하기", type="primary"):
    if not bible_input:
        st.warning("성경 구절을 입력해주세요.")
    else:
        state.bible_passage = parse_bible_reference(bible_input)
        update_state(state)
        
        generator = ScriptGenerator()
        try:
            with st.spinner("Claude가 대본을 작성하고 있습니다... (약 10-20초 소요)"):
                script_data = generator.generate_script(state.bible_passage)
                state.script = script_data
                update_state(state)
            st.success("대본 생성이 완료되었습니다! 아래에서 내용을 확인하고 수정하세요.")
        except Exception as e:
            st.error(f"오류 발생: {e}")

# --- Edit Section ---
if state.script:
    st.divider()
    st.header("2. 대본 및 프롬프트 편집")
    
    # Art Style 설정
    st.subheader("🎨 전체 이미지 스타일")
    
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
    
    # 현재 설정된 스타일이 프리셋에 있는지 확인하여 기본값 설정
    current_preset = "직접 입력"
    for name, prompt in STYLE_PRESETS.items():
        if prompt == state.script.art_style:
            current_preset = name
            break
            
    selected_preset = st.selectbox("스타일 프리셋 선택", options=list(STYLE_PRESETS.keys()), index=list(STYLE_PRESETS.keys()).index(current_preset))
    
    if selected_preset == "직접 입력":
        new_art_style = st.text_input("스타일 프롬프트 직접 입력", value=state.script.art_style)
    else:
        new_art_style = STYLE_PRESETS[selected_preset]
        st.caption(f"적용된 프롬프트: {new_art_style}")
        
    if new_art_style != state.script.art_style:
        state.script.art_style = new_art_style
        update_state(state)

    st.markdown("---")

    # 섹션별 편집
    for i, section in enumerate(state.script.sections):
        with st.expander(f"Section {i+1}: {section.section_type}", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                new_content = st.text_area(
                    f"[{section.section_type}] 대본 내용",
                    value=section.content,
                    height=150,
                    key=f"content_{i}"
                )
                if not new_content.strip():
                    st.warning("⚠️ 대본 내용이 비어있습니다.")
            
            with col2:
                new_prompt_kr = st.text_area(
                    "이미지 설명 (한글 - 참고용)",
                    value=section.image_prompt_korean,
                    height=70,
                    key=f"prompt_kr_{i}"
                )
                new_prompt_en = st.text_area(
                    "이미지 프롬프트 (English - Gemini용)",
                    value=section.image_prompt_english,
                    height=70,
                    key=f"prompt_en_{i}"
                )
            
            # 변경 사항 실시간 반영 (Streamlit 특성상 rerun 시 반영되므로 session state 직접 수정)
            section.content = new_content
            section.image_prompt_korean = new_prompt_kr
            section.image_prompt_english = new_prompt_en

    st.divider()
    
    col_confirm, col_next = st.columns([1, 1])
    with col_confirm:
        if st.button("💾 대본 저장 및 확정"):
            update_state(state)
            st.toast("대본이 저장되었습니다.", icon="✅")
            
    with col_next:
        if st.button("다음 단계 (음성 생성) 👉"):
            st.switch_page("pages/2_voice.py")
