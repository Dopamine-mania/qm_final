from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseMusicGenerator(ABC):
    """
    Abstract base class for music generators.
    Defines the common interface that all music generators must implement.
    """

    @abstractmethod
    def load_model(self, **kwargs) -> None:
        """
        Load the music generation model into memory.
        """
        pass

    @abstractmethod
    def generate_music(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate music from a given prompt.

        Args:
            prompt (str): The text prompt to guide music generation.
            **kwargs: Model-specific parameters.

        Returns:
            Dict[str, Any]: A dictionary containing at least 'audio' (the audio data as a numpy array)
                            and 'sample_rate' (the sample rate of the audio).
        """
        pass

    @abstractmethod
    def save_audio(self, audio_data: Any, output_path: str, sample_rate: int) -> None:
        """
        Save the audio data to a file.

        Args:
            audio_data (Any): The audio data to save.
            output_path (str): The path to save the file.
            sample_rate (int): The sample rate of the audio.
        """
        pass 