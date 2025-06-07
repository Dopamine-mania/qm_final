import torch
import logging
import os
import sys
import scipy.io.wavfile
import numpy as np
from typing import Dict, Any, Optional
from TTM.base_music_generator import BaseMusicGenerator

# --- Path Setup ---
# Add the 'oher' directory to the path to find the 'acestep' module
try:
    oher_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'oher'))
    if oher_path not in sys.path:
        sys.path.insert(0, oher_path)
    from acestep.pipeline_ace_step import ACEStepPipeline
except ImportError as e:
    print(f"Error: Could not import ACEStepPipeline. Make sure the 'acestep' module is in 'qm_final/TTM/oher/'. Details: {e}")
    sys.exit(1)

class MusicGenerator(BaseMusicGenerator):
    def __init__(self, checkpoint_path: Optional[str] = None):
        """
        Initializes the Music Generator using the ACEStep pipeline.

        Args:
            checkpoint_path (Optional[str], optional): Path to a local ACEStep model checkpoint directory.
                                                      If None, the model will be downloaded to a default cache directory.
                                                      Defaults to None.
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.checkpoint_path = checkpoint_path
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dtype = "bfloat16" if self.device == "cuda" else "float32"

    def load_model(self):
        """
        Loads the ACEStep model pipeline from the specified path or downloads it.
        """
        if self.pipeline is not None:
            self.logger.info("ACEStep model is already loaded.")
            return

        # If a path is provided, check if it's valid
        if self.checkpoint_path and not os.path.isdir(self.checkpoint_path):
            self.logger.error(f"Provided checkpoint path not found or not a directory: {self.checkpoint_path}")
            raise FileNotFoundError(f"ACEStep checkpoint directory not found at {self.checkpoint_path}")

        try:
            if self.checkpoint_path:
                self.logger.info(f"Loading ACEStep pipeline from local path: {self.checkpoint_path}")
            else:
                self.logger.info("No checkpoint path provided. ACEStep will attempt to download the model to its default cache directory.")

            self.pipeline = ACEStepPipeline(
                checkpoint_dir=self.checkpoint_path, # This can be None
                dtype=self.dtype,
                torch_compile=False,
            )
            self.logger.info("ACEStep pipeline loaded successfully.")
        except Exception as e:
            self.logger.error(f"Error loading ACEStep pipeline: {e}", exc_info=True)
            raise

    def generate_music(
        self,
        prompt: str,
        duration_secs: int = 10,
        lyrics: str = "",
        infer_step: int = 100,
        guidance_scale: float = 3.5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generates music using the ACEStep pipeline.

        Args:
            prompt (str): The text prompt (tags, description).
            duration_secs (int): Desired duration in seconds.
            lyrics (str): Lyrics for the music. Defaults to "".
            infer_step (int): Number of inference steps.
            guidance_scale (float): Guidance scale.
            **kwargs: Additional parameters for the pipeline.

        Returns:
            Dict[str, Any]: Dictionary with audio array and sample rate.
        """
        if self.pipeline is None:
            raise RuntimeError("ACEStep model not loaded. Call load_model() first.")

        try:
            # ACEStepPipeline returns the saved file path directly.
            # We need to run it, then load the audio back to return the array.
            temp_output_filename = os.path.join(os.path.dirname(__file__), "temp_acestep_output.wav")

            # Default ACEStep parameters from the infer-api.py
            # These can be overridden by kwargs.
            params = {
                'audio_duration': float(duration_secs),
                'prompt': prompt,
                'lyrics': lyrics,
                'infer_step': infer_step,
                'guidance_scale': guidance_scale,
                'scheduler_type': 'dpm++',
                'cfg_type': 'self-attention-v',
                'omega_scale': 0.7,
                'actual_seeds': "0",
                'guidance_interval': 0.98,
                'guidance_interval_decay': 1.0,
                'min_guidance_scale': 1.0,
                'use_erg_tag': True,
                'use_erg_lyric': True,
                'use_erg_diffusion': True,
                'oss_steps': "20",
                'guidance_scale_text': 0.0,
                'guidance_scale_lyric': 0.0,
                'save_path': temp_output_filename
            }
            params.update(kwargs)

            self.logger.info(f"Running ACEStep pipeline with prompt: '{prompt}'")
            self.pipeline(**params)

            if not os.path.exists(temp_output_filename):
                 raise FileNotFoundError("ACEStep pipeline ran but did not produce an output file.")

            # Load the generated audio file
            sample_rate, audio_array = scipy.io.wavfile.read(temp_output_filename)
            
            # Clean up the temporary file
            os.remove(temp_output_filename)

            return {
                "audio": audio_array,
                "sample_rate": sample_rate,
                "prompt": prompt
            }
        except Exception as e:
            self.logger.error(f"Error during ACEStep music generation: {e}", exc_info=True)
            raise

    def save_audio(self, audio_data: np.ndarray, output_path: str, sample_rate: int):
        """
        Saves the generated audio to a file.

        Args:
            audio_data (np.ndarray): The audio data array.
            output_path (str): The path to save the audio file.
            sample_rate (int): The sample rate of the audio.
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            scipy.io.wavfile.write(output_path, rate=sample_rate, data=audio_data)
            self.logger.info(f"ACEStep music saved to {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving ACEStep music: {e}", exc_info=True)
            raise 