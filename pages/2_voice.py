import streamlit as st
from utils.session_state import get_state, update_state
from core.voice_synthesizer import VoiceSynthesizer
from core.audio_processor import AudioProcessor
from models.data_models import AudioBlock

st.title("Step 2: 음성")
state = get_state()

if not state.script:
    st.warning("⚠️ 먼저 Step 1에서 스크립트를 생성해주세요.")
    if st.button("Step 1으로 이동"):
        st.switch_page("pages/1_script.py")
    st.stop()

# --- Voice Selection ---
st.header("1. 목소리 선택")

try:
    synthesizer = VoiceSynthesizer()
    
    # 세션에 음성 목록 캐싱 (API 호출 최소화)
    if "voice_list" not in st.session_state:
        with st.spinner("ElevenLabs 음성 목록을 불러오는 중..."):
            st.session_state.voice_list = synthesizer.get_all_voices()
    
    voices = st.session_state.voice_list
    
    # 현재 선택된 보이스 인덱스 찾기
    voice_names = list(voices.keys())
    current_index = 0
    if state.selected_voice_id:
        # ID로 이름 찾기
        for name, vid in voices.items():
            if vid == state.selected_voice_id:
                if name in voice_names:
                    current_index = voice_names.index(name)
                break
    
    selected_name = st.selectbox("사용할 목소리를 선택하세요", options=voice_names, index=current_index)
    selected_id = voices[selected_name]
    
    if state.selected_voice_id != selected_id:
        state.selected_voice_id = selected_id
        update_state(state)
        
except Exception as e:
    st.error(f"음성 목록 로드 실패: {e}")
    st.stop()

# --- Audio Generation ---
st.divider()
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.header("2. 섹션별 오디오 생성")
with col_h2:
    if st.button("🔄 스크립트 동기화", help="스크립트 수정사항을 반영하여 오디오 블록을 초기화합니다."):
        state.audio_blocks = []
        update_state(state)
        st.rerun()

# AudioBlock 리스트 초기화 (아직 없으면 스크립트 기반으로 생성)
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
    st.progress(confirmed_count / total_count)

for i, block in enumerate(state.audio_blocks):
    section = state.script.sections[i]
    
    # 텍스트 변경 감지 및 자동 업데이트
    if block.text != section.content:
        block.text = section.content
        block.confirmed = False # 내용이 바뀌었으므로 확정 해제
    
    # 상태 아이콘 및 스타일 결정
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
        col_text, col_ctrl = st.columns([3, 1])
        
        with col_text:
            st.text_area("대본", value=block.text, height=80, disabled=True, key=f"txt_{i}")
            if voice_mismatch:
                st.caption(f"⚠️ 생성된 목소리({block.voice_id[:8]}...)가 현재 선택된 목소리와 다릅니다.")
            
        with col_ctrl:
            btn_label = "재생성" if block.audio_data else "음성 생성"
            if st.button(f"🔊 {btn_label}", key=f"btn_gen_{i}", type="primary" if not block.audio_data else "secondary"):
                with st.spinner("생성 중..."):
                    try:
                        audio_data = synthesizer.generate_audio(block.text, state.selected_voice_id)
                        block.audio_data = audio_data
                        block.voice_id = state.selected_voice_id
                        block.confirmed = False # 재생성 시 확정 해제
                        update_state(state)
                        st.rerun()
                    except Exception as e:
                        st.error(f"실패: {e}")

        # 생성된 오디오가 있으면 플레이어 표시
        if block.audio_data:
            col_play, col_confirm = st.columns([3, 1])
            with col_play:
                st.audio(block.audio_data, format="audio/mp3")
            with col_confirm:
                is_confirmed = st.checkbox("확정", value=block.confirmed, key=f"chk_{i}")
                if is_confirmed != block.confirmed:
                    block.confirmed = is_confirmed
                    update_state(state)
                    st.rerun()

# --- Final Merge ---
st.divider()
st.header("3. 전체 오디오 병합")

if st.button("🎵 전체 오디오 병합 및 확정", type="primary"):
    # 미확정 블록 경고
    not_confirmed = [b.section_index + 1 for b in state.audio_blocks if not b.confirmed]
    missing_audio = [b.section_index + 1 for b in state.audio_blocks if not b.audio_data]
    
    if missing_audio:
        st.error(f"다음 섹션의 오디오가 아직 생성되지 않았습니다: {missing_audio}")
    elif not_confirmed:
        st.warning(f"아직 확정되지 않은 섹션이 있습니다: {not_confirmed}. 모든 섹션을 확정(체크)해주세요.")
    else:
        with st.spinner("오디오 병합 및 타임스탬프 계산 중..."):
            try:
                # ScriptSection 메타데이터 준비
                sections_meta = [{"section_type": s.section_type} for s in state.script.sections]
                
                final_audio, timestamps = processor.merge_audio_blocks(state.audio_blocks, sections_meta)
                
                state.final_audio_bytes = final_audio
                state.timestamps = timestamps
                update_state(state)
                
                st.success("오디오 병합 완료! 다음 단계로 이동하세요.")
                if st.button("다음 단계 (비주얼 생성) 👉"):
                    st.switch_page("pages/3_visual.py")
            except Exception as e:
                st.error(f"병합 실패: {e}")

if state.final_audio_bytes:
    st.subheader("최종 결과물 미리듣기")
    st.audio(state.final_audio_bytes, format="audio/mp3")
