from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/")
@router.get("/admin")
@router.get("/admin/")
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request,
        "dashboard/index.html",
        {
            "users": 1250,
            "sales": 5200,
            "orders": 184,
            "active_nav": "dashboard",
            "active_item": "",
        },
    )
