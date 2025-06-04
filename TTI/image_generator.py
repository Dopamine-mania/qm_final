import torch
from diffusers import AutoPipelineForText2Image
from typing import Optional, Dict, Any, List
import logging
from PIL import Image
import numpy as np

class ImageGenerator:
    def __init__(self, model_id: str = "playgroundai/playground-v2.5-1024px-aesthetic"):
        """
        初始化图像生成器
        
        Args:
            model_id: 图像生成模型ID，默认使用Playground v2.5
        """
        self.logger = logging.getLogger(__name__)
        self.model_id = model_id
        self.pipeline = None
        
    def load_model(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        """
        加载模型
        
        Args:
            device: 运行设备
        """
        try:
            self.pipeline = AutoPipelineForText2Image.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                use_safetensors=True,
                variant="fp16" if device == "cuda" else None
            )
            self.pipeline.to(device)
            self.logger.info(f"Model loaded successfully on {device}")
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            raise
            
    def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成图像
        
        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            num_inference_steps: 推理步数
            guidance_scale: 引导系数
            width: 图像宽度
            height: 图像高度
            num_images: 生成图像数量
            seed: 随机种子
            **kwargs: 其他参数
            
        Returns:
            包含生成图像信息的字典
        """
        if self.pipeline is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
            
        try:
            # 设置随机种子
            if seed is not None:
                torch.manual_seed(seed)
                torch.cuda.manual_seed_all(seed)
            
            # 生成图像
            result = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                num_images_per_prompt=num_images,
                **kwargs
            )
            
            return {
                "images": result.images,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "parameters": {
                    "num_inference_steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "width": width,
                    "height": height,
                    "num_images": num_images,
                    "seed": seed,
                    **kwargs
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating image: {str(e)}")
            raise
            
    def save_image(self, image: Image.Image, output_path: str):
        """
        保存生成的图像
        
        Args:
            image: PIL图像对象
            output_path: 输出路径
        """
        try:
            image.save(output_path)
            self.logger.info(f"Image saved to {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving image: {str(e)}")
            raise
            
    def generate_image_grid(self, images: List[Image.Image], grid_size: tuple = (2, 2)) -> Image.Image:
        """
        将多个图像组合成网格
        
        Args:
            images: 图像列表
            grid_size: 网格大小 (rows, cols)
            
        Returns:
            组合后的图像
        """
        rows, cols = grid_size
        width = images[0].width
        height = images[0].height
        
        grid = Image.new('RGB', (width * cols, height * rows))
        
        for idx, img in enumerate(images):
            if idx >= rows * cols:
                break
            row = idx // cols
            col = idx % cols
            grid.paste(img, (col * width, row * height))
            
        return grid 