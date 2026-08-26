"""
captioning.py

Generates natural-language captions for a folder of images using BLIP
(Salesforce/blip-image-captioning-base), run locally via HuggingFace transformers.

This is the "indexing" step: run once (or on new uploads) to build the caption
store that TF-IDF and the LLM ranker will later search over.

Usage:
    python captioning.py --image_dir ./photos --out captions.json
"""

import argparse
import json
import os

from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

MODEL_NAME = "Salesforce/blip-image-captioning-base"
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def load_model():
    """Load BLIP processor + model once. Reuse across calls — loading is expensive."""
    processor = BlipProcessor.from_pretrained(MODEL_NAME)
    model = BlipForConditionalGeneration.from_pretrained(MODEL_NAME)
    model.eval()
    return processor, model


def caption_image(image_path: str, processor, model) -> str:
    """Generate a single caption for one image file."""
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    output_ids = model.generate(**inputs, max_new_tokens=30)
    caption = processor.decode(output_ids[0], skip_special_tokens=True)
    return caption


def caption_directory(image_dir: str, processor, model) -> dict:
    """Walk a directory of images and caption every supported file."""
    captions = {}
    for fname in sorted(os.listdir(image_dir)):
        ext = os.path.splitext(fname)[1].lower()
        if ext not in SUPPORTED_EXTS:
            continue
        path = os.path.join(image_dir, fname)
        try:
            captions[fname] = caption_image(path, processor, model)
        except Exception as e:
            print(f"[warn] skipped {fname}: {e}")
    return captions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_dir", required=True, help="Folder of photos to caption")
    parser.add_argument("--out", default="captions.json", help="Output JSON path")
    args = parser.parse_args()

    processor, model = load_model()
    captions = caption_directory(args.image_dir, processor, model)

    with open(args.out, "w") as f:
        json.dump(captions, f, indent=2)

    print(f"Captioned {len(captions)} images -> {args.out}")


if __name__ == "__main__":
    main()