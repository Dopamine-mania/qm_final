import os
import logging
from parallel_generator import ParallelGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # 初始化并行生成器
    generator = ParallelGenerator(output_dir="output")
    
    # 测试用例
    test_cases = [
        {
            "name": "冥想场景",
            "speech_text": "让我们深呼吸，感受当下的平静。吸气，感受空气充满肺部；呼气，释放所有的紧张。",
            "image_prompt": "A serene meditation room with soft lighting, incense burning, and a person sitting in lotus position",
            "music_prompt": "Calm meditation music with gentle nature sounds and soft piano",
            "language": "zh"
        },
        {
            "name": "治愈花园",
            "speech_text": "想象你漫步在一个美丽的花园中，阳光温暖，花香四溢。每一朵花都在诉说着生命的美好。",
            "image_prompt": "A beautiful healing garden with colorful flowers, butterflies, and a peaceful path",
            "music_prompt": "Peaceful garden ambient music with birds chirping and gentle wind sounds",
            "language": "zh"
        }
    ]
    
    # 运行测试
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n=== 测试用例 {i}: {test_case['name']} ===")
        
        try:
            # 并行生成所有内容
            results = generator.generate_all(
                speech_text=test_case["speech_text"],
                image_prompt=test_case["image_prompt"],
                music_prompt=test_case["music_prompt"],
                language=test_case["language"]
            )
            
            # 打印结果
            logger.info("生成完成！文件路径：")
            for key, path in results.items():
                logger.info(f"{key}: {path}")
                
        except Exception as e:
            logger.error(f"生成过程中出错: {str(e)}")
            
    # 清理资源
    generator.cleanup()
    
if __name__ == "__main__":
    main() 