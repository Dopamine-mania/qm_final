import os
import logging
import torch
import sys
from typing import Dict, Any, Optional, List
import numpy as np

# 确保moviepy正确导入
try:
    from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, TextClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Error importing moviepy: {e}")
    MOVIEPY_AVAILABLE = False
    VideoFileClip = ImageClip = AudioFileClip = CompositeVideoClip = CompositeAudioClip = TextClip = concatenate_videoclips = None

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
        
        # 检查moviepy是否可用
        if not MOVIEPY_AVAILABLE:
            self.logger.warning("MoviePy is not available. Video creation will be limited to ffmpeg fallback.")
        
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
        
        # 记录字幕状态
        if enable_subtitles:
            self.logger.info(f"Subtitles enabled with text: {speech_text[:50]}...")
        else:
            self.logger.info("Subtitles disabled")
            speech_text = None
        
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
            
            # 5. Synthesize the video
            self.logger.info("Synthesizing video from generated content...")
            try:
                video_path = self._create_slideshow_video(
                    image_paths=image_paths,
                    speech_path=speech_path,
                    music_path=music_path,
                    output_path=os.path.join(self.output_dir, output_filename), 
                    duration=video_duration,
                    speech_text=speech_text
                )
                self.logger.info(f"Successfully created video at: {video_path}")
                return video_path
            except Exception as e:
                self.logger.error(f"An error occurred during video synthesis: {e}")
                raise
                
        except Exception as e:
            self.logger.error(f"An error occurred during generation or synthesis: {str(e)}")
            raise
        finally:
            # Optionally clean up temp files
            # for file_path in temp_files:
            #     if os.path.exists(file_path):
            #         os.remove(file_path)
            pass

    def _create_slideshow_video_ffmpeg(
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
        使用ffmpeg创建视频的回退方案，包含字幕支持
        """
        try:
            import subprocess
            import tempfile
            import platform
            
            # 创建输出目录
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # 根据操作系统选择合适的中文字体
            if platform.system() == 'Windows':
                font_name = 'Microsoft YaHei'  # Windows的中文字体
            elif platform.system() == 'Darwin':
                font_name = 'PingFang SC'  # macOS的中文字体
            else:
                # Linux系统，尝试常见的中文字体
                available_fonts = [
                    'Noto Sans CJK SC',
                    'WenQuanYi Micro Hei',
                    'Source Han Sans CN',
                    'DroidSansFallback',
                ]
                font_name = 'Noto Sans CJK SC'  # 默认使用Noto字体
                
                # 检查字体是否存在
                try:
                    font_check = subprocess.run(
                        ['fc-list', ':lang=zh'],
                        capture_output=True,
                        text=True
                    )
                    for font in available_fonts:
                        if font.lower() in font_check.stdout.lower():
                            font_name = font
                            break
                except Exception as e:
                    self.logger.warning(f"Unable to check fonts: {e}")
            
            # 首先合并音频文件
            merged_audio = os.path.join(output_dir, "temp_merged_audio.wav")
            subprocess.run([
                "ffmpeg", "-y",
                "-i", speech_path,
                "-i", music_path,
                "-filter_complex", f"[1:a]volume={music_volume}[a1];[0:a][a1]amix=inputs=2:duration=longest",
                merged_audio
            ], check=True)
            
            # 计算每张图片的持续时间
            if duration is None:
                # 使用音频文件的长度作为视频长度
                result = subprocess.run([
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", merged_audio
                ], capture_output=True, text=True)
                duration = float(result.stdout.strip())
            
            image_duration = duration / len(image_paths)
            
            # 创建一个临时文件列表
            images_list_file = os.path.join(output_dir, "temp_images_list.txt")
            with open(images_list_file, 'w', encoding='utf-8') as f:
                for img_path in image_paths:
                    f.write(f"file '{img_path}'\n")
                    f.write(f"duration {image_duration}\n")
                # 添加最后一张图片再一次，防止视频末尾黑屏
                f.write(f"file '{image_paths[-1]}'\n")
                f.write(f"duration 0.5\n")
            
            # 创建ASS字幕文件（如果提供了文本）
            subtitle_file = None
            if speech_text:
                subtitle_file = os.path.join(output_dir, "temp_subtitles.ass")
                self._create_ass_subtitles(speech_text, subtitle_file, duration, font_name)
            
            # 基本ffmpeg命令
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", images_list_file,
                "-i", merged_audio
            ]
            
            # 添加字幕（如果有）
            if subtitle_file:
                ffmpeg_cmd.extend([
                    "-vf", f"ass={subtitle_file}"
                ])
            else:
                # 只添加淡入淡出效果
                ffmpeg_cmd.extend([
                    "-vf", f"fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1"
                ])
            
            # 添加其他参数
            ffmpeg_cmd.extend([
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-shortest",
                "-af", f"afade=t=in:st=0:d=1,afade=t=out:st={duration-1}:d=1",
                output_path
            ])
            
            # 执行ffmpeg命令
            subprocess.run(ffmpeg_cmd, check=True)
            
            # 清理临时文件
            os.remove(images_list_file)
            os.remove(merged_audio)
            if subtitle_file:
                os.remove(subtitle_file)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error in ffmpeg video creation: {str(e)}")
            raise

    def _create_ass_subtitles(self, text: str, output_file: str, duration: float, font_name: str):
        """
        创建ASS格式的字幕文件，支持中文
        """
        try:
            # 将文本分成几个部分
            words = text.split()
            # 每段显示约5秒，计算每段应该有多少单词
            segments_count = max(1, int(duration / 5))
            words_per_segment = max(1, len(words) // segments_count)
            
            segments = []
            for i in range(0, len(words), words_per_segment):
                end_idx = min(i + words_per_segment, len(words))
                segments.append(" ".join(words[i:end_idx]))
            
            # 计算每段的时间
            segment_duration = duration / len(segments)
            
            # 写入ASS文件头
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("[Script Info]\n")
                f.write("ScriptType: v4.00+\n")
                f.write("PlayResX: 1024\n")
                f.write("PlayResY: 1024\n")
                f.write("Collisions: Normal\n\n")
                
                f.write("[V4+ Styles]\n")
                f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                f.write(f"Style: Default,{font_name},36,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,2,20,20,50,1\n\n")
                
                f.write("[Events]\n")
                f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                
                # 写入字幕事件
                for i, segment in enumerate(segments):
                    start_time = i * segment_duration
                    end_time = (i + 1) * segment_duration
                    
                    # 格式化时间为ASS格式 (H:MM:SS.cc)
                    start_formatted = self._format_ass_time(start_time)
                    end_formatted = self._format_ass_time(end_time)
                    
                    # 添加淡入淡出效果
                    text_with_fx = "{\\fad(500,500)}" + segment
                    
                    # 写入字幕条目
                    f.write(f"Dialogue: 0,{start_formatted},{end_formatted},Default,,0,0,0,,{text_with_fx}\n")
                    
        except Exception as e:
            self.logger.error(f"Error creating ASS subtitles: {str(e)}")
            raise
    
    def _format_ass_time(self, seconds: float) -> str:
        """
        将秒数格式化为ASS时间格式 (H:MM:SS.cc)
        """
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        seconds_part = seconds % 60
        centiseconds = int((seconds_part - int(seconds_part)) * 100)
        return f"{hours}:{minutes:02d}:{int(seconds_part):02d}.{centiseconds:02d}"

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
        """
        # 如果moviepy不可用，使用ffmpeg回退方案
        if not MOVIEPY_AVAILABLE:
            self.logger.info("Using ffmpeg fallback for video creation...")
            return self._create_slideshow_video_ffmpeg(
                image_paths=image_paths,
                speech_path=speech_path,
                music_path=music_path,
                output_path=output_path,
                duration=duration,
                fade_duration=fade_duration,
                music_volume=music_volume,
                speech_text=speech_text
            )
            
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
            
            # 添加最后一帧作为结束帧，防止黑屏
            final_clip = (ImageClip(image_paths[-1])
                         .set_duration(2.0)
                         .set_start(total_duration - 2.0))
            image_clips.append(final_clip)
            
            # Create video from image clips
            video = CompositeVideoClip(image_clips, size=(1024, 1024))
            
            # Add subtitles if text is provided and TextClip is available
            if speech_text and TextClip is not None:
                try:
                    # Split text into segments based on duration
                    words = speech_text.split()
                    words_per_segment = max(1, len(words) // int(total_duration / 5))  # 每5秒一段字幕
                    segments = [' '.join(words[i:i+words_per_segment]) 
                              for i in range(0, len(words), words_per_segment)]
                    
                    subtitle_clips = []
                    segment_duration = total_duration / len(segments)
                    
                    for i, text in enumerate(segments):
                        start_time = i * segment_duration
                        try:
                            # 使用更明显的字幕样式
                            txt_clip = (TextClip(text, 
                                              fontsize=36,  # 增大字号
                                              color='white', 
                                              stroke_color='black',
                                              stroke_width=2, 
                                              font='Arial-Bold',  # 使用粗体
                                              size=(video.w * 0.9, None),  # 宽度为视频宽度的90%
                                              method='caption',
                                              align='center')
                                      .set_position(('center', 'bottom'))
                                      .margin(bottom=50, opacity=0)  # 底部边距
                                      .set_duration(segment_duration)
                                      .set_start(start_time)
                                      .crossfadein(0.5)
                                      .crossfadeout(0.5))
                            subtitle_clips.append(txt_clip)
                            self.logger.info(f"Added subtitle at {start_time}s: {text[:30]}...")
                        except Exception as e:
                            self.logger.warning(f"Error creating subtitle clip: {str(e)}")
                            continue
                    
                    # Add subtitles to video if any were created successfully
                    if subtitle_clips:
                        self.logger.info(f"Adding {len(subtitle_clips)} subtitle clips to video")
                        video = CompositeVideoClip([video] + subtitle_clips)
                    else:
                        self.logger.warning("No subtitle clips were created successfully")
                except Exception as e:
                    self.logger.warning(f"Error adding subtitles: {str(e)}")
            
            # Combine audio tracks
            music_clip = music_clip.volumex(music_volume)
            final_audio = CompositeAudioClip([music_clip, speech_clip])
            
            # Set audio to video with smooth fadeout
            video = video.set_audio(final_audio)
            
            # Add final fadeout to both video and audio
            video = video.fadeout(2.0)
            
            # Write final video
            self.logger.info("Writing video file with moviepy...")
            video.write_videofile(output_path, fps=24, codec='libx264', 
                                audio_codec='aac', preset='medium')
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error in moviepy video creation: {str(e)}", exc_info=True)
            # 如果moviepy失败，尝试使用ffmpeg回退方案
            self.logger.info("Falling back to ffmpeg for video creation...")
            return self._create_slideshow_video_ffmpeg(
                image_paths=image_paths,
                speech_path=speech_path,
                music_path=music_path,
                output_path=output_path,
                duration=duration,
                fade_duration=fade_duration,
                music_volume=music_volume,
                speech_text=speech_text
            )
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