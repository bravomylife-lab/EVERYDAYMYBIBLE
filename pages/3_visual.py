import streamlit as st

from utils.session_state import get_state

st.title("Step 3: 비주얼")
state = get_state()

st.info("Phase 4에서 이미지 생성 및 텍스트 오버레이를 구현합니다.")

st.write("생성된 이미지 수:", len(state.generated_images))
