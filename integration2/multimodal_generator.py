import os
import logging
import torch
import sys
from typing import Dict, Any, Optional, List
import numpy as np

# Try different imports for moviepy
try:
    from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip, TextClip, CompositeVideoClip, concatenate_videoclips
except ImportError:
    try:
        # Alternative import paths
        from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
        from moviepy.audio.AudioClip import CompositeAudioClip
        from moviepy.video.VideoClip import TextClip
        from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
        from moviepy.video.compositing.concatenate import concatenate_videoclips
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
        TextClip = None
        CompositeVideoClip = None
        concatenate_videoclips = None

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
    # 添加TTS目录到路径
    tts_path = os.path.join(project_root, 'TTS')
    if tts_path not in sys.path:
        sys.path.insert(0, tts_path)
except NameError:
    # Fallback for interactive environments
    project_root = os.path.abspath('.')
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    # 添加TTS目录到路径
    tts_path = os.path.join(project_root, 'TTS')
    if tts_path not in sys.path:
        sys.path.insert(0, tts_path)

from TTI.base_image_generator import BaseImageGenerator
from base_speech_generator import BaseSpeechGenerator
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
        video_duration: int = 45,  # 默认45秒
        image_params: dict = None,
        speech_params: dict = None,
        music_params: dict = None,
        num_images: int = 9,  # 默认生成9张图片
        enable_subtitles: bool = True,  # 启用字幕
        speech_text: str = None  # 字幕文本
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
            num_images (int): Number of images to generate for the slideshow.
            enable_subtitles (bool): Whether to add subtitles to the video.
            speech_text (str, optional): Text for subtitles, defaults to speech_prompt if None.

        Returns:
            str: The path to the generated video file.
        """
        image_params = image_params or {}
        speech_params = speech_params or {}
        music_params = music_params or {}
        
        # 如果没有提供字幕文本，使用语音文本
        if speech_text is None:
            speech_text = speech_prompt
        
        # Create unique temp filenames based on output_filename
        base_name = os.path.splitext(output_filename)[0]
        temp_files = []
        try:
            # 1. Generate Multiple Images
            self.logger.info(f"Generating {num_images} images with prompt: '{image_prompt}'")
            image_paths = []
            
            # 为每张图片添加更多样化的变化
            style_variations = [
                "in a realistic style",
                "in an artistic style",
                "with dramatic lighting",
                "in a cinematic view",
                "with soft lighting",
                "from a different perspective",
                "with detailed textures",
                "in a minimalist style",
                "with vibrant colors"
            ]
            
            for i in range(num_images):
                # 组合原始提示词和风格变化
                style = style_variations[i % len(style_variations)]
                varied_prompt = f"{image_prompt}, {style}, unique variation {i+1}"
                img_result = self.image_generator.generate_image(prompt=varied_prompt, **image_params)
                image = img_result["images"][0]
                image_path = os.path.join(self.output_dir, f"{base_name}_image_{i+1}.png")
                self.image_generator.save_image(image, image_path)
                image_paths.append(image_path)
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
            self.logger.info(f"Image files: {len(image_paths)} images generated")
            self.logger.info(f"Speech file: {speech_path}")
            self.logger.info(f"Music file: {music_path}")
            
            # Ensure the files exist
            for file_path in image_paths + [speech_path, music_path]:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Required file not found: {file_path}")
            
            # 5. Synthesize Video
            self.logger.info("Synthesizing video from generated content...")
            video_path = self._create_slideshow_video(
                image_paths, speech_path, music_path, 
                os.path.join(self.output_dir, output_filename), 
                duration=video_duration,
                speech_text=speech_text if enable_subtitles else None
            )
            self.logger.info(f"Successfully created video at: {video_path}")
            
            return video_path

        except Exception as e:
            self.logger.error(f"An error occurred during generation or synthesis: {e}", exc_info=True)
            raise
        finally:
            # Don't clean up temp files anymore since we want to keep them for ffmpeg fallback
            pass

    def _create_slideshow_video(
        self,
        image_paths: List[str],
        speech_path: str,
        music_path: str,
        output_path: str,
        duration: Optional[float] = None,
        fade_duration: float = 1.0,
        music_volume: float = 0.3,
        speech_text: Optional[str] = None
    ) -> str:
        """
        Creates a video from images with audio and optional subtitles.
        
        Args:
            image_paths: List of paths to images
            speech_path: Path to speech audio file
            music_path: Path to background music file
            output_path: Path for output video
            duration: Total video duration (optional)
            fade_duration: Duration of fade transition between images
            music_volume: Volume of background music (0.0-1.0)
            speech_text: Text for subtitles (optional)
        """
        try:
            # Load audio clips
            speech_clip = AudioFileClip(speech_path)
            music_clip = AudioFileClip(music_path)
            
            # Calculate durations
            total_duration = max(speech_clip.duration, music_clip.duration)
            if duration:
                total_duration = duration
                
            # Extend music if needed with crossfade
            if music_clip.duration < total_duration:
                num_loops = int(np.ceil(total_duration / music_clip.duration))
                music_clips = [music_clip]
                for i in range(1, num_loops):
                    start_time = i * music_clip.duration - fade_duration
                    music_clips.append(music_clip.set_start(start_time))
                music_clip = CompositeAudioClip(music_clips)
            
            # Create image clips with transitions
            image_duration = total_duration / len(image_paths)
            image_clips = []
            
            for i, img_path in enumerate(image_paths):
                start_time = i * image_duration
                clip = (ImageClip(img_path)
                       .set_duration(image_duration + fade_duration)
                       .set_start(start_time)
                       .crossfadein(fade_duration)
                       .crossfadeout(fade_duration))
                image_clips.append(clip)
            
            # Create video from image clips
            video = CompositeVideoClip(image_clips, size=(1024, 1024))
            
            # Add subtitles if text is provided
            if speech_text and TextClip is not None:
                # Split text into segments based on duration
                words = speech_text.split()
                words_per_segment = max(1, len(words) // int(total_duration / 3))  # Show ~3 seconds per segment
                segments = [' '.join(words[i:i+words_per_segment]) 
                          for i in range(0, len(words), words_per_segment)]
                
                subtitle_clips = []
                segment_duration = total_duration / len(segments)
                
                for i, text in enumerate(segments):
                    start_time = i * segment_duration
                    try:
                        txt_clip = (TextClip(text, fontsize=30, color='white', stroke_color='black',
                                          stroke_width=2, font='Arial', size=(video.w, None),
                                          method='caption')
                                  .set_position(('center', 'bottom'))
                                  .set_duration(segment_duration)
                                  .set_start(start_time)
                                  .crossfadein(0.5)
                                  .crossfadeout(0.5))
                        subtitle_clips.append(txt_clip)
                    except Exception as e:
                        self.logger.warning(f"Error creating subtitle clip: {str(e)}")
                        continue
                
                # Add subtitles to video if any were created successfully
                if subtitle_clips:
                    video = CompositeVideoClip([video] + subtitle_clips)
            
            # Combine audio tracks
            music_clip = music_clip.volumex(music_volume)
            final_audio = CompositeAudioClip([music_clip, speech_clip])
            
            # Set audio to video with smooth fadeout
            video = video.set_audio(final_audio)
            
            # Add final fadeout to both video and audio
            video = video.fadeout(2.0)
            
            # Write final video
            video.write_videofile(output_path, fps=24, codec='libx264', 
                                audio_codec='aac', preset='medium')
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error in video creation: {str(e)}", exc_info=True)
            raise
        finally:
            # Clean up moviepy clips
            try:
                if 'video' in locals(): 
                    video.close()
                if 'speech_clip' in locals(): 
                    speech_clip.close()
                if 'music_clip' in locals(): 
                    music_clip.close()
            except Exception as e:
                self.logger.warning(f"Error during cleanup: {str(e)}") 