from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import auth
import user
import partner_request
from fastapi.templating import Jinja2Templates
from chat import socket_app

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/avatars", StaticFiles(directory="profile-images"), name="profile_images")

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(partner_request.router)
app.mount("/chatserver", socket_app)


@app.get("/app1")
async def index(request: Request):
    return templates.TemplateResponse("app.html", {"request": request})


@app.get("/app2")
async def index(request: Request):
    return templates.TemplateResponse("app.html", {"request": request})
