from abc import ABC, abstractmethod
from typing import Dict, Any
from PIL import Image

class BaseImageGenerator(ABC):
    """
    Abstract base class for image generators.
    Defines the common interface that all image generators must implement.
    """

    @abstractmethod
    def load_model(self, **kwargs) -> None:
        """
        Load the image generation model into memory.
        """
        pass

    @abstractmethod
    def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate an image from a given prompt.

        Args:
            prompt (str): The text prompt to guide image generation.
            **kwargs: Model-specific parameters.

        Returns:
            Dict[str, Any]: A dictionary containing at least 'images' (a list of PIL.Image objects).
        """
        pass

    @abstractmethod
    def save_image(self, image: Image.Image, output_path: str) -> None:
        """
        Save the image to a file.

        Args:
            image (Image.Image): The PIL Image object to save.
            output_path (str): The path to save the file.
        """
        pass 