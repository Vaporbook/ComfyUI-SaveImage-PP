from comfy.cli_args import args
import folder_paths
import json
import numpy
import os
from PIL import Image, ExifTags
from PIL.PngImagePlugin import PngInfo

class SaveImagePP:
    def __init__(self):
        pass

    FILE_TYPE_PNG = "PNG"
    FILE_TYPE_JPEG = "JPEG"
    FILE_TYPE_WEBP_LOSSLESS = "WEBP (lossless)"
    FILE_TYPE_WEBP_LOSSY = "WEBP (lossy)"
    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "image"
    MODEL_LOADER_CHECKPOINT_SIMPLE = "CheckpointLoaderSimple"
    MODEL_LOADER_NONE = "None"
    MODEL_LOADER_DEFAULT = MODEL_LOADER_CHECKPOINT_SIMPLE 
    COMFYUI_PREFIX = "%date:yyyy-MM-dd%/ComfyUI_%date:hhmmss%_"
    PNG_COMPRESS_LEVEL = 4 

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
                "filename_prefix": ("STRING", {"default": s.COMFYUI_PREFIX}),
                "model_loader_id": ([s.MODEL_LOADER_DEFAULT, s.MODEL_LOADER_NONE], ),
                "file_type": ([s.FILE_TYPE_PNG, s.FILE_TYPE_JPEG, s.FILE_TYPE_WEBP_LOSSLESS, s.FILE_TYPE_WEBP_LOSSY], ),
                "remove_metadata": ("BOOLEAN", {"default": False}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    def save_images(self, images, filename_prefix=COMFYUI_PREFIX, model_loader_id=MODEL_LOADER_DEFAULT, file_type=FILE_TYPE_PNG, remove_metadata=False, prompt=None, extra_pnginfo=None):
        output_dir = folder_paths.get_output_directory()
        
        # TODO: expand the list to include other model loaders and the correct ref for each
        if model_loader_id == s.MODEL_LOADER_CHECKPOINT_SIMPLE:
            model_ref = "CheckpointLoaderSimple.ckpt_name"
            filename_prefix += f"%{model_ref}%_"

        full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(filename_prefix, output_dir, images[0].shape[1], images[0].shape[0])
        
        extension = {
            self.FILE_TYPE_PNG: "png",
            self.FILE_TYPE_JPEG: "jpg",
            self.FILE_TYPE_WEBP_LOSSLESS: "webp",
            self.FILE_TYPE_WEBP_LOSSY: "webp",
        }.get(file_type, "png")

        results = []
        for image in images:
            array = 255. * image.cpu().numpy()
            img = Image.fromarray(numpy.clip(array, 0, 255).astype(numpy.uint8))

            kwargs = dict()
            if extension == "png":
                kwargs["compress_level"] = PNG_COMPRESS_LEVEL
                if not remove_metadata and not args.disable_metadata:
                    metadata = PngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for x in extra_pnginfo:
                            metadata.add_text(x, json.dumps(extra_pnginfo[x]))
                    kwargs["pnginfo"] = metadata
            else:
                if file_type == self.FILE_TYPE_WEBP_LOSSLESS:
                    kwargs["lossless"] = True
                else:
                    kwargs["quality"] = 90
                if not remove_metadata and not args.disable_metadata:
                    metadata = {}
                    if prompt is not None:
                        metadata["prompt"] = prompt
                    if extra_pnginfo is not None:
                        metadata.update(extra_pnginfo)
                    exif = img.getexif()
                    exif[ExifTags.Base.UserComment] = json.dumps(metadata)
                    kwargs["exif"] = exif.tobytes()

            file = f"{filename}_{counter:05}_.{extension}"
            img.save(os.path.join(full_output_folder, file), **kwargs)
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": "output",
            })
            counter += 1

        return { "ui": { "images": results } }

NODE_CLASS_MAPPINGS = {
    "SaveImagePP": SaveImagePP
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImagePP": "Save Image PP"
}

WEB_DIRECTORY = "web"
