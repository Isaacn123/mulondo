from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.portal_auth import portal_url
from app.database import get_db
from app.schemas.investor_auth import AuthResponse, InvestorLoginRequest, InvestorRegisterRequest
from app.services import user_service
from app.util.users_utility import verify_password

router = APIRouter(prefix="/api/auth", tags=["investor-auth"])


@router.post("/register", response_model=AuthResponse)
async def register_investor(payload: InvestorRegisterRequest, db: Session = Depends(get_db)):
    if user_service.get_user_by_email(db, str(payload.email).lower()):
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user_service.create_investor(
        db,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=str(payload.email),
        password=payload.password,
    )
    return AuthResponse(
        message="Account created successfully. You can sign in now.",
        redirect="/investors/login",
    )


@router.post("/login", response_model=AuthResponse)
async def login_investor(
    request: Request,
    payload: InvestorLoginRequest,
    db: Session = Depends(get_db),
):
    user = user_service.get_user_by_email(db, str(payload.email).lower())
    if not user or user.is_admin or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.full_name
    request.session["account_type"] = "investor"

    return AuthResponse(
        message="Signed in successfully.",
        redirect=portal_url("/"),
    )
