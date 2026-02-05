import streamlit as st
import os
from utils.session_state import get_state, update_state
from core.image_generator import ImageGenerator
from core.text_overlay import TextOverlay

st.title("Step 3: 비주얼")
state = get_state()

if not state.script:
    st.warning("⚠️ 먼저 Step 1에서 스크립트를 생성해주세요.")
    st.stop()

# --- Image Generation ---
st.header("1. 이미지 생성 (Gemini)")
st.caption(f"적용된 스타일: {state.script.art_style}")

img_gen = ImageGenerator()
text_overlay = TextOverlay()

# 생성된 이미지 목록 초기화 (없으면 빈 리스트)
if not state.generated_images:
    state.generated_images = [""] * len(state.script.sections)

for i, section in enumerate(state.script.sections):
    with st.expander(f"Section {i+1}: {section.section_type}", expanded=True):
        col_prompt, col_img = st.columns([1, 1])
        
        with col_prompt:
            st.markdown("**이미지 프롬프트 (English):**")
            st.caption(section.image_prompt_english)
            
            st.markdown("**대본 내용 (자막):**")
            st.text(section.content)
            
            if st.button(f"🎨 이미지 생성", key=f"btn_img_{i}"):
                with st.spinner("Gemini가 그림을 그리고 있습니다..."):
                    try:
                        # 스타일 프롬프트 결합
                        full_prompt = f"{state.script.art_style}. {section.image_prompt_english}"
                        filename = img_gen.get_output_path(i, section.section_type)
                        
                        # 이미지 생성
                        img_path = img_gen.generate_image(full_prompt, filename)
                        
                        # 상태 업데이트
                        state.generated_images[i] = img_path
                        update_state(state)
                        st.rerun()
                    except Exception as e:
                        st.error(f"생성 실패: {e}")

        with col_img:
            current_img = state.generated_images[i]
            if current_img and os.path.exists(current_img):
                st.image(current_img, caption=f"{section.section_type} (원본)")
                
                # 텍스트 오버레이 버튼
                if st.button("🔤 자막 입히기", key=f"btn_txt_{i}"):
                    try:
                        text_overlay.add_text_to_image(current_img, section.content)
                        st.success("자막 적용 완료!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"자막 적용 실패: {e}")
            else:
                st.info("이미지가 아직 생성되지 않았습니다.")

# --- Navigation ---
st.divider()

if st.button("다음 단계 (내보내기) 👉", type="primary"):
    # 모든 이미지가 생성되었는지 확인
    missing_images = [i+1 for i, path in enumerate(state.generated_images) if not path]
    
    if missing_images:
        st.warning(f"⚠️ 아직 이미지가 생성되지 않은 섹션이 있습니다: {missing_images}")
        if st.button("그래도 진행하기"):
             st.switch_page("pages/4_export.py")
    else:
        st.switch_page("pages/4_export.py")
