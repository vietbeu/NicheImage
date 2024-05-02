from fastapi import FastAPI
from pydantic import BaseModel, Extra
import argparse
from typing import Optional
from transformers import set_seed
import httpx
import random
from datasets import load_dataset
import random
import time

class Prompt(BaseModel, extra=Extra.allow):
    prompt: str
    seed: Optional[int] = 0
    max_length: Optional[int] = 77


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=10001)
    parser.add_argument("--netuid", type=str, default=23)
    parser.add_argument("--min_stake", type=int, default=100)
    parser.add_argument(
        "--chain_endpoint",
        type=str,
        default="finney",
    )
    parser.add_argument("--disable_secure", action="store_true", default=False)
    args = parser.parse_args()
    return args


class ChallengeImage:
    def __init__(self):
        self.captions, self.templates = self.init_caption()
        print(f"Total captions: {len(self.captions)}", flush=True)
        self.app = FastAPI()
        self.app.add_api_route("/", self.__call__, methods=["POST"])
    def init_caption(self):
        gpt4v_220k = load_dataset("toilaluan/livis-gpt4v-laicon-coco-aes-caption")
        captions = gpt4v_220k['train']['caption']
        with open("services/challenge_generating/prompt_generating/template.txt", "r") as f:
            templates = f.readlines()
            templates = [template.strip() for template in templates]
        return captions, templates
    async def __call__(
        self, data: dict,
    ):
        start = time.time()
        prompt = random.choice(self.captions)
        template = random.choice(self.templates)
        prompt = template.replace("{{prompt}}", prompt)
        print(f"Time taken: {time.time()-start}", flush=True)
        return {"prompt": prompt}


app = ChallengeImage()
