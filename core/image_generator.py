import os
from google import genai
from google.genai import types
from PIL import Image
import io

from utils.config import load_env, require_env


class ImageGenerator:
    def __init__(self):
        load_env()
        self.api_key = require_env("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-3-pro-image-preview"

        self.output_dir = "output/Images"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_image(self, prompt: str, filename: str) -> str:
        """
        Google GenAI (Imagen 3)를 사용하여 이미지를 생성하고 저장합니다.
        Returns: 저장된 파일 경로
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'],
                    image_config=types.ImageConfig(
                        aspect_ratio="16:9"
                    ),
                )
            )

            # response.parts에서 이미지 추출
            image_found = False
            for part in response.parts:
                if image := part.as_image():
                    save_path = os.path.join(self.output_dir, filename)
                    image.save(save_path)
                    image_found = True
                    return save_path

            if not image_found:
                raise RuntimeError("No images returned from API")

        except Exception as e:
            raise RuntimeError(f"Image generation failed: {str(e)}")

    def get_output_path(self, global_index: int, section_name: str, sub_index: int = 0) -> str:
        """
        파일 저장 경로 규칙 생성
        예: 01_Opening_00.png (전체순서_섹션명_서브인덱스.png)
        """
        safe_name = "".join(c for c in section_name if c.isalnum())
        return f"{global_index:02d}_{safe_name}_{sub_index:02d}.png"
