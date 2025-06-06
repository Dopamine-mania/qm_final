import os
import logging
from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip, VideoFileClip
from typing import Dict, Optional

class VideoGenerator:
    def __init__(self, output_dir: str = "output"):
        """
        初始化视频生成器
        
        Args:
            output_dir: 输出目录
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = output_dir
        self.video_dir = os.path.join(output_dir, "videos")
        os.makedirs(self.video_dir, exist_ok=True)
        
    def create_video(
        self,
        image_path: str,
        speech_path: str,
        music_path: str,
        output_name: str,
        duration: Optional[float] = None,
        fade_duration: float = 1.0,
        music_volume: float = 0.3
    ) -> str:
        """
        创建视频
        
        Args:
            image_path: 图像文件路径
            speech_path: 语音文件路径
            music_path: 音乐文件路径
            output_name: 输出视频名称
            duration: 视频时长（秒），如果为None则使用语音时长
            fade_duration: 淡入淡出时长（秒）
            music_volume: 背景音乐音量（0-1）
            
        Returns:
            生成的视频文件路径
        """
        try:
            # 加载音频文件
            speech_audio = AudioFileClip(speech_path)
            music_audio = AudioFileClip(music_path).volumex(music_volume)
            
            # 如果未指定时长，使用语音时长
            if duration is None:
                duration = speech_audio.duration
                
            # 加载图像并设置时长
            image_clip = ImageClip(image_path).set_duration(duration)
            
            # 创建背景音乐（循环播放）
            if music_audio.duration < duration:
                music_audio = music_audio.loop(duration=duration)
            else:
                music_audio = music_audio.subclip(0, duration)
                
            # 添加淡入淡出效果
            music_audio = music_audio.audio_fadein(fade_duration).audio_fadeout(fade_duration)
            
            # 合并音频
            final_audio = CompositeAudioClip([speech_audio, music_audio])
            
            # 将音频添加到视频
            video = image_clip.set_audio(final_audio)
            
            # 生成输出路径
            output_path = os.path.join(self.video_dir, f"{output_name}.mp4")
            
            # 导出视频
            video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            self.logger.info(f"Video generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error creating video: {str(e)}")
            raise
        finally:
            # 清理临时文件
            if os.path.exists('temp-audio.m4a'):
                os.remove('temp-audio.m4a')
                
    def create_video_from_results(
        self,
        results: Dict[str, str],
        output_name: str,
        **kwargs
    ) -> str:
        """
        从生成结果创建视频
        
        Args:
            results: 包含生成文件路径的字典
            output_name: 输出视频名称
            **kwargs: 传递给create_video的其他参数
            
        Returns:
            生成的视频文件路径
        """
        return self.create_video(
            image_path=results["image"],
            speech_path=results["speech"],
            music_path=results["music"],
            output_name=output_name,
            **kwargs
        ) 