import base64
from io import BytesIO
import io
from PIL import Image
import logging


def process_images(images):
    base64_images = []
    for image_bytes in images:
        base64_image = encode_image(image_bytes)
        if base64_image:
            base64_images.append(base64_image)
    return base64_images


def decode_base64_image(base64_string):
    try:
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        return image
    except Exception as e:
        print(f"Failed to decode base64 image: {e}")
        return None
    
def encode_image(controlnet_image):
    try:
        if controlnet_image is None:
            raise ValueError("No image provided.")
        
        if isinstance(controlnet_image, (bytes, bytearray)):
            try:
                image = Image.open(io.BytesIO(controlnet_image))
                if image.mode != 'RGBA':
                    image = image.convert('RGBA') 
            except Exception as e:
                print(f"Error opening image from binary data: {e}")
                return None
        
        elif hasattr(controlnet_image, 'read'):
            try:
                image = Image.open(controlnet_image)
                if image.mode != 'RGBA':
                    image = image.convert('RGBA') 
            except Exception as e:
                print(f"Error opening image from file-like object: {e}")
                return None
        
        else:
            raise ValueError("Unsupported image format or missing file attribute")

        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    except Exception as e:
        print(f"Failed to open or encode image: {e}")
        return None
