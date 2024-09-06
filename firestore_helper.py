from config2 import db

def fetch_jobs(user_email):
    user_ref = db.collection('users').document(user_email)
    user_doc = user_ref.get()
    if user_doc.exists:
        jobs = user_doc.to_dict().get('jobs', [])
        return jobs
    else:
        return []
