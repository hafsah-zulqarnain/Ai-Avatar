# cloud_storage.py
import io
import datetime
from google.cloud import storage
from PIL import Image
import logging
from config2 import storage_client, bucket_name, bucket


def generate_signed_url(bucket_name, blob_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    expiration = datetime.timedelta(minutes=15)
    
    try:
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration,
            method="GET",
            content_type="image/png"  
        )
        return signed_url
    except Exception as e:
        print(f"Error generating signed URL: {e}")
        return None

def upload_image_to_bucket(user_email, image, job_id):
    
    folder_path = f"{user_email}/"  
    filename = f"{job_id}.png" 
    blob = bucket.blob(folder_path + filename)
    
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')
    image_bytes = image_bytes.getvalue()
    
    blob.upload_from_string(image_bytes, content_type='image/png')
    
    
    signed_url = generate_signed_url(bucket_name, folder_path + filename)
    return signed_url

def fetch_images(job_id, user_email):
    folder_path = f"{user_email}/"
    blobs = bucket.list_blobs(prefix=folder_path)
    images = []
    
    for blob in blobs:
        if blob.name.endswith(f"{job_id}.png"):
            image_url = f"https://storage.googleapis.com/{bucket_name}/{blob.name}"
            print(f"Fetching image from URL: {image_url}")
            
            try:
                image_data = blob.download_as_bytes()
                image = Image.open(io.BytesIO(image_data))
                images.append(image)
            except Exception as e:
                print(f"Failed to fetch image: {e}")
    
    return images