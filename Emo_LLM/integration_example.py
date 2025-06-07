#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
这是一个示例脚本，展示如何将Emo_LLM模型与TTI、TTS和TTM三个模块集成。
注意：这个脚本只是示例，实际运行需要确保其他三个模块已正确配置。
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

# 添加必要的路径
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)
sys.path.append(os.path.join(script_dir, 'LLaMA-Factory/src'))

# 导入Emo_LLM模型
from llamafactory.chat import ChatModel

# 导入其他模块（路径可能需要根据实际情况调整）
sys.path.append(os.path.join(parent_dir, 'TTI'))
sys.path.append(os.path.join(parent_dir, 'TTS'))
sys.path.append(os.path.join(parent_dir, 'TTM'))

# 导入各个生成器
from TTI.image_generator import ImageGenerator
from TTS.speech_generator import SpeechGenerator
from TTM.music_generator import MusicGenerator
from integration2.multimodal_generator import MultimodalVideoGenerator

def parse_args():
    parser = argparse.ArgumentParser(description='Integrated Emoheal demo')
    parser.add_argument('--llm_model_path', type=str, 
                        default=os.path.join(script_dir, 'Model_results/emoheal_merged'),
                        help='Path to the Emoheal LLM model')
    parser.add_argument('--input', type=str, required=True,
                        help='User input text to process')
    parser.add_argument('--output_dir', type=str, default='output',
                        help='Directory to save generated files')
    return parser.parse_args()

def load_emoheal_model(model_path: str) -> ChatModel:
    """加载Emoheal LLM模型"""
    print(f"Loading Emoheal model from: {model_path}")
    
    model_args = {
        "model_name_or_path": model_path,
        "infer_backend": "huggingface",
        "trust_remote_code": True
    }
    
    return ChatModel(model_args)

def generate_emoheal_response(model: ChatModel, text: str) -> Dict[str, Any]:
    """生成Emoheal模型的响应"""
    print(f"Generating emotional response for: '{text}'")
    
    # 设置消息格式
    messages = [{"role": "user", "content": text}]
    
    # 获取模型响应
    response = model.chat(messages)[0].content
    
    # 解析响应
    try:
        # 移除可能的多余字符
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        
        # 解析JSON
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"Error parsing response as JSON: {e}")
        print(f"Raw response: {response}")
        raise

def setup_generators():
    """初始化各个生成器"""
    print("Setting up TTI, TTS, and TTM generators...")
    
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
    
    # 加载模型
    multimodal_gen.load_all_models()
    
    return multimodal_gen

def generate_multimedia_content(generator: MultimodalVideoGenerator, emoheal_response: Dict[str, Any], output_dir: str) -> str:
    """使用Emoheal响应生成多媒体内容"""
    print("Generating multimedia content based on emotional response...")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 提取各个prompt
    image_prompt = emoheal_response.get('image_prompt', '')
    voice_text = emoheal_response.get('voice_text', '')
    music_prompt = emoheal_response.get('music_prompt', '')
    emotion_tag = emoheal_response.get('emotion_tag', 'neutral')
    
    # 设置输出文件名
    output_filename = f"{emotion_tag}_response.mp4"
    
    # 生成并合成视频
    video_path = generator.generate_and_synthesize(
        image_prompt=image_prompt,
        speech_prompt=voice_text,
        music_prompt=music_prompt,
        output_filename=output_filename,
        video_duration=30  # 30秒视频
    )
    
    return video_path

def main():
    args = parse_args()
    
    try:
        # 1. 加载Emoheal模型
        emoheal_model = load_emoheal_model(args.llm_model_path)
        
        # 2. 生成情感响应
        emoheal_response = generate_emoheal_response(emoheal_model, args.input)
        
        # 3. 设置生成器
        multimodal_generator = setup_generators()
        
        # 4. 生成多媒体内容
        video_path = generate_multimedia_content(
            multimodal_generator, 
            emoheal_response,
            args.output_dir
        )
        
        print(f"\nProcess completed successfully!")
        print(f"Generated video saved at: {video_path}")
        
    except Exception as e:
        print(f"\nError during processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 