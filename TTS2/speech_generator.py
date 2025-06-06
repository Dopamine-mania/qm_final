import torch
from TTS.api import TTS
from typing import Optional, Dict, Any, List
import logging
import os
import numpy as np
import soundfile as sf

class SpeechGenerator:
    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/your_tts"):
        """
        初始化语音生成器
        
        Args:
            model_name: TTS模型名称，默认使用YourTTS模型
        """
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self.tts = None
        
    def load_model(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        """
        加载模型
        
        Args:
            device: 运行设备
        """
        try:
            self.tts = TTS(model_name=self.model_name).to(device)
            self.logger.info(f"Model loaded successfully on {device}")
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            raise
            
    def generate_speech(
        self,
        text: str,
        speaker_wav: Optional[str] = None,
        language: str = "en",
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成语音
        
        Args:
            text: 要转换的文本
            speaker_wav: 说话人参考音频文件路径（可选）
            language: 语言代码
            **kwargs: 其他参数
            
        Returns:
            包含生成语音信息的字典
        """
        if self.tts is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
            
        try:
            # 生成语音
            wav = self.tts.tts(
                text=text,
                speaker_wav=speaker_wav,
                language=language,
                **kwargs
            )
            
            return {
                "audio": wav,
                "text": text,
                "speaker_wav": speaker_wav,
                "language": language,
                "parameters": kwargs
            }
            
        except Exception as e:
            self.logger.error(f"Error generating speech: {str(e)}")
            raise
            
    def save_audio(self, wav, output_path: str, sample_rate: int = 22050):
        """
        保存生成的音频
        
        Args:
            wav: 音频数据
            output_path: 输出路径
            sample_rate: 采样率
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 保存音频文件
            self.tts.save_wav(wav=wav, path=output_path, sample_rate=sample_rate)
            self.logger.info(f"Audio saved to {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving audio: {str(e)}")
            raise
            
    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表
        
        Returns:
            模型列表
        """
        return [
            "tts_models/multilingual/multi-dataset/your_tts",  # 多语言模型，支持中英文
            "tts_models/zh-CN/baker/tacotron2-DDC-GST",       # 中文模型
            "tts_models/en/ljspeech/tacotron2-DDC",           # 英文模型
            "tts_models/en/vctk/vits",                        # 英文模型（VITS）
            "tts_models/zh-CN/baker/tacotron2-DDC-GST"        # 中文模型（GST）
        ]
        
    def get_available_languages(self) -> Dict[str, str]:
        """
        获取支持的语言列表
        
        Returns:
            语言代码到语言名称的映射
        """
        return {
            "en": "English",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian"
        } 