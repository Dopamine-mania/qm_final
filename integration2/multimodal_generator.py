import os
import logging
import torch
import sys
from typing import Dict, Any, Optional
import numpy as np

# Try different imports for moviepy
try:
    from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip
except ImportError:
    try:
        # Alternative import paths
        from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
        from moviepy.audio.AudioClip import CompositeAudioClip
        # Create a custom ImageClip using PIL and ImageSequenceClip
        from PIL import Image
        def ImageClip(image_path, duration=None):
            img = Image.open(image_path)
            return ImageSequenceClip([np.array(img)], fps=1, durations=[duration])
    except ImportError:
        # Fallback to a minimal implementation using only basic libraries
        logging.warning("MoviePy not fully available. Video creation may be limited.")
        ImageClip = None
        AudioFileClip = None
        CompositeAudioClip = None

# 打印 Python 路径以进行调试
python_paths = sys.path
print("Python sys.path:")
for path in python_paths:
    print(f"  - {path}")

# Check if moviepy is installed and show version
try:
    import moviepy
    print(f"moviepy is installed at: {moviepy.__file__}")
    print(f"moviepy version: {moviepy.__version__}")
except ImportError:
    print("Error: moviepy is not installed")
except Exception as e:
    print(f"Error importing moviepy: {str(e)}")

from PIL import Image

# --- Path Setup ---
# Add project root to sys.path to allow for absolute imports from TTI, TTM, TTS
# This makes the script runnable from anywhere
try:
    # This assumes the script is in qm_final/integration2
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except NameError:
    # Fallback for interactive environments
    project_root = os.path.abspath('.')
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from TTI.base_image_generator import BaseImageGenerator
from TTS.base_speech_generator import BaseSpeechGenerator
from TTM.base_music_generator import BaseMusicGenerator

class MultimodalVideoGenerator:
    def __init__(
        self,
        image_gen: BaseImageGenerator,
        speech_gen: BaseSpeechGenerator,
        music_gen: BaseMusicGenerator
    ):
        """
        Initializes the multimodal video generator using dependency injection.

        Args:
            image_gen (BaseImageGenerator): An instantiated image generator object.
            speech_gen (BaseSpeechGenerator): An instantiated speech generator object.
            music_gen (BaseMusicGenerator): An instantiated music generator object.
        """
        self.logger = logging.getLogger(__name__)
        
        # Store the injected generator instances
        self.image_generator = image_gen
        self.speech_generator = speech_gen
        self.music_generator = music_gen
        
        self.output_dir = "output_video"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def load_all_models(self):
        """
        Loads all necessary models using the injected generators.
        """
        self.logger.info("--- Loading all models via injected generators ---")
        try:
            self.image_generator.load_model()
            self.speech_generator.load_model()
            self.music_generator.load_model()
            self.logger.info("--- All models loaded successfully ---")
        except Exception as e:
            self.logger.error(f"An error occurred while loading models: {e}", exc_info=True)
            raise

    def generate_and_synthesize(
        self,
        image_prompt: str,
        speech_prompt: str,
        music_prompt: str,
        output_filename: str = "final_video.mp4",
        video_duration: int = 10,
        image_params: dict = None,
        speech_params: dict = None,
        music_params: dict = None
    ) -> str:
        """
        Generates image, speech, and music, then synthesizes them into a single video.

        Args:
            image_prompt (str): Prompt for the image generation.
            speech_prompt (str): Text for the speech generation.
            music_prompt (str): Prompt for the music generation.
            output_filename (str): Name of the output video file.
            video_duration (int): Desired duration of the video in seconds.
            image_params (dict, optional): Parameters for ImageGenerator.
            speech_params (dict, optional): Parameters for SpeechGenerator.
            music_params (dict, optional): Parameters for MusicGenerator.

        Returns:
            str: The path to the generated video file.
        """
        image_params = image_params or {}
        speech_params = speech_params or {}
        music_params = music_params or {}
        
        # Create unique temp filenames based on output_filename
        base_name = os.path.splitext(output_filename)[0]
        temp_files = []
        try:
            # 1. Generate Image
            self.logger.info(f"Generating image with prompt: '{image_prompt}'")
            img_result = self.image_generator.generate_image(prompt=image_prompt, **image_params)
            image = img_result["images"][0]
            image_path = os.path.join(self.output_dir, f"{base_name}_image.png")
            self.image_generator.save_image(image, image_path)
            temp_files.append(image_path)

            # 2. Generate Speech
            self.logger.info(f"Generating speech for text: '{speech_prompt}'")
            speech_result = self.speech_generator.generate_speech(text=speech_prompt, **speech_params)
            speech_audio = speech_result["audio"]
            speech_sr = speech_result["sample_rate"]
            speech_path = os.path.join(self.output_dir, f"{base_name}_speech.wav")
            self.speech_generator.save_audio(speech_audio, speech_path, speech_sr)
            temp_files.append(speech_path)

            # 3. Generate Music
            self.logger.info(f"Generating music with prompt: '{music_prompt}'")
            self.logger.info(f"Music will be saved as: {base_name}_music.wav")
            music_params.setdefault('duration_secs', video_duration)
            music_result = self.music_generator.generate_music(prompt=music_prompt, **music_params)
            music_audio = music_result["audio"]
            music_sr = music_result["sample_rate"]
            music_path = os.path.join(self.output_dir, f"{base_name}_music.wav")
            self.music_generator.save_audio(music_audio, music_path, music_sr)
            temp_files.append(music_path)
            
            # 4. Verify file independence
            self.logger.info("Verifying file independence...")
            self.logger.info(f"Image file: {image_path}")
            self.logger.info(f"Speech file: {speech_path}")
            self.logger.info(f"Music file: {music_path}")
            
            # Ensure the files exist and belong to the current scene
            for file_path in [image_path, speech_path, music_path]:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Required file not found: {file_path}")
                if base_name not in file_path:
                    raise ValueError(f"File {file_path} does not belong to the current scene ({base_name})")
            
            # 5. Synthesize Video
            self.logger.info("Synthesizing video from generated content...")
            video_path = self._create_video(
                image_path, speech_path, music_path, 
                os.path.join(self.output_dir, output_filename), 
                duration=video_duration
            )
            self.logger.info(f"Successfully created video at: {video_path}")
            
            return video_path

        except Exception as e:
            self.logger.error(f"An error occurred during generation or synthesis: {e}", exc_info=True)
            raise
        finally:
            # Don't clean up temp files anymore since we want to keep them for ffmpeg fallback
            pass

    def _create_video(
        self,
        image_path: str,
        speech_path: str,
        music_path: str,
        output_path: str,
        duration: Optional[float] = None,
        fade_duration: float = 1.0,
        music_volume: float = 0.3
    ) -> str:
        """
        Creates a video from an image and audio files.

        Args:
            image_path (str): Path to the image file
            speech_path (str): Path to the speech audio file
            music_path (str): Path to the music audio file
            output_path (str): Path where the video should be saved
            duration (Optional[float]): Duration of the video in seconds. If None, uses speech duration.
            fade_duration (float): Duration of audio fade in/out in seconds
            music_volume (float): Volume of the background music (0.0 to 1.0)

        Returns:
            str: Path to the created video file
        """
        try:
            # Load audio files
            speech_audio = AudioFileClip(speech_path)
            music_audio = AudioFileClip(music_path)
            
            # Set music volume
            music_audio = music_audio.set_volume(music_volume)
            
            # If duration not specified, use speech duration
            if duration is None:
                duration = speech_audio.duration
            
            # Create image clip with duration
            image_clip = ImageClip(image_path, duration=duration)
            
            # Adjust music length
            if music_audio.duration < duration:
                # Calculate how many times we need to loop the music
                repeats = int(duration / music_audio.duration) + 1
                # Create a list of music clips
                music_clips = [music_audio] * repeats
                # Concatenate them
                from moviepy.editor import concatenate_audioclips
                music_audio = concatenate_audioclips(music_clips)
            
            # Trim music to exact duration
            music_audio = music_audio.set_duration(duration)
            
            # Add fade effects to music
            music_audio = music_audio.audio_fadein(fade_duration).audio_fadeout(fade_duration)
            
            # Combine audio tracks
            final_audio = CompositeAudioClip([speech_audio, music_audio])
            
            # Set audio to video
            final_video = image_clip.set_audio(final_audio)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write video file
            final_video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac'
            )
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to create video: {str(e)}")
            
            # Fallback: Use ffmpeg directly
            try:
                import subprocess
                
                # Create output directory
                output_dir = os.path.dirname(output_path)
                os.makedirs(output_dir, exist_ok=True)
                
                # First merge the audio files
                merged_audio = os.path.join(output_dir, "temp_merged_audio.wav")
                subprocess.run([
                    "ffmpeg", "-y",
                    "-i", speech_path,
                    "-i", music_path,
                    "-filter_complex", "[1:a]volume=0.3[a1];[0:a][a1]amix=inputs=2:duration=longest",
                    merged_audio
                ], check=True)
                
                # Then create the video
                subprocess.run([
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", image_path,
                    "-i", merged_audio,
                    "-c:v", "libx264",
                    "-tune", "stillimage",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-shortest",
                    output_path
                ], check=True)
                
                # Clean up temporary audio file
                if os.path.exists(merged_audio):
                    os.remove(merged_audio)
                
                return output_path
                
            except Exception as e:
                self.logger.error(f"Failed to create video with ffmpeg: {str(e)}")
                # Return the directory containing the individual files
                return os.path.dirname(output_path)
        finally:
            # Clean up any temporary files
            if os.path.exists('temp-audio.m4a'):
                try:
                    os.remove('temp-audio.m4a')
                except:
                    pass 