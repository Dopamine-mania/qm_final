from image_generator import ImageGenerator
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO)

def test_image_generation():
    # 创建输出目录
    os.makedirs("output/images", exist_ok=True)
    
    # 初始化图像生成器
    generator = ImageGenerator()
    
    # 加载模型
    generator.load_model()
    
    # 测试用例
    test_cases = [
        {
            "name": "serene_landscape",
            "prompt": "A serene forest landscape with a flowing river, soft morning light, peaceful atmosphere, highly detailed, 8k resolution",
            "negative_prompt": "ugly, blurry, low quality, distorted, oversaturated",
            "num_inference_steps": 30,
            "guidance_scale": 7.5
        },
        {
            "name": "emotional_abstract",
            "prompt": "Abstract art representing inner peace and tranquility, soft pastel colors, flowing shapes, ethereal atmosphere",
            "negative_prompt": "realistic, photographic, harsh colors, sharp edges",
            "num_inference_steps": 40,
            "guidance_scale": 8.0
        },
        {
            "name": "healing_garden",
            "prompt": "A healing garden with blooming flowers, gentle sunlight, butterflies, and a small meditation pond, peaceful atmosphere",
            "negative_prompt": "dark, gloomy, dead plants, harsh lighting",
            "num_inference_steps": 35,
            "guidance_scale": 7.0
        }
    ]
    
    # 运行测试
    for case in test_cases:
        print(f"\nGenerating image for: {case['name']}")
        print(f"Prompt: {case['prompt']}")
        
        # 生成单张图片
        result = generator.generate_image(
            prompt=case["prompt"],
            negative_prompt=case["negative_prompt"],
            num_inference_steps=case["num_inference_steps"],
            guidance_scale=case["guidance_scale"]
        )
        
        # 保存图片
        output_path = f"output/images/{case['name']}.png"
        generator.save_image(result["images"][0], output_path)
        print(f"Image saved to: {output_path}")
        
        # 生成多张图片并创建网格
        print(f"\nGenerating multiple images for: {case['name']}")
        result = generator.generate_image(
            prompt=case["prompt"],
            negative_prompt=case["negative_prompt"],
            num_inference_steps=case["num_inference_steps"],
            guidance_scale=case["guidance_scale"],
            num_images=4
        )
        
        # 创建并保存网格
        grid = generator.generate_image_grid(result["images"], grid_size=(2, 2))
        grid_path = f"output/images/{case['name']}_grid.png"
        generator.save_image(grid, grid_path)
        print(f"Image grid saved to: {grid_path}")

if __name__ == "__main__":
    test_image_generation() 