import streamlit as st
from utils.session_state import get_state, update_state
from core.script_generator import ScriptGenerator
from utils.bible_parser import parse_bible_reference
from utils.bible_data import BIBLE_DATA

st.title("Step 1: 스크립트")
state = get_state()

if "script_confirmed" not in st.session_state:
    st.session_state.script_confirmed = False
if not state.script:
    st.session_state.script_confirmed = False

def build_full_script_text(sections):
    parts = []
    for section in sections:
        parts.append(f"### {section.section_type}\n{section.content.strip()}")
    return "\n\n".join(parts).strip() + "\n"

def apply_full_script_text(text, sections):
    lines = [line.rstrip() for line in text.splitlines()]
    current_type = None
    buffer = []
    contents = {}

    def flush():
        nonlocal buffer, current_type
        if current_type is not None:
            contents[current_type] = "\n".join(buffer).strip()
        buffer = []

    for line in lines:
        if line.startswith("### "):
            flush()
            current_type = line.replace("### ", "").strip()
        else:
            buffer.append(line)
    flush()

    for section in sections:
        if section.section_type in contents and contents[section.section_type]:
            section.content = contents[section.section_type]

# --- Input Section ---
st.header("1. 성경 본문 선택")

def generate_script_action(passage):
    """대본 생성 로직을 수행하는 함수"""
    state.bible_passage = parse_bible_reference(passage)
    update_state(state)
    
    generator = ScriptGenerator()
    try:
        with st.spinner(f"Claude가 '{passage}' 대본을 작성하고 있습니다... (약 10-20초 소요)"):
            script_data = generator.generate_script(state.bible_passage)
            state.script = script_data
            update_state(state)
            st.session_state.script_confirmed = False
        st.success("대본 생성이 완료되었습니다! 아래에서 내용을 확인하고 수정하세요.")
    except Exception as e:
        st.error(f"오류 발생: {e}")

tab_ot, tab_nt, tab_direct = st.tabs(["구약 성경", "신약 성경", "직접 입력"])

with tab_ot:
    col_book, col_chapter = st.columns([1, 2])
    with col_book:
        ot_books = list(BIBLE_DATA["구약"].keys())
        selected_book_ot = st.selectbox("구약 성경 선택", ot_books, key="sb_ot")
    
    with col_chapter:
        if selected_book_ot:
            chapter_count = BIBLE_DATA["구약"][selected_book_ot]
            chapters = [str(i) for i in range(1, chapter_count + 1)]
            
            # UI 과밀 방지: 장 수가 20장을 넘으면 Selectbox, 아니면 Pills 사용
            if chapter_count > 20:
                selected_chapter_ot = st.selectbox(
                    f"{selected_book_ot} 장 선택", 
                    chapters, 
                    index=None, 
                    placeholder="장을 선택하세요",
                    key="sb_ch_ot"
                )
            else:
                selected_chapter_ot = st.pills(f"{selected_book_ot} 장 선택", chapters, selection_mode="single", key="pl_ot")
            
            if selected_chapter_ot:
                passage_ot = f"{selected_book_ot} {selected_chapter_ot}장"
                if st.button(f"📜 '{passage_ot}' 대본 만들기", key="btn_ot", type="primary"):
                    generate_script_action(passage_ot)

with tab_nt:
    col_book, col_chapter = st.columns([1, 2])
    with col_book:
        nt_books = list(BIBLE_DATA["신약"].keys())
        selected_book_nt = st.selectbox("신약 성경 선택", nt_books, key="sb_nt")
    
    with col_chapter:
        if selected_book_nt:
            chapter_count = BIBLE_DATA["신약"][selected_book_nt]
            chapters = [str(i) for i in range(1, chapter_count + 1)]
            
            # UI 과밀 방지: 장 수가 20장을 넘으면 Selectbox, 아니면 Pills 사용
            if chapter_count > 20:
                selected_chapter_nt = st.selectbox(
                    f"{selected_book_nt} 장 선택", 
                    chapters, 
                    index=None, 
                    placeholder="장을 선택하세요",
                    key="sb_ch_nt"
                )
            else:
                selected_chapter_nt = st.pills(f"{selected_book_nt} 장 선택", chapters, selection_mode="single", key="pl_nt")
            
            if selected_chapter_nt:
                passage_nt = f"{selected_book_nt} {selected_chapter_nt}장"
                if st.button(f"📜 '{passage_nt}' 대본 만들기", key="btn_nt", type="primary"):
                    generate_script_action(passage_nt)

with tab_direct:
    direct_input = st.text_input("성경 구절 직접 입력 (예: 시편 23편)", value=state.bible_passage)
    if st.button("대본 생성하기", key="btn_direct", type="primary"):
        if direct_input:
            generate_script_action(direct_input)
        else:
            st.warning("성경 구절을 입력해주세요.")

# --- Edit Section ---
if state.script:
    st.divider()
    st.header("2. 대본 편집")
    st.info("💡 팁: 숫자가 한글(이십칠장, 일절 등)로 되어 있는지 확인해주세요. 음성 생성 시 훨씬 자연스럽습니다.")

    full_script_default = build_full_script_text(state.script.sections)
    full_script_text = st.text_area(
        "대본 전체 편집",
        value=st.session_state.get("full_script_text", full_script_default),
        height=420,
        help="섹션 구분은 '### 섹션명' 형태로 유지해주세요. 예: ### Opening",
        key="full_script_editor"
    )
    st.session_state.full_script_text = full_script_text

    if not full_script_text.strip():
        st.warning("⚠️ 대본 내용이 비어있습니다.")

    st.divider()

    col_confirm, col_next = st.columns([1, 1])
    with col_confirm:
        if st.button("💾 대본 저장 및 확정"):
            apply_full_script_text(st.session_state.full_script_text, state.script.sections)
            update_state(state)
            st.session_state.script_confirmed = True
            st.toast("대본이 저장되었습니다.", icon="✅")

    if st.session_state.script_confirmed:
        st.header("3. 이미지 스타일 설정")

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

        st.subheader("파트별 이미지 프롬프트")
        for i, section in enumerate(state.script.sections):
            with st.expander(f"Section {i+1}: {section.section_type}", expanded=False):
                new_prompt_kr = st.text_area(
                    "이미지 설명 (한글 - 참고용)",
                    value=section.image_prompt_korean,
                    height=80,
                    key=f"prompt_kr_{i}"
                )
                new_prompt_en = st.text_area(
                    "이미지 프롬프트 (English - Gemini용)",
                    value=section.image_prompt_english,
                    height=80,
                    key=f"prompt_en_{i}"
                )
                section.image_prompt_korean = new_prompt_kr
                section.image_prompt_english = new_prompt_en

        col_save, col_next = st.columns([1, 1])
        with col_save:
            if st.button("💾 대본 및 스타일 저장", type="primary"):
                update_state(state)
                st.toast("대본과 스타일이 저장되었습니다!", icon="✅")

        with col_next:
            if st.button("다음 단계 (음성 생성) 👉"):
                st.switch_page("pages/2_voice.py")
    else:
        st.info("대본을 확정하면 이미지 스타일 설정이 나타납니다.")
