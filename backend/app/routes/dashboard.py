from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.dashboard_service import chart_payload, get_dashboard_stats

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/admin")
@router.get("/admin/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    stats = get_dashboard_stats(db)
    return templates.TemplateResponse(
        request,
        "dashboard/index.html",
        {
            "stats": stats,
            "chart_payload": chart_payload(stats),
            "active_nav": "dashboard",
            "active_item": "",
            "page_title": "Dashboard",
        },
    )
