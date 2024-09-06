from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import httpx
import os
import base64
import hashlib
from urllib.parse import urlencode
from dotenv import load_dotenv
import gradio as gr
from test_service import create_app
from set_email import set_user_email
load_dotenv()

app = FastAPI()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

interface = create_app()
gr.mount_gradio_app(app, interface, path="/gradio")
def generate_code_verifier():
    return base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('ascii')

def generate_code_challenge(code_verifier):
    sha256 = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(sha256).rstrip(b'=').decode('ascii')


@app.get("/")
async def login(request: Request):
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    request.session['code_verifier'] = code_verifier

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile email",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    auth_url_with_params = f"{auth_url}?{urlencode(params)}"
    return RedirectResponse(url=auth_url_with_params)

@app.get("/oauth2/callback")
async def oauth2_callback(request: Request, code: str):
    code_verifier = request.session.get('code_verifier')

    if not code_verifier:
        raise HTTPException(status_code=400, detail="Code verifier not found")

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=token_data)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch token")

        token_response = response.json()

    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {
        "Authorization": f"Bearer {token_response['access_token']}"
    }

    async with httpx.AsyncClient() as client:
        user_info_response = await client.get(user_info_url, headers=headers)
        if user_info_response.status_code != 200:
            raise HTTPException(status_code=user_info_response.status_code, detail="Failed to fetch user info")

        user_info = user_info_response.json()
        request.session['user_email'] = user_info['email']
        user_email = user_info['email']
        set_user_email(user_email)

        if user_info['email'] not in ALLOWED_USERS:
            return "Access Denied", 403


    return RedirectResponse(url='/gradio')
    
@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user_email', None)
    request.session.pop('code_verifier', None)
    return RedirectResponse(url='/')


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
