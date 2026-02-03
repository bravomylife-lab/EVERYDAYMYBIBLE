import streamlit as st

from utils.session_state import get_state

st.title("Step 5: 유튜브")
state = get_state()

st.info("Phase 6에서 유튜브 메타데이터 생성 UI를 구현합니다.")

if state.youtube_metadata:
    st.write("제목 후보:", state.youtube_metadata.title_candidates)
else:
    st.write("메타데이터가 아직 없습니다.")
