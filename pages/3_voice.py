import streamlit as st
from utils.session_state import get_state, update_state
from core.voice_synthesizer import VoiceSynthesizer
from core.audio_processor import AudioProcessor
from models.data_models import AudioBlock

st.title("Step 3: 음성")
state = get_state()

if not state.script:
    st.warning("먼저 Step 1에서 스크립트를 생성해주세요.")
    if st.button("Step 1으로 이동"):
        st.switch_page("pages/1_script.py")
    st.stop()

# ──────────────────────────────────────────────
# 1. 확정된 대본 미리보기
# ──────────────────────────────────────────────
st.header("1. 확정된 대본")
with st.expander("대본 전체 보기", expanded=False):
    for i, section in enumerate(state.script.sections):
        st.markdown(f"**{section.section_type}**")
        st.text(section.content)
        st.markdown("---")

# ──────────────────────────────────────────────
# 2. 목소리 선택 (5개 프리셋 + 전체 목록)
# ──────────────────────────────────────────────
st.header("2. 목소리 선택")

try:
    synthesizer = VoiceSynthesizer()

    # 세션에 음성 목록 캐싱
    if "voice_list" not in st.session_state:
        with st.spinner("ElevenLabs 음성 목록을 불러오는 중..."):
            st.session_state.voice_list = synthesizer.get_all_voices()

    voices = st.session_state.voice_list
    voice_names = list(voices.keys())

    # 추천 목소리 5개 (있으면 상단에 표시)
    RECOMMENDED_VOICES = ["Rachel", "Josh", "Arnold", "Bella", "Antoni"]
    available_recommended = [v for v in RECOMMENDED_VOICES if v in voice_names]
    other_voices = [v for v in voice_names if v not in RECOMMENDED_VOICES]

    # 현재 선택된 보이스 인덱스 찾기
    display_voices = available_recommended + other_voices
    current_index = 0
    if state.selected_voice_id:
        for name, vid in voices.items():
            if vid == state.selected_voice_id and name in display_voices:
                current_index = display_voices.index(name)
                break

    col_voice, col_info = st.columns([2, 1])
    with col_voice:
        selected_name = st.selectbox(
            "사용할 목소리를 선택하세요",
            options=display_voices,
            index=current_index,
            help="상단 5개는 추천 목소리입니다"
        )
        selected_id = voices[selected_name]

        if state.selected_voice_id != selected_id:
            state.selected_voice_id = selected_id
            update_state(state)

    with col_info:
        st.info(f"선택: **{selected_name}**")

except Exception as e:
    st.error(f"음성 목록 로드 실패: {e}")
    st.stop()

# ──────────────────────────────────────────────
# 3. 섹션별 오디오 생성
# ──────────────────────────────────────────────
st.divider()
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.header("3. 섹션별 오디오 생성")
with col_h2:
    if st.button("🔄 스크립트 동기화", help="스크립트 수정사항을 반영하여 오디오 블록을 초기화합니다."):
        state.audio_blocks = []
        update_state(state)
        st.rerun()

# AudioBlock 리스트 초기화
if not state.audio_blocks:
    state.audio_blocks = [
        AudioBlock(section_index=i, text=section.content)
        for i, section in enumerate(state.script.sections)
    ]
    update_state(state)

processor = AudioProcessor()

# 진행률 표시
confirmed_count = sum(1 for b in state.audio_blocks if b.confirmed)
total_count = len(state.audio_blocks)
if total_count > 0:
    st.progress(confirmed_count / total_count, text=f"확정: {confirmed_count}/{total_count}")

