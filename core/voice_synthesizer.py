from typing import Dict

from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

from utils.config import load_env, require_env

class VoiceSynthesizer:
    def __init__(self):
        load_env()
        self.api_key = require_env("ELEVENLABS_API_KEY")
        self.client = ElevenLabs(api_key=self.api_key)

    def get_all_voices(self) -> Dict[str, str]:
        """
        사용 가능한 모든 음성 목록을 가져옵니다.
        Returns: { "Voice Name": "voice_id" } 형태의 딕셔너리
        """
        try:
            response = self.client.voices.get_all()
            voices = {v.name: v.voice_id for v in response.voices}
            if not voices:
                raise RuntimeError("No voices found in ElevenLabs account.")
            return voices
        except Exception as e:
            raise RuntimeError(f"Failed to fetch voices: {str(e)}")

    def generate_audio(self, text: str, voice_id: str) -> bytes:
        """
        텍스트를 음성으로 변환하여 오디오 바이트 데이터를 반환합니다.
        """
        try:
            # 텍스트가 너무 짧거나 비어있으면 예외 처리 또는 빈 바이트 반환
            if not text or not text.strip():
                return b""

            audio_generator = self.client.generate(
                text=text,
                voice=voice_id,
                model="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
            )
            
            # generator에서 모든 청크를 모아 bytes로 변환
            return b"".join(audio_generator)
        except Exception as e:
            raise RuntimeError(f"Failed to generate audio: {str(e)}")