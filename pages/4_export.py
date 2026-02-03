import streamlit as st

from utils.session_state import get_state

st.title("Step 4: 내보내기")
state = get_state()

st.info("Phase 5에서 SRT 및 ZIP 내보내기 기능을 구현합니다.")

st.write("SRT 준비 여부:", bool(state.srt_content))
