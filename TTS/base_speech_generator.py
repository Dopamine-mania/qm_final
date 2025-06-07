from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseSpeechGenerator(ABC):
    """
    Abstract base class for speech generators.
    Defines the common interface that all speech generators must implement.
    """

    @abstractmethod
    def load_model(self, **kwargs) -> None:
        """
        Load the speech synthesis model into memory.
        """
        pass

    @abstractmethod
    def generate_speech(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Generate speech from the given text.

        Args:
            text (str): The text to be converted to speech.
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