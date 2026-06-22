from pathlib import Path

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.mentorship import MentorshipContent, MentorshipModule, MentorshipStage, MentorshipTopic
from app.services.mentorship_service import load_mentorship, save_mentorship

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["mentorship"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


def _parse_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _parse_topics(value: str) -> list[MentorshipTopic]:
    topics: list[MentorshipTopic] = []
    for line in _parse_lines(value):
        parts = [part.strip() for part in line.split("|")]
        if len(parts) >= 3:
            topics.append(
                MentorshipTopic(
                    topic_area=parts[0],
                    learning_objectives=parts[1],
                    practical_exercise=parts[2],
                )
            )
        elif len(parts) == 2:
            topics.append(
                MentorshipTopic(
                    topic_area=parts[0],
                    learning_objectives=parts[1],
                    practical_exercise="",
                )
            )
        elif parts:
            topics.append(MentorshipTopic(topic_area=parts[0], learning_objectives="", practical_exercise=""))
    return topics


def _topics_to_text(topics: list[MentorshipTopic]) -> str:
    return "\n".join(
        f"{t.topic_area}|{t.learning_objectives}|{t.practical_exercise}" for t in topics
    )


def _parse_stages_from_form(form) -> list[MentorshipStage]:
    stages: list[MentorshipStage] = []
    si = 0
    while f"stage_{si}_title" in form:
        modules: list[MentorshipModule] = []
        mi = 0
        while f"stage_{si}_module_{mi}_title" in form:
            modules.append(
                MentorshipModule(
                    title=form.get(f"stage_{si}_module_{mi}_title", "").strip(),
                    description=form.get(f"stage_{si}_module_{mi}_description", "").strip(),
                    topics=_parse_topics(form.get(f"stage_{si}_module_{mi}_topics", "")),
                )
            )
            mi += 1
        stages.append(
            MentorshipStage(
                title=form.get(f"stage_{si}_title", "").strip(),
                weeks=form.get(f"stage_{si}_weeks", "").strip(),
                description=form.get(f"stage_{si}_description", "").strip(),
                modules=modules,
            )
        )
        si += 1
    return stages


@admin_router.get("/mentorship")
async def mentorship_overview_form(request: Request, saved: bool = Query(False)):
    mentorship = load_mentorship()
    return templates.TemplateResponse(
        request,
        "admin/mentorship/overview.html",
        {
            "page_title": "Mentorship Training",
            "active_nav": "mentorship",
            "active_item": "mentorship-overview",
            "mentorship": mentorship,
            "saved": saved,
        },
    )


@admin_router.post("/mentorship")
async def mentorship_overview_save(
    request: Request,
    title: str = Form(...),
    subtitle: str = Form(""),
    prepared_for: str = Form(""),
    prepared_by: str = Form(""),
    target_audience: str = Form(""),
    curriculum_source: str = Form(""),
    introduction: str = Form(...),
    conclusion: str = Form(""),
    assessment: str = Form(""),
    published: str = Form(""),
):
    mentorship = load_mentorship()
    updated = mentorship.model_copy(
        update={
            "title": title.strip(),
            "subtitle": subtitle.strip(),
            "prepared_for": prepared_for.strip(),
            "prepared_by": prepared_by.strip(),
            "target_audience": target_audience.strip(),
            "curriculum_source": curriculum_source.strip(),
            "introduction": introduction.strip(),
            "conclusion": conclusion.strip(),
            "assessment": assessment.strip(),
            "published": published == "on",
        }
    )
    save_mentorship(updated)
    return RedirectResponse(url="/admin/mentorship?saved=1", status_code=303)


@admin_router.get("/mentorship/curriculum")
async def mentorship_curriculum_form(request: Request, saved: bool = Query(False)):
    mentorship = load_mentorship()
    return templates.TemplateResponse(
        request,
        "admin/mentorship/curriculum.html",
        {
            "page_title": "Mentorship Curriculum",
            "active_nav": "mentorship",
            "active_item": "mentorship-curriculum",
            "mentorship": mentorship,
            "topics_to_text": _topics_to_text,
            "saved": saved,
        },
    )


@admin_router.post("/mentorship/curriculum")
async def mentorship_curriculum_save(request: Request):
    form = await request.form()
    mentorship = load_mentorship()
    stages = _parse_stages_from_form(form)
    updated = mentorship.model_copy(update={"stages": stages})
    save_mentorship(updated)
    return RedirectResponse(url="/admin/mentorship/curriculum?saved=1", status_code=303)


@api_router.get("/mentorship")
async def mentorship_api():
    mentorship = load_mentorship()
    if not mentorship.published:
        return {"published": False}
    return mentorship.model_dump()
