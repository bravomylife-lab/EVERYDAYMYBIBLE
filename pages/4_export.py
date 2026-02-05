import streamlit as st

from core.exporter import build_zip_package
from core.subtitle_generator import SubtitleGenerator
from utils.session_state import get_state, update_state

st.title("Step 4: 내보내기")
state = get_state()

if not state.script or not state.audio_blocks:
	st.warning("⚠️ 먼저 Step 1~2에서 스크립트와 음성을 생성해주세요.")
	if st.button("Step 2로 이동"):
		st.switch_page("pages/2_voice.py")
	st.stop()

st.header("1. SRT 생성")
generator = SubtitleGenerator()

if st.button("📝 SRT 생성하기", type="primary"):
	with st.spinner("SRT 생성 중..."):
		try:
			srt_text = generator.generate_srt(
				audio_bytes=state.final_audio_bytes,
				sections=state.script.sections,
				audio_blocks=state.audio_blocks,
				timestamps=state.timestamps,
			)
			state.srt_content = srt_text
			update_state(state)
			st.success("SRT 생성 완료")
		except Exception as e:
			st.error(f"SRT 생성 실패: {e}")

if state.srt_content:
	st.subheader("SRT 미리보기")
	st.code(state.srt_content, language="srt")

st.divider()
st.header("2. ZIP 패키지 내보내기")

if not state.srt_content:
	st.info("먼저 SRT를 생성해주세요.")
else:
	if st.button("📦 ZIP 만들기"):
		with st.spinner("ZIP 패키지 생성 중..."):
			try:
				zip_bytes = build_zip_package(
					bible_reference=state.script.bible_reference,
					script=state.script,
					final_audio_bytes=state.final_audio_bytes,
					srt_content=state.srt_content,
					image_paths=state.generated_images,
					timestamps=state.timestamps,
				)
				st.download_button(
					"ZIP 다운로드",
					data=zip_bytes,
					file_name=f"{state.script.bible_reference}.zip",
					mime="application/zip",
				)
			except Exception as e:
				st.error(f"ZIP 생성 실패: {e}")
