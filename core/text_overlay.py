import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

class TextOverlay:
    def __init__(self):
        # 폰트 경로 설정 (없으면 기본 폰트 사용 시도)
        self.font_path = "assets/fonts/NanumSquareRoundB.ttf"
        self.default_font_size = 50

    def add_text_to_image(self, image_path: str, text: str) -> str:
        """
        이미지에 텍스트(자막)를 오버레이하고 덮어씁니다.
        """
        try:
            img = Image.open(image_path).convert("RGBA")
            draw = ImageDraw.Draw(img)
            width, height = img.size

            # 폰트 로드
            try:
                font = ImageFont.truetype(self.font_path, self.default_font_size)
            except IOError:
                # 폰트 파일이 없으면 기본 폰트 로드 (한글 깨질 수 있음)
                font = ImageFont.load_default()
                print(f"Warning: Font file not found at {self.font_path}. Using default font.")

            # 텍스트 줄바꿈 (이미지 너비의 80% 기준)
            # 대략적인 글자 수 계산 (한글 기준)
            chars_per_line = int((width * 0.8) / self.default_font_size)
            wrapped_text = textwrap.fill(text, width=chars_per_line)

            # 텍스트 크기 계산 (bbox 사용)
            bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align="center")
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 위치 계산 (중앙 하단)
            x = (width - text_width) / 2
            y = height * 0.75  # 하단 75% 지점

            # 텍스트 배경 (반투명 검정 박스) - 가독성 확보
            padding = 20
            bg_x0 = x - padding
            bg_y0 = y - padding
            bg_x1 = x + text_width + padding
            bg_y1 = y + text_height + padding
            
            # 반투명 레이어 생성
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw_overlay = ImageDraw.Draw(overlay)
            draw_overlay.rectangle(
                [bg_x0, bg_y0, bg_x1, bg_y1], 
                fill=(0, 0, 0, 120) # 검정색, 투명도 120
            )
            
            # 원본과 합성
            img = Image.alpha_composite(img, overlay)
            draw = ImageDraw.Draw(img)

            # 텍스트 그리기 (그림자 효과 + 흰색 글씨)
            shadow_offset = 2
            # 그림자
            draw.multiline_text(
                (x + shadow_offset, y + shadow_offset), 
                wrapped_text, 
                font=font, 
                fill=(0, 0, 0, 200), 
                align="center"
            )
            # 본문
            draw.multiline_text(
                (x, y), 
                wrapped_text, 
                font=font, 
                fill=(255, 255, 255, 255), 
                align="center"
            )

            # 저장 (RGB로 변환하여 PNG 저장)
            img = img.convert("RGB")
            img.save(image_path)
            return image_path

        except Exception as e:
            raise RuntimeError(f"Failed to add text overlay: {str(e)}")