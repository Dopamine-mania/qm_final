#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
from typing import Optional, Dict, Any

# 添加LLaMA-Factory到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
llamafactory_dir = os.path.join(script_dir, 'LLaMA-Factory/src')
sys.path.append(llamafactory_dir)

# 导入LLaMA-Factory的ChatModel
from llamafactory.chat import ChatModel

def parse_args():
    parser = argparse.ArgumentParser(description='Test the Emoheal LLM model')
    parser.add_argument('--model_path', type=str, default=os.path.join(script_dir, 'Model_results/emoheal_merged'),
                        help='Path to the model directory')
    parser.add_argument('--input', type=str, default=None,
                        help='Input text to generate response (if not provided, will use interactive mode)')
    return parser.parse_args()

def format_response(response: str) -> Dict[str, Any]:
    """将模型的JSON字符串响应解析为Python字典"""
    try:
        # 移除可能的多余字符
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        
        # 解析JSON
        return json.loads(response)
    except json.JSONDecodeError:
        print(f"Error parsing response as JSON: {response}")
        return {
            "error": "Failed to parse response",
            "raw_response": response
        }

def generate_response(model: ChatModel, text: str) -> Dict[str, Any]:
    """生成模型响应并解析"""
    # 设置消息格式
    messages = [{"role": "user", "content": text}]
    
    # 获取模型响应
    response = model.chat(messages)[0].content
    
    # 解析并返回响应
    return format_response(response)

def print_formatted_response(response: Dict[str, Any]):
    """打印格式化的响应"""
    if "error" in response:
        print(f"Error: {response['error']}")
        print(f"Raw response: {response['raw_response']}")
        return
    
    print("\n===== EMOHEAL RESPONSE =====")
    
    if "emotion_tag" in response:
        print(f"Emotion Tag: {response['emotion_tag']}")
    
    if "music_prompt" in response:
        print(f"\nMusic Prompt: {response['music_prompt']}")
    
    if "image_prompt" in response:
        print(f"\nImage Prompt: {response['image_prompt']}")
    
    if "voice_text" in response:
        print(f"\nVoice Text: {response['voice_text']}")
    
    print("===========================\n")

def interactive_mode(model: ChatModel):
    """交互模式，允许用户输入文本并获取响应"""
    print("===== EMOHEAL MODEL INTERACTIVE TEST =====")
    print("Type 'quit' or 'exit' to end the session")
    print("==========================================\n")
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        
        if not user_input.strip():
            continue
            
        print("Generating response...\n")
        response = generate_response(model, user_input)
        print_formatted_response(response)

def main():
    args = parse_args()
    
    print(f"Loading model from: {args.model_path}")
    
    # 设置模型参数
    model_args = {
        "model_name_or_path": args.model_path,
        "infer_backend": "huggingface",    # 使用Huggingface后端
        "trust_remote_code": True  # 信任远程代码
    }
    
    # 加载模型
    try:
        model = ChatModel(model_args)
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    # 根据是否提供输入决定模式
    if args.input:
        response = generate_response(model, args.input)
        print_formatted_response(response)
    else:
        interactive_mode(model)

if __name__ == "__main__":
    main() 