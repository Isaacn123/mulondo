from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.blog import BlogPost
from app.schemas.insights import slugify
from app.services.blog_service import add_post, delete_post, get_post, list_posts, update_post

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["blog"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


@admin_router.get("/blog")
async def blog_list(request: Request, saved: bool = Query(False), deleted: bool = Query(False)):
    published = list_posts(published_only=True)
    drafts = [post for post in list_posts() if post.status == "draft"]
    return templates.TemplateResponse(
        request,
        "admin/blog/list.html",
        {
            "page_title": "Blog",
            "active_nav": "blog",
            "active_item": "blog",
            "published_posts": published,
            "draft_posts": drafts,
            "saved": saved,
            "deleted": deleted,
        },
    )


@admin_router.get("/blog/new")
async def blog_new_form(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/blog/post_form.html",
        {
            "page_title": "Add Post",
            "active_nav": "blog",
            "active_item": "blog-new",
            "post": None,
            "is_new": True,
        },
    )


@admin_router.post("/blog/new")
async def blog_create(
    request: Request,
    title: str = Form(...),
    excerpt: str = Form(""),
    body: str = Form(""),
    author: str = Form("Daniel Mulondo"),
    published_at: str = Form(""),
    status: str = Form("draft"),
):
    if status not in ("draft", "published"):
        raise HTTPException(status_code=400, detail="Invalid status")
    post = BlogPost(
        slug=slugify(title),
        title=title.strip(),
        excerpt=excerpt.strip(),
        body=body.strip(),
        author=author.strip(),
        published_at=published_at.strip(),
        status=status,  # type: ignore[arg-type]
    )
    add_post(post)
    return RedirectResponse(url="/admin/blog?saved=1", status_code=303)


@admin_router.get("/blog/{slug}")
async def blog_edit_form(request: Request, slug: str, saved: bool = Query(False)):
    post = get_post(slug)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse(
        request,
        "admin/blog/post_form.html",
        {
            "page_title": "Edit Post",
            "active_nav": "blog",
            "active_item": "blog-edit",
            "post": post,
            "is_new": False,
            "saved": saved,
        },
    )


@admin_router.post("/blog/{slug}")
async def blog_update(
    request: Request,
    slug: str,
    title: str = Form(...),
    excerpt: str = Form(""),
    body: str = Form(""),
    author: str = Form("Daniel Mulondo"),
    published_at: str = Form(""),
    status: str = Form("draft"),
):
    if get_post(slug) is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if status not in ("draft", "published"):
        raise HTTPException(status_code=400, detail="Invalid status")
    post = BlogPost(
        slug=slug,
        title=title.strip(),
        excerpt=excerpt.strip(),
        body=body.strip(),
        author=author.strip(),
        published_at=published_at.strip(),
        status=status,  # type: ignore[arg-type]
    )
    update_post(slug, post)
    return RedirectResponse(url=f"/admin/blog/{slug}?saved=1", status_code=303)


@admin_router.post("/blog/{slug}/delete")
async def blog_delete(request: Request, slug: str):
    try:
        delete_post(slug)
    except KeyError:
        raise HTTPException(status_code=404, detail="Post not found")
    return RedirectResponse(url="/admin/blog?deleted=1", status_code=303)


@api_router.get("/blog")
async def blog_api() -> list[BlogPost]:
    return list_posts(published_only=True)


@api_router.get("/blog/{slug}")
async def blog_post_api(slug: str) -> BlogPost:
    post = get_post(slug)
    if post is None or post.status != "published":
        raise HTTPException(status_code=404, detail="Post not found")
    return post
