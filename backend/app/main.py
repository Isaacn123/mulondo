from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import get_settings
from app.routes import admin, blog, calculator, clients, contact, coverage, dashboard, homepage, insights, market_data, markets, services

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
settings = get_settings()


app = FastAPI(root_path="/admin") # adding "/admin" for nginx  routing
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.get("/")
# async def root():
#     return {
#         "users": 1250,
#         "sales": 5200,
#         "orders": 184
#     }

app.include_router(dashboard.router)
app.include_router(blog.admin_router)
app.include_router(blog.api_router)
app.include_router(homepage.admin_router)
app.include_router(homepage.api_router)
app.include_router(services.admin_router)
app.include_router(services.api_router)
app.include_router(markets.admin_router)
app.include_router(markets.api_router)
app.include_router(calculator.admin_router)
app.include_router(calculator.api_router)
app.include_router(insights.admin_router)
app.include_router(insights.api_router)
app.include_router(coverage.admin_router)
app.include_router(coverage.api_router)
app.include_router(clients.admin_router)
app.include_router(clients.api_router)
app.include_router(contact.admin_router)
app.include_router(contact.bookings_router)
app.include_router(contact.api_router)
app.include_router(market_data.router)
app.include_router(admin.router)
# app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")
