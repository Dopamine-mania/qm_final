#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
全流程集成脚本：情感反馈模型 + TTI + TTS + TTM

流程：
1. 用户输入文本
2. 情感反馈模型生成JSON响应(emotion_tag, music_prompt, image_prompt, voice_text)
3. 三个模块根据各自的prompt生成内容
4. 合成最终视频
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler(), 
                             logging.FileHandler("full_pipeline.log", mode='w')])

logger = logging.getLogger(__name__)

# 添加必要的路径
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)
sys.path.append(os.path.join(script_dir, 'LLaMA-Factory/src'))

# 导入情感反馈模型
from llamafactory.chat import ChatModel

# 导入其他模块
sys.path.append(os.path.join(parent_dir, 'TTI'))
sys.path.append(os.path.join(parent_dir, 'TTS'))
sys.path.append(os.path.join(parent_dir, 'TTM'))
sys.path.append(os.path.join(parent_dir, 'integration2'))

# 确保可以直接导入基类
tts_path = os.path.join(parent_dir, 'TTS')
if tts_path not in sys.path:
    sys.path.insert(0, tts_path)
    
# 打印当前 Python 路径，用于调试
logger.info("Python 路径:")
for path in sys.path:
    logger.info(f"  - {path}")

# 导入各个生成器
try:
    from TTI.image_generator import ImageGenerator
    from speech_generator import SpeechGenerator
    from TTM.music_generator import MusicGenerator
    from integration2.multimodal_generator import MultimodalVideoGenerator
    logger.info("所有模块导入成功!")
except ImportError as e:
    logger.error(f"导入模块时出错: {e}")
    raise

def parse_args():
    parser = argparse.ArgumentParser(description='全流程集成演示')
    parser.add_argument('--llm_model_path', type=str, 
                        default=os.path.join(script_dir, 'Model_results/emoheal_merged'),
                        help='情感反馈模型路径')
    parser.add_argument('--input', type=str, 
                        help='用户输入文本')
    parser.add_argument('--output_dir', type=str, default='output_videos',
                        help='输出视频目录')
    parser.add_argument('--interactive', action='store_true',
                        help='是否使用交互模式')
    return parser.parse_args()

def load_emoheal_model(model_path: str) -> ChatModel:
    """加载情感反馈模型"""
    logger.info(f"正在加载情感反馈模型，路径: {model_path}")
    
    model_args = {
        "model_name_or_path": model_path,
        "infer_backend": "huggingface",
        "trust_remote_code": True
    }
    
    model = ChatModel(model_args)
    logger.info("情感反馈模型加载成功！")
    return model

def generate_emoheal_response(model: ChatModel, text: str) -> Dict[str, Any]:
    """生成情感响应"""
    logger.info(f"正在为文本生成情感响应: '{text}'")
    
    # 设置消息格式
    messages = [{"role": "user", "content": text}]
    
    # 获取模型响应
    response = model.chat(messages)[0].response_text
    
    # 解析响应
    try:
        # 移除可能的多余字符
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        
        # 解析JSON
        result = json.loads(response)
        logger.info(f"情感响应生成成功: {result['emotion_tag']}")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"解析JSON响应出错: {e}")
        logger.error(f"原始响应: {response}")
        raise

def setup_generators(output_dir: str) -> MultimodalVideoGenerator:
    """初始化各个生成器"""
    logger.info("正在初始化TTI, TTS和TTM生成器...")
    
    # 初始化生成器
    image_gen = ImageGenerator()
    speech_gen = SpeechGenerator()
    music_gen = MusicGenerator()
    
    # 初始化多模态生成器
    multimodal_gen = MultimodalVideoGenerator(
        image_gen=image_gen,
        speech_gen=speech_gen,
        music_gen=music_gen
    )
    
    # 设置输出目录
    multimodal_gen.output_dir = output_dir
    
    # 加载模型
    logger.info("正在加载各个生成模型...")
    multimodal_gen.load_all_models()
    logger.info("所有模型加载完成！")
    
    return multimodal_gen

