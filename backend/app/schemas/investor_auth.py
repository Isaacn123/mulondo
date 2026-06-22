from pydantic import BaseModel, EmailStr, Field


class InvestorRegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class InvestorLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    ok: bool = True
    message: str = ""
    redirect: str = "/investors/"


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
