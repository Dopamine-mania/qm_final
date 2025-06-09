import torch
import logging
import os
import sys
import numpy as np
from typing import Optional, Dict, Any, List
from scipy.io.wavfile import write as write_wav
from base_speech_generator import BaseSpeechGenerator

# Add ChatTTS path to sys.path
# This assumes the script is run from a location where `qm_final` is in the parent directory or root
# A more robust solution might involve setting PYTHONPATH environment variable
try:
    # Assuming this script is in qm_final/TTS
    chat_tts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ChatTTS'))
    if chat_tts_path not in sys.path:
        sys.path.append(chat_tts_path)
    import ChatTTS
except ImportError:
    # Fallback for different execution contexts
    try:
        # Assuming execution from qm_final/integration2
        chat_tts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'TTS', 'ChatTTS'))
        if chat_tts_path not in sys.path:
            sys.path.append(chat_tts_path)
        import ChatTTS
    except ImportError:
        print("Could not import ChatTTS. Please check the path.")
        sys.exit(1)

# ChatTTS 默认采样率
SAMPLE_RATE = 24000

# 添加完整的参数类来替代字典
class TextParams:
    def __init__(self, prompt: str):
        self.prompt = prompt
        self.top_P = 0.7
        self.top_K = 20
        self.temperature = 0.7
        self.repetition_penalty = 1.0
        self.max_new_token = 384
        self.min_new_token = 0
        self.show_tqdm = True
        self.ensure_non_empty = True
        self.manual_seed = None

class InferCodeParams:
    def __init__(self, prompt: str, spk_emb: Optional[np.ndarray] = None):
        self.prompt = prompt
        self.spk_emb = spk_emb
        self.spk_smp = None
        self.txt_smp = None
        self.temperature = 0.3
        self.repetition_penalty = 1.05
        self.max_new_token = 2048
        self.stream_batch = 24
        self.stream_speed = 12000
        self.pass_first_n_batches = 2
        self.top_P = 0.7
        self.top_K = 20
        self.min_new_token = 0
        self.show_tqdm = True
        self.ensure_non_empty = True
        self.manual_seed = None

class SpeechGenerator(BaseSpeechGenerator):
    def __init__(self):
        """
        Initializes the Speech Generator using ChatTTS.
        """
        self.logger = logging.getLogger(__name__)
        self.chat = ChatTTS.Chat()
        self.model_loaded = False

    def load_model(self, source='local', **kwargs):
        """
        Loads the ChatTTS model.

        Args:
            source (str): The source to load the model from ('local', 'huggingface', 'custom').
            **kwargs: Additional arguments for chat.load().
        """
        if self.model_loaded:
            self.logger.info("ChatTTS model is already loaded.")
            return

        try:
            # Change directory to the ChatTTS root to ensure it finds asset/config folders
            # This is based on the notebook's `os.chdir(root_dir)`
            original_dir = os.getcwd()
            chat_tts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ChatTTS'))
            os.chdir(chat_tts_root)
            
            self.chat.load(source=source, **kwargs)
            self.model_loaded = True
            self.logger.info(f"ChatTTS model loaded successfully from source: {source}.")

        except Exception as e:
            self.logger.error(f"Error loading ChatTTS model: {e}")
            raise
        finally:
            # Restore the original directory
            os.chdir(original_dir)

    def generate_speech(
        self,
        text: str,
        speaker: Optional[np.ndarray] = None,
        speed: Optional[int] = 5,
        oral: Optional[int] = 2,
        laugh: Optional[int] = 0,
        break_val: Optional[int] = 6,
        temperature: float = 0.3,
        generate_subtitles: bool = True,  # 添加字幕生成选项
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generates speech from text.

        Args:
            text (str): The input text.
            speaker (np.ndarray, optional): A sampled random speaker embedding. Defaults to None for random speaker.
            speed (int, optional): Speaking speed. Defaults to 5.
            oral (int, optional): Oral level.
            laugh (int, optional): Laugh level.
            break_val (int, optional): Break level.
            temperature (float, optional): Sampling temperature.
            generate_subtitles (bool, optional): Whether to generate subtitles. Defaults to True.
            **kwargs: Additional arguments for chat.infer().

        Returns:
            Dict[str, Any]: A dictionary containing the audio array and other info.
        """
        if not self.model_loaded:
            raise RuntimeError("ChatTTS model not loaded. Call load_model() first.")

        try:
            # If no speaker is provided, sample a random one
            if speaker is None:
                speaker = self.chat.sample_random_speaker()

            # 使用参数类而不是字典
            params_refine_text = TextParams(f'[oral_{oral}][laugh_{laugh}][break_{break_val}]')
            params_infer_code = InferCodeParams(
                prompt=f'[speed_{speed}]',
                spk_emb=speaker
            )
            params_infer_code.temperature = temperature

            # chat.infer returns a list of audio arrays
            wavs = self.chat.infer([text], params_refine_text=params_refine_text, params_infer_code=params_infer_code, **kwargs)
            
            # Extract the first audio array
            audio_array = wavs[0]

            # 生成字幕数据
            subtitles = None
            if generate_subtitles:
                subtitles = self._generate_subtitles(text, len(audio_array) / SAMPLE_RATE)

            return {
                "audio": audio_array,
                "sample_rate": SAMPLE_RATE,  # 使用固定的采样率
                "text": text,
                "speaker_embedding": speaker,
                "subtitles": subtitles  # 添加字幕数据
            }
        except Exception as e:
            self.logger.error(f"Error generating speech: {e}")
            raise

    def _generate_subtitles(self, text: str, duration: float) -> List[Dict[str, Any]]:
        """
        生成简单的字幕数据

        Args:
            text (str): 语音文本
            duration (float): 音频时长（秒）

        Returns:
            List[Dict[str, Any]]: 字幕数据列表，每项包含开始时间、结束时间和文本
        """
        # 简单的字幕生成算法：按句子或标点符号分割文本
        import re
        
        # 分割句子
        sentences = re.split(r'([.!?。！？])', text)
        sentences = [''.join(i) for i in zip(sentences[0::2], sentences[1::2] + [''] * (len(sentences) % 2))]
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            sentences = [text]
            
        # 计算每个句子的大致时长
        total_chars = sum(len(s) for s in sentences)
        char_duration = duration / total_chars if total_chars > 0 else duration
        
        subtitles = []
        current_time = 0
        
        for sentence in sentences:
            if not sentence:
                continue
                
            # 估算句子时长
            sentence_duration = len(sentence) * char_duration
            
            # 添加字幕条目
            subtitles.append({
                "start": current_time,
                "end": current_time + sentence_duration,
                "text": sentence
            })
            
            current_time += sentence_duration
            
        return subtitles

    def save_audio(self, audio_data: np.ndarray, output_path: str, sample_rate: int = SAMPLE_RATE):
        """
        Saves the generated audio to a file.

        Args:
            audio_data (np.ndarray): The audio data.
            output_path (str): The path to save the audio file.
            sample_rate (int): The sample rate of the audio.
        """
        try:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            write_wav(output_path, sample_rate, audio_data)
            self.logger.info(f"Audio saved to {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving audio: {e}")
            raise 