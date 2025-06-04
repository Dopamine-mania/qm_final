import torch
from transformers import AutoProcessor, AutoModel
from typing import Optional, Dict, Any, List
import logging
import os
import numpy as np
from scipy.io import wavfile
import soundfile as sf

class SpeechGenerator:
    def __init__(self, model_id: str = "suno/bark"):
        """
        初始化语音生成器
        
        Args:
            model_id: 语音生成模型ID，默认使用Bark
        """
        self.logger = logging.getLogger(__name__)
        self.model_id = model_id
        self.processor = None
        self.model = None
        
    def load_model(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        """
        加载模型
        
        Args:
            device: 运行设备
        """
        try:
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            self.model = AutoModel.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            ).to(device)
            self.logger.info(f"Model loaded successfully on {device}")
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            raise
            
    def generate_speech(
        self,
        text: str,
        voice_preset: Optional[str] = None,
        language: str = "en",
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成语音
        
        Args:
            text: 要转换的文本
            voice_preset: 声音预设（可选）
            language: 语言代码
            temperature: 采样温度
            **kwargs: 其他参数
            
        Returns:
            包含生成语音信息的字典
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
            
        try:
            # 准备输入
            inputs = self.processor(
                text=text,
                voice_preset=voice_preset,
                return_tensors="pt"
            ).to(self.model.device)
            
            # 生成语音
            with torch.no_grad():
                output = self.model.generate(
                    **inputs,
                    do_sample=True,
                    temperature=temperature,
                    **kwargs
                )
            
            # 转换为numpy数组
            audio_array = output.cpu().numpy().squeeze()
            
            return {
                "audio": audio_array,
                "text": text,
                "voice_preset": voice_preset,
                "language": language,
                "parameters": {
                    "temperature": temperature,
                    **kwargs
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating speech: {str(e)}")
            raise
            
    def save_audio(self, audio: np.ndarray, output_path: str, sample_rate: int = 24000):
        """
        保存生成的音频
        
        Args:
            audio: 音频数据
            output_path: 输出路径
            sample_rate: 采样率
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 保存音频文件
            sf.write(output_path, audio, sample_rate)
            self.logger.info(f"Audio saved to {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving audio: {str(e)}")
            raise
            
    def get_available_voices(self) -> List[str]:
        """
        获取可用的声音预设列表
        
        Returns:
            声音预设列表
        """
        return [
            "v2/en_speaker_0",  # 英语男声
            "v2/en_speaker_1",  # 英语女声
            "v2/zh_speaker_0",  # 中文男声
            "v2/zh_speaker_1",  # 中文女声
            "v2/ja_speaker_0",  # 日语男声
            "v2/ja_speaker_1",  # 日语女声
        ] 