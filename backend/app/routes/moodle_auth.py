from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.moodle_auth import moodle_url
from app.database import get_db
from app.schemas.investor_auth import AuthResponse, InvestorLoginRequest, InvestorRegisterRequest
from app.services import user_service
from app.util.users_utility import verify_password

router = APIRouter(prefix="/api/auth/moodle", tags=["moodle-auth"])


@router.post("/register", response_model=AuthResponse)
async def register_mentee(payload: InvestorRegisterRequest, db: Session = Depends(get_db)):
    if user_service.get_user_by_email(db, str(payload.email).lower()):
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user_service.create_mentee(
        db,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=str(payload.email),
        password=payload.password,
    )
    return AuthResponse(
        message="Account created successfully. You can sign in to Moodle now.",
        redirect=moodle_url("/login"),
    )


@router.post("/login", response_model=AuthResponse)
async def login_mentee(
    request: Request,
    payload: InvestorLoginRequest,
    db: Session = Depends(get_db),
):
    user = user_service.get_user_by_email(db, str(payload.email).lower())
    if not user or user.is_admin or user.portal_role != "mentee":
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.full_name
    request.session["account_type"] = "mentee"

    return AuthResponse(
        message="Signed in successfully.",
        redirect=moodle_url("/"),
    )
