import logging
import os
import sys

# --- Path Setup ---
# Ensures the script can find the TTI, TTS, and TTM modules
try:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except NameError:
    project_root = os.path.abspath('.')
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

# --- Actor Selection (Import the specific generators you want to use) ---
from TTI.image_generator import ImageGenerator
from TTS.speech_generator import SpeechGenerator
from TTM.music_generator import MusicGenerator
from integration2.multimodal_generator import MultimodalVideoGenerator

# --- Configuration ---
# 1. Configure the ACEStep model path (optional)
#    Set to a local path or leave as None to auto-download.
ACESTEP_CHECKPOINT_PATH = None

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(), logging.FileHandler("generation.log", mode='w')])

def main():
    """
    Main function to configure, instantiate, and run the multimodal video generation.
    """
    logger = logging.getLogger("Director")

    # --- 1. Casting the Actors (Instantiate your chosen generators) ---
    logger.info("Casting actors for our video production...")
    # To use a different music model, you would just instantiate a different class here.
    # For example: music_actor = NewMusicGenerator(api_key="...")
    image_actor = ImageGenerator()
    speech_actor = SpeechGenerator()
    music_actor = MusicGenerator(checkpoint_path=ACESTEP_CHECKPOINT_PATH)
    
    # --- 2. Hiring the Director (Instantiate the main generator and inject dependencies) ---
    logger.info("Hiring the director and giving them the cast...")
    director = MultimodalVideoGenerator(
        image_gen=image_actor,
        speech_gen=speech_actor,
        music_gen=music_actor
    )

    # --- 3. Pre-production (Load all models) ---
    try:
        logger.info("Director is asking all actors to get ready (loading models)...")
        director.load_all_models()
    except Exception as e:
        logger.error("A critical error occurred during model loading. Production is cancelled.", exc_info=True)
        return

    # --- 4. Lights, Camera, Action! (Define prompts and run the generation) ---
    logger.info("Scene 1: The English Epic. Action!")
    run_generation_task(
        director=director,
        task_name="English-Fantasy-Epic",
        prompts={
            "image": "Epic fantasy landscape, a lone knight looking at a castle on a cliff, hyperdetailed, digital art.",
            "speech": "In a land of myth and a time of magic, the destiny of a great kingdom rests on the shoulders of a young knight.",
            "music": "Epic orchestral, fantasy movie soundtrack, adventurous, powerful, choir, cinematic."
        },
        params={
            "output_filename": "english_fantasy_epic.mp4",
            "video_duration": 12,
            "music_params": {"lyrics": "Destiny calls, heroes rise."}
        }
    )

    logger.info("Scene 2: The Chinese Landscape. Action!")
    run_generation_task(
        director=director,
        task_name="Chinese-Serene-Landscape",
        prompts={
            "image": "A beautiful ancient Chinese painting of serene mountains and a peaceful lake, Guilin landscape, ink wash style.",
            "speech": "欢迎来到这片山水之间。在这里，时间仿佛静止，只剩下自然的呼吸和内心的平和。",
            "music": "Chinese traditional style, Guzheng, serene, peaceful, melodic"
        },
        params={
            "output_filename": "chinese_serene_landscape.mp4",
            "video_duration": 12,
            "music_params": {"lyrics": "山水之间，心自安。"}
        }
    )
    
    logger.info("All scenes are complete. Production finished!")


def run_generation_task(director: MultimodalVideoGenerator, task_name: str, prompts: dict, params: dict):
    """ Helper function to run a video generation task. """
    logger = logging.getLogger(task_name)
    logger.info(f"--- Starting scene: {task_name} ---")
    try:
        video_path = director.generate_and_synthesize(
            image_prompt=prompts["image"],
            speech_prompt=prompts["speech"],
            music_prompt=prompts["music"],
            **params
        )
        logger.info(f"--- Scene '{task_name}' wrapped! Video at: {os.path.abspath(video_path)} ---")
    except Exception as e:
        logger.error(f"--- Scene '{task_name}' failed! Error: {e} ---", exc_info=True)


if __name__ == "__main__":
    main() 