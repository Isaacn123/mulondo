"""Seed content tables from JSON files.

Run after migrations when switching to database storage:
    STORAGE_BACKEND=database python -m app.scripts.seed_content
"""
import json
from pathlib import Path

from app.database import SessionLocal
from app.models.about import AboutSection
from app.models.blog import BlogPostRow
from app.models.calculator import CalculatorSection
from app.models.clients import ClientsSection
from app.models.contact import ContactSection
from app.models.coverage import CoverageSection
from app.models.hero import HeroSection
from app.models.insights import InsightsSection
from app.models.markets import MarketsSection
from app.models.membership import MembershipSection
from app.models.mentorship import MentorshipSection
from app.models.philosophy import PhilosophySection
from app.models.services import ServicesSection
from app.models.trust import TrustSection

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SLUG = "homepage"


def _seed_if_missing(db, model, filename: str) -> None:
    path = DATA_DIR / filename
    if not path.exists() or db.query(model).filter(model.slug == SLUG).first():
        return
    with path.open(encoding="utf-8") as f:
        db.add(model(slug=SLUG, content=json.load(f)))


def _seed_blog_posts(db) -> None:
    path = DATA_DIR / "blog.json"
    if not path.exists() or db.query(BlogPostRow).first():
        return
    with path.open(encoding="utf-8") as f:
        posts = json.load(f).get("posts", [])
    for post in posts:
        db.add(
            BlogPostRow(
                slug=post["slug"],
                title=post["title"],
                excerpt=post.get("excerpt", ""),
                body=post.get("body", ""),
                author=post.get("author", "Daniel Mulondo"),
                published_at=post.get("published_at", ""),
                status=post.get("status", "draft"),
                media_type=post.get("media_type", ""),
                media_url=post.get("media_url", ""),
            )
        )


def seed() -> None:
    db = SessionLocal()
    try:
        _seed_if_missing(db, HeroSection, "hero.json")
        _seed_if_missing(db, TrustSection, "trust.json")
        _seed_if_missing(db, AboutSection, "about.json")
        _seed_if_missing(db, PhilosophySection, "philosophy.json")
        _seed_if_missing(db, ServicesSection, "services.json")
        _seed_if_missing(db, MarketsSection, "markets.json")
        _seed_if_missing(db, CalculatorSection, "calculator.json")
        _seed_if_missing(db, InsightsSection, "insights.json")
        _seed_if_missing(db, CoverageSection, "coverage.json")
        _seed_if_missing(db, ClientsSection, "clients.json")
        _seed_if_missing(db, ContactSection, "contact.json")
        _seed_if_missing(db, MembershipSection, "membership.json")
        _seed_if_missing(db, MentorshipSection, "mentorship.json")
        _seed_blog_posts(db)
        db.commit()
        print("Content seeded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
