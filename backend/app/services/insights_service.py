import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_cms_content
from app.database import SessionLocal
from app.models.insights import InsightsSection
from app.schemas.content_defaults import default_insights
from app.schemas.insights import InsightsContent, ResearchArticle, slugify

BASE_DIR = Path(__file__).resolve().parent.parent
INSIGHTS_FILE = BASE_DIR / "data" / "insights.json"
INSIGHTS_SLUG = "homepage"


def _load_insights_from_db(db: Session) -> InsightsContent | None:
    row = db.query(InsightsSection).filter(InsightsSection.slug == INSIGHTS_SLUG).one_or_none()
    if row is None:
        return None
    return InsightsContent.model_validate(row.content)


def _save_insights_to_json(insights: InsightsContent) -> InsightsContent:
    INSIGHTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with INSIGHTS_FILE.open("w", encoding="utf-8") as f:
        json.dump(insights.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return insights


def _save_insights_to_db(db: Session, insights: InsightsContent) -> InsightsContent:
    row = db.query(InsightsSection).filter(InsightsSection.slug == INSIGHTS_SLUG).one_or_none()
    payload = insights.model_dump()
    if row is None:
        row = InsightsSection(slug=INSIGHTS_SLUG, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return InsightsContent.model_validate(row.content)


def load_insights() -> InsightsContent:
    return load_cms_content(
        model=InsightsContent,
        json_path=INSIGHTS_FILE,
        db_loader=_load_insights_from_db,
        default_factory=default_insights,
    )


def save_insights(insights: InsightsContent) -> InsightsContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_insights_to_db(db, insights)
        finally:
            db.close()
    return _save_insights_to_json(insights)


def get_research_article(slug: str) -> ResearchArticle | None:
    insights = load_insights()
    for article in insights.research_articles:
        if article.slug == slug:
            return article
    return None


def _unique_slug(base: str, existing: set[str]) -> str:
    slug = slugify(base)
    if slug not in existing:
        return slug
    index = 2
    while f"{slug}-{index}" in existing:
        index += 1
    return f"{slug}-{index}"


def add_research_article(article: ResearchArticle) -> ResearchArticle:
    insights = load_insights()
    existing = {item.slug for item in insights.research_articles}
    if article.slug in existing:
        article = article.model_copy(update={"slug": _unique_slug(article.title, existing)})
    insights.research_articles.append(article)
    save_insights(insights)
    return article


def update_research_article(slug: str, article: ResearchArticle) -> ResearchArticle:
    insights = load_insights()
    updated_articles: list[ResearchArticle] = []
    found = False
    for item in insights.research_articles:
        if item.slug == slug:
            updated_articles.append(article)
            found = True
        else:
            updated_articles.append(item)
    if not found:
        raise KeyError(slug)
    save_insights(insights.model_copy(update={"research_articles": updated_articles}))
    return article


def delete_research_article(slug: str) -> None:
    insights = load_insights()
    filtered = [item for item in insights.research_articles if item.slug != slug]
    if len(filtered) == len(insights.research_articles):
        raise KeyError(slug)
    save_insights(insights.model_copy(update={"research_articles": filtered}))
