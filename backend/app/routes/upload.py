from fastapi import APIRouter, File, Query, UploadFile

from app.services import r2_service

admin_router = APIRouter(prefix="/admin", tags=["upload"])


@admin_router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    folder: str = Query("cms"),
):
    url = await r2_service.upload_image(file, folder=folder)
    return {"ok": True, "url": url}


@admin_router.post("/upload/media")
async def upload_media(file: UploadFile = File(...)):
    url, media_type = await r2_service.upload_article_media(file)
    return {"ok": True, "url": url, "media_type": media_type}


@admin_router.post("/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    folder: str = Query("mentorship"),
):
    url, file_name, size_bytes = await r2_service.upload_document(file, folder=folder)
    return {"ok": True, "url": url, "file_name": file_name, "file_size_bytes": size_bytes}
