from get import get_user_email
from api_requests import get_job_results, get_job_status
from firestore_helper import fetch_jobs
from cloud_storage import fetch_images

def check_and_show_results(job_ids):
    user_email =get_user_email()
    results = []
    statuses = []
    for job_id in job_ids:
        status = get_job_status(job_id,user_email)
        statuses.append(status)
        if status == "COMPLETED":
            result_images = get_job_results(job_id, user_email)
            results.extend(result_images)
        else:
            results.append("https://via.placeholder.com/150")
    status_df = pd.DataFrame({"Job ID": job_ids, "Status": statuses})
    return status_df, results

def generate_results_display():
    results = display_results()
    
    job_data = [(result['job_id'], result['status']) for result in results]
    
    image_paths = []
    for result in results:
        image_paths.extend(result['images'])  
    
    return job_data, image_paths

def display_results():
    user_email = get_user_email()
    jobs = fetch_jobs(user_email)
    job_results = []
    
    for job in jobs:
        job_id = job['job_id']
        status = job.get('status', 'Unknown')
        images = fetch_images(job_id, user_email)
        job_results.append({
            'job_id': job_id,
            'status': status,
            'images': images
        })
    
    return job_results