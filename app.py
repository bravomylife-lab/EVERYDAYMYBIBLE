import streamlit as st

from utils.session_state import init_session_state

st.set_page_config(
    page_title="EverydayBible",
    page_icon="📖",
    layout="wide",
)

init_session_state()

pages = [
    st.Page("pages/1_script.py", title="1. 스크립트", icon="📝"),
    st.Page("pages/2_voice.py", title="2. 음성", icon="🎙️"),
    st.Page("pages/3_visual.py", title="3. 비주얼", icon="🖼️"),
    st.Page("pages/4_export.py", title="4. 내보내기", icon="📦"),
    st.Page("pages/5_youtube.py", title="5. 유튜브", icon="▶️"),
]

nav = st.navigation(pages)
nav.run()
