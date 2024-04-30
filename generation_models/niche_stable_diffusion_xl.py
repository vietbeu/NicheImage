import diffusers
from PIL import Image
from .base_model import BaseModel
from .utils import (
    download_checkpoint,
    base64_to_pil_image,
    resize_for_condition_image,
    set_scheduler,
)
import os
import torch
import sys

class NicheStableDiffusionXL(BaseModel):
    def load_model(self, checkpoint_file, download_url, supporting_pipelines, **kwargs):
        if not os.path.exists(checkpoint_file):
            download_checkpoint(download_url, checkpoint_file)

        txt2img_pipe = diffusers.StableDiffusionXLPipeline.from_single_file(
            checkpoint_file,
            use_safetensors=True,
            torch_dtype=torch.float16,
            load_safety_checker=False,
        )
        scheduler_name = kwargs.get("scheduler", "euler_a")
        txt2img_pipe.scheduler = set_scheduler(
            scheduler_name, txt2img_pipe.scheduler.config
        )
        txt2img_pipe.to("cuda")


        img2img_pipe = self.load_img2img(txt2img_pipe.components, supporting_pipelines)
        instant_id_pipe = self.load_instantid_pipeline(txt2img_pipe.components, supporting_pipelines)
        pipelines = {
            "txt2img": txt2img_pipe,
            "img2img": img2img_pipe,
            "instantid": instant_id_pipe,
        }

        def inference_function(*args, **kwargs) -> Image.Image:
            pipeline_type = kwargs["pipeline_type"]
            pipeline = pipelines[pipeline_type]
            if not pipeline:
                raise ValueError(f"Pipeline type {pipeline_type} is not supported")
            
            output = pipeline(*args, **kwargs)
            if output is None:
                return Image.new("RGB", (512, 512), (255, 255, 255))
            return output.images[0]

        return inference_function

    def load_img2img(self, components, supporting_pipelines) -> callable:
        if "img2img" not in supporting_pipelines:
            return None
        img2img_pipe = diffusers.StableDiffusionXLImg2ImgPipeline(**components)
        img2img_pipe.to("cuda")

        def inference_function(*args, **kwargs):
            conditional_image = self.process_conditional_image(**kwargs)
            width, height = conditional_image.size
            kwargs.update(
                {
                    "image": conditional_image,
                    "width": width,
                    "height": height,
                }
            )
            return img2img_pipe(*args, **kwargs)

        return inference_function

    def load_instantid_pipeline(self, components, supporting_pipelines) -> callable:
        if "instantid" not in supporting_pipelines:
            return None

        from huggingface_hub import hf_hub_download
        hf_hub_download(repo_id="InstantX/InstantID", filename="ControlNetModel/config.json", local_dir="checkpoints/InstantID")
        hf_hub_download(repo_id="InstantX/InstantID", filename="ControlNetModel/diffusion_pytorch_model.safetensors", local_dir="checkpoints/InstantID")
        hf_hub_download(repo_id="InstantX/InstantID", filename="ip-adapter.bin", local_dir="checkpoints/InstantID")

        from insightface.app import FaceAnalysis

        app = FaceAnalysis(name='antelopev2', root='checkpoints/insightface', providers=['CUDAExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(640, 640))

        sys.path.append("generation_models/custom_pipelines/InstantID")
        import cv2
        import numpy as np
        from pipeline_stable_diffusion_xl_instantid import StableDiffusionXLInstantIDPipeline, draw_kps

        controlnet_path = "checkpoints/InstantID/ControlNetModel"
        face_adapter = "checkpoints/InstantID/ip-adapter.bin"
        controlnet = diffusers.ControlNetModel.from_pretrained(controlnet_path, torch_dtype=torch.float16, local_files_only=True)
        pipe = StableDiffusionXLInstantIDPipeline(**components, controlnet=controlnet)
        pipe.set_ip_adapter_scale(0)
        pipe.to("cuda")
        pipe.load_ip_adapter_instantid(face_adapter)

        def inference_function(*args, **kwargs):
            conditional_image: Image.Image = self.process_conditional_image(**kwargs)
            face_info = app.get(cv2.cvtColor(np.array(conditional_image), cv2.COLOR_RGB2BGR))
            if len(face_info) == 0:
                print("No face detected", flush=True)
                return None
            face_info = sorted(face_info, key=lambda x:(x['bbox'][2]-x['bbox'][0])*(x['bbox'][3]-x['bbox'][1]))[-1]  # only use the maximum face
            face_emb = face_info['embedding']
            face_kps = draw_kps(conditional_image, face_info['kps'])
            if kwargs.get("kps_conditional_image"):
                conditional_image: Image.Image = self.process_conditional_image(key="kps_conditional_image", **kwargs)
                face_info = app.get(cv2.cvtColor(np.array(conditional_image), cv2.COLOR_RGB2BGR))
                face_info = sorted(face_info, key=lambda x:(x['bbox'][2]-x['bbox'][0])*(x['bbox'][3]-x['bbox'][1]))[-1]  # only use the maximum face
                face_kps = draw_kps(conditional_image, face_info['kps'])
            
            kwargs.update(
                {
                    "image_embeds": face_emb,
                    "image": face_kps,
                }
            )
            images = pipe(*args, **kwargs)
            pipe.set_ip_adapter_scale(0)
            return images

        return inference_function

    def process_conditional_image(self, key="conditional_image", **kwargs) -> Image.Image:
        conditional_image = kwargs[key]
        conditional_image = base64_to_pil_image(conditional_image)
        resolution = kwargs.get("resolution", 768)
        conditional_image = resize_for_condition_image(conditional_image, resolution)
        return conditional_image