for i, block in enumerate(state.audio_blocks):
    section = state.script.sections[i]

    # 텍스트 변경 감지
    if block.text != section.content:
        block.text = section.content
        block.confirmed = False

    # 상태 아이콘
    status_icon = "⬜"
    if block.confirmed:
        status_icon = "✅"
    elif block.audio_data:
        status_icon = "🔊"

    # 보이스 불일치 감지
    voice_mismatch = False
    if block.audio_data and block.voice_id != state.selected_voice_id:
        voice_mismatch = True
        status_icon = "⚠️"

    with st.expander(f"{status_icon} Section {i+1}: {section.section_type}", expanded=not block.confirmed):
        # 대본 표시
        st.text(block.text)

        if voice_mismatch:
            st.caption("⚠️ 생성된 목소리가 현재 선택된 목소리와 다릅니다.")

        col_gen, col_confirm = st.columns([1, 1])
        with col_gen:
            btn_label = "재생성" if block.audio_data else "음성 생성"
            if st.button(f"🔊 {btn_label}", key=f"btn_gen_{i}", type="primary" if not block.audio_data else "secondary", use_container_width=True):
                with st.spinner("생성 중..."):
                    try:
                        audio_data = synthesizer.generate_audio(block.text, state.selected_voice_id)
                        block.audio_data = audio_data
                        block.voice_id = state.selected_voice_id
                        block.confirmed = False
                        update_state(state)
                        st.rerun()
                    except Exception as e:
                        st.error(f"실패: {e}")

        with col_confirm:
            if block.audio_data:
                is_confirmed = st.checkbox("확정", value=block.confirmed, key=f"chk_{i}")
                if is_confirmed != block.confirmed:
                    block.confirmed = is_confirmed
                    update_state(state)
                    st.rerun()

        # 오디오 플레이어 (play/stop + 스크롤 지원)
        if block.audio_data:
            st.audio(block.audio_data, format="audio/mp3")
            if block.duration_seconds > 0:
                st.caption(f"길이: {block.duration_seconds:.1f}초")

# ──────────────────────────────────────────────
# 4. 전체 오디오 병합
# ──────────────────────────────────────────────
st.divider()
st.header("4. 전체 오디오 병합")

if st.button("🎵 전체 오디오 병합 및 확정", type="primary", use_container_width=True):
    not_confirmed = [b.section_index + 1 for b in state.audio_blocks if not b.confirmed]
    missing_audio = [b.section_index + 1 for b in state.audio_blocks if not b.audio_data]

    if missing_audio:
        st.error(f"다음 섹션의 오디오가 아직 생성되지 않았습니다: {missing_audio}")
    elif not_confirmed:
        st.warning(f"아직 확정되지 않은 섹션이 있습니다: {not_confirmed}. 모든 섹션을 확정(체크)해주세요.")
    else:
        with st.spinner("오디오 병합 및 타임스탬프 계산 중..."):
            try:
                sections_meta = [{"section_type": s.section_type} for s in state.script.sections]
                final_audio, timestamps = processor.merge_audio_blocks(state.audio_blocks, sections_meta)

                state.final_audio_bytes = final_audio
                state.timestamps = timestamps
                update_state(state)

                st.success("오디오 병합 완료!")
            except Exception as e:
                st.error(f"병합 실패: {e}")

# ──────────────────────────────────────────────
# 5. 최종 결과물 & 섹션별 시간 데이터
# ──────────────────────────────────────────────
if state.final_audio_bytes:
    st.divider()
    st.header("5. 최종 오디오")
    st.audio(state.final_audio_bytes, format="audio/mp3")

    # 섹션별 소요 시간 데이터 (CapCut 편집용)
    if state.timestamps:
        st.subheader("섹션별 소요 시간 (CapCut 편집용)")
        time_data = []
        for ts in state.timestamps:
            duration = ts.end_time_seconds - ts.start_time_seconds
            time_data.append({
                "섹션": ts.section_type,
                "시작": f"{ts.start_time_seconds:.1f}s",
                "종료": f"{ts.end_time_seconds:.1f}s",
                "길이": f"{duration:.1f}s"
            })
        st.table(time_data)

        # 이미지-시간 매핑 데이터
        st.subheader("이미지별 예상 시간 (CapCut 배치용)")
        img_time_data = []
        for idx, section in enumerate(state.script.sections):
            if idx < len(state.timestamps):
                ts = state.timestamps[idx]
                section_duration = ts.end_time_seconds - ts.start_time_seconds
                num_images = len(section.image_prompts)
                per_image = section_duration / max(num_images, 1)

                for j, ip in enumerate(section.image_prompts):
                    img_start = ts.start_time_seconds + (j * per_image)
                    img_end = img_start + per_image
                    img_time_data.append({
                        "이미지": f"#{sum(len(s.image_prompts) for s in state.script.sections[:idx]) + j + 1}",
                        "섹션": section.section_type,
                        "설명": ip.prompt_korean[:30] + "...",
                        "시작": f"{img_start:.1f}s",
                        "종료": f"{img_end:.1f}s",
                        "길이": f"{per_image:.1f}s"
                    })

        if img_time_data:
            st.table(img_time_data)

    st.divider()
    if st.button("다음 단계 (내보내기) 👉", type="primary"):
        st.switch_page("pages/4_export.py")