def generate_multimedia_content(
    generator: MultimodalVideoGenerator, 
    emoheal_response: Dict[str, Any]
) -> str:
    """根据情感响应生成多媒体内容"""
    logger.info("根据情感响应生成多媒体内容...")
    
    # 提取各个prompt
    image_prompt = emoheal_response.get('image_prompt', '')
    voice_text = emoheal_response.get('voice_text', '')
    music_prompt = emoheal_response.get('music_prompt', '')
    emotion_tag = emoheal_response.get('emotion_tag', 'neutral')
    
    # 设置输出文件名
    output_filename = f"{emotion_tag}_response.mp4"
    
    try:
        # 生成并合成视频
        video_path = generator.generate_and_synthesize(
            image_prompt=image_prompt,
            speech_prompt=voice_text,
            music_prompt=music_prompt,
            output_filename=output_filename,
            video_duration=45,  # 45秒视频
            num_images=9,  # 生成9张图片，每5秒切换一次
            enable_subtitles=True,
            speech_text=voice_text  # 使用语音文本作为字幕
        )
        
        logger.info(f"视频生成完成: {video_path}")
        return video_path
    except Exception as e:
        logger.error(f"视频生成失败: {str(e)}")
        raise

def print_formatted_response(response: Dict[str, Any]):
    """打印格式化的响应"""
    print("\n===== 情感反馈模型响应 =====")
    
    if "emotion_tag" in response:
        print(f"情感标签: {response['emotion_tag']}")
    
    if "music_prompt" in response:
        print(f"\n音乐提示词: {response['music_prompt']}")
    
    if "image_prompt" in response:
        print(f"\n图像提示词: {response['image_prompt']}")
    
    if "voice_text" in response:
        print(f"\n语音文本: {response['voice_text']}")
    
    print("===========================\n")

def process_single_input(
    emoheal_model: ChatModel,
    multimodal_generator: MultimodalVideoGenerator,
    user_input: str
) -> str:
    """处理单条用户输入"""
    # 1. 生成情感响应
    emoheal_response = generate_emoheal_response(emoheal_model, user_input)
    
    # 2. 打印响应内容
    print_formatted_response(emoheal_response)
    
    # 3. 生成多媒体内容
    video_path = generate_multimedia_content(multimodal_generator, emoheal_response)
    
    return video_path

def interactive_mode(
    emoheal_model: ChatModel,
    multimodal_generator: MultimodalVideoGenerator
):
    """交互模式，允许用户输入文本并获取视频响应"""
    print("\n===== 情感反馈全流程演示系统 =====")
    print("输入文本，系统将生成对应的视频")
    print("输入 'quit' 或 'exit' 退出")
    print("===========================\n")
    
    while True:
        user_input = input("\n用户输入: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        
        if not user_input.strip():
            continue
            
        try:
            video_path = process_single_input(
                emoheal_model, 
                multimodal_generator,
                user_input
            )
            print(f"\n✓ 视频生成成功: {video_path}")
            print(f"请打开此文件查看生成结果")
        except Exception as e:
            logger.error(f"处理过程中出错: {e}", exc_info=True)
            print(f"\n✗ 生成过程出错: {str(e)}")

def process_text_to_video(user_input: str, output_dir: str = "static/output") -> str:
    """
    Web应用程序接口：处理用户输入并生成视频
    
    Args:
        user_input: 用户输入的文本
        output_dir: 输出目录路径
        
    Returns:
        生成的视频文件的完整路径
    """
    logger.info(f"处理文本输入: {user_input}")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 1. 加载情感反馈模型
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Model_results/emoheal_merged')
        emoheal_model = load_emoheal_model(model_path)
        
        # 2. 设置生成器
        multimodal_generator = setup_generators(output_dir)
        
        # 3. 生成响应
        emoheal_response = generate_emoheal_response(emoheal_model, user_input)
        
        # 4. 生成多媒体内容
        video_path = generate_multimedia_content(multimodal_generator, emoheal_response)
        
        logger.info(f"视频生成成功: {video_path}")
        return video_path
        
    except Exception as e:
        logger.error(f"处理过程中出错: {e}", exc_info=True)
        raise Exception(f"生成视频失败: {str(e)}")

def main():
    args = parse_args()
    
    try:
        # 1. 确保输出目录存在
        os.makedirs(args.output_dir, exist_ok=True)
        
        # 2. 加载情感反馈模型
        emoheal_model = load_emoheal_model(args.llm_model_path)
        
        # 3. 设置生成器
        multimodal_generator = setup_generators(args.output_dir)
        
        # 4. 根据模式处理输入
        if args.interactive:
            interactive_mode(emoheal_model, multimodal_generator)
        elif args.input:
            video_path = process_single_input(
                emoheal_model, 
                multimodal_generator,
                args.input
            )
            print(f"\n✓ 视频生成成功: {video_path}")
        else:
            print("错误: 请提供输入文本(--input)或使用交互模式(--interactive)")
            return 1
        
        print("\n处理完成！")
        return 0
        
    except Exception as e:
        logger.error(f"执行过程中出错: {e}", exc_info=True)
        print(f"\n错误: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 