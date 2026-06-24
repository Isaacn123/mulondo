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
    from app.services import user_service

    stats = get_dashboard_stats(db)
    kyc_user_map = {u.id: u for u in user_service.list_users(db)}
    return templates.TemplateResponse(
        request,
        "dashboard/index.html",
        {
            "stats": stats,
            "chart_payload": chart_payload(stats),
            "kyc_user_map": kyc_user_map,
            "active_nav": "dashboard",
            "active_item": "",
            "page_title": "Dashboard",
        },
    )
