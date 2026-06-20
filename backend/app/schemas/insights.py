import re
import unicodedata

from pydantic import BaseModel, Field


class InsightsWidget(BaseModel):
    title: str
    enabled: bool = True


class TradingViewNewsSettings(BaseModel):
    feed_mode: str = "all_symbols"
    display_mode: str = "regular"
    color_theme: str = "dark"
    locale: str = "en"
    is_transparent: bool = True


class TradingViewEventsSettings(BaseModel):
    color_theme: str = "dark"
    locale: str = "en"
    is_transparent: bool = True
    importance_filter: str = "0,1"
    country_filter: str = "us,eu,gb,jp,cn,za,ng,ke"


class ResearchArticle(BaseModel):
    slug: str
    title: str
    excerpt: str = ""
    url: str = ""
    published_at: str = ""
    enabled: bool = True


class InsightsContent(BaseModel):
    eyebrow: str
    title_before: str
    title_highlight: str
    news: InsightsWidget
    economic_calendar: InsightsWidget
    news_settings: TradingViewNewsSettings
    events_settings: TradingViewEventsSettings
    research_articles: list[ResearchArticle] = Field(default_factory=list)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug or "article"
