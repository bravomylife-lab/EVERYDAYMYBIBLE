import streamlit as st

from models.data_models import ProjectState


def init_session_state() -> None:
    if "project_state" not in st.session_state:
        st.session_state.project_state = ProjectState()


def get_state() -> ProjectState:
    if "project_state" not in st.session_state:
        init_session_state()
    return st.session_state.project_state


def update_state(new_state: ProjectState) -> None:
    st.session_state.project_state = new_state


def reset_session_state() -> None:
    st.session_state.project_state = ProjectState()
    for key in [
        "script_confirmed",
        "full_script_text",
        "voice_list",
        "images_confirmed",
    ]:
        if key in st.session_state:
            del st.session_state[key]
