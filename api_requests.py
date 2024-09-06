import requests
import logging
from config2 import API_KEY, db
from image_processing import decode_base64_image
from cloud_storage import upload_image_to_bucket

def create_avatar(payload):
    try:
        response = requests.post(
            "https://api.runpod.ai/v2/iz237h0zn7amu0/run",
            headers={
               "Authorization": f"Bearer {API_KEY}",
               "Content-Type": "application/json"
            },
            json=payload
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

def get_job_status(job_id,user_email):
    url = f"https://api.runpod.ai/v2/iz237h0zn7amu0/status/{job_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"
, "Content-Type": "application/json"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        status = data.get("status")

        user_ref = db.collection('users').document(user_email)
        jobs = user_ref.get().to_dict().get('jobs', [])
        for job in jobs:
            if job['job_id'] == job_id:
                job['status'] = status
        user_ref.update({"jobs": jobs})
        return status
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return f"Request failed: {e}"

def get_job_results(job_id, user_email):
    url = f"https://api.runpod.ai/v2/iz237h0zn7amu0/status/{job_id}"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        status = data.get("status")
        if status == "COMPLETED":
            results = data.get("output", {}).get("images", [])
            result_images = [decode_base64_image(img) for img in results]

            if result_images:
                upload_url = upload_image_to_bucket(user_email, result_images[0], job_id)
                print(f"Image uploaded to: {upload_url}")
            return result_images
        else:
            return ["https://via.placeholder.com/150"]
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return ["https://via.placeholder.com/150"]