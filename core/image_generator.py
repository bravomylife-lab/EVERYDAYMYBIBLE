import os
import time
from typing import List
import google.generativeai as genai
from PIL import Image

from models.data_models import ScriptData
from utils.config import load_env, require_env

class ImageGenerator:
    def __init__(self):
        load_env()
        self.api_key = require_env("GOOGLE_API_KEY")
        genai.configure(api_key=self.api_key)
        # 요청하신 모델명 설정
        self.model_name = "gemini-3-pro-image-preview"
        
        # 출력 디렉토리 생성
        self.output_dir = "output/Images"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_image(self, prompt: str, filename: str) -> str:
        """
        Google GenAI를 사용하여 이미지를 생성하고 저장합니다.
        Returns: 저장된 파일 경로
        """
        try:
            # ImageGenerationModel 초기화
            # 주의: 해당 모델이 사용자의 계정에서 접근 가능해야 합니다.
            model = genai.ImageGenerationModel(self.model_name)
            
            response = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="9:16", # 숏폼 비율
                safety_filter_level="block_only_high",
            )
            
            if not response.images:
                raise RuntimeError("No images returned from API")

            # PIL Image 객체 추출
            image = response.images[0]._pil_image
            
            # 파일 저장
            save_path = os.path.join(self.output_dir, filename)
            image.save(save_path, format="PNG")
            
            return save_path

        except Exception as e:
            # 모델명 오류 등의 경우 폴백(Fallback) 또는 에러 메시지 구체화가 필요할 수 있음
            raise RuntimeError(f"Image generation failed with model '{self.model_name}': {str(e)}")

    def get_output_path(self, index: int, section_name: str) -> str:
        """
        파일 저장 경로 규칙 생성
        예: 01_Opening.png (순서_섹션명.png)
        """
        # 파일명에 타임스탬프는 나중에 오디오와 결합할 때 정확해지므로, 
        # 여기서는 순서(Index)를 기준으로 생성합니다.
        safe_name = "".join(c for c in section_name if c.isalnum())
        return f"{index:02d}_{safe_name}.png"