import torch
import logging
import os
import sys
import numpy as np
from typing import Optional, Dict, Any
from scipy.io.wavfile import write as write_wav
from TTS.base_speech_generator import BaseSpeechGenerator

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

            params_refine_text = {
                'prompt': f'[oral_{oral}][laugh_{laugh}][break_{break_val}]'
            }
            params_infer_code = {
                'prompt': f'[speed_{speed}]',
                'spk_emb': speaker,
                'temperature': temperature
            }

            # chat.infer returns a list of audio arrays
            wavs = self.chat.infer([text], params_refine_text=params_refine_text, params_infer_code=params_infer_code, **kwargs)
            
            # Extract the first audio array
            audio_array = wavs[0]

            return {
                "audio": audio_array,
                "sample_rate": self.chat.sample_rate,
                "text": text,
                "speaker_embedding": speaker
            }
        except Exception as e:
            self.logger.error(f"Error generating speech: {e}")
            raise

    def save_audio(self, audio_data: np.ndarray, output_path: str, sample_rate: int = 24000):
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