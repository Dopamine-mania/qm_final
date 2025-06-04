from image_generator import ImageGenerator
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

def main():
    # 初始化图像生成器
    generator = ImageGenerator()
    
    # 加载模型
    generator.load_model()
    
    # 生成图像
    result = generator.generate_image(
        prompt="A serene forest landscape with a flowing river, soft morning light, peaceful atmosphere",
        negative_prompt="ugly, blurry, low quality, distorted",
        num_inference_steps=30,
        guidance_scale=7.5
    )
    
    # 保存图像
    generator.save_image(result["image"], "output/forest_landscape.png")
    
if __name__ == "__main__":
    main() 