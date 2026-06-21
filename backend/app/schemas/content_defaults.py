from pathlib import Path

from app.core.content_storage import DATA_DIR, load_json_model
from app.schemas.about import AboutContent
from app.schemas.blog import BlogStore
from app.schemas.calculator import CalculatorContent
from app.schemas.clients import ClientsContent
from app.schemas.contact import ContactContent
from app.schemas.coverage import CoverageContent
from app.schemas.hero import HeroContent
from app.schemas.insights import InsightsContent
from app.schemas.markets import MarketsContent
from app.schemas.membership import MembershipContent
from app.schemas.philosophy import PhilosophyContent
from app.schemas.services import ServicesContent
from app.schemas.trust import TrustContent


def _from_json(filename: str, model: type):
    loaded = load_json_model(DATA_DIR / filename, model)
    if loaded is not None:
        return loaded
    raise RuntimeError(f"Missing default content file: {filename}")


def default_hero() -> HeroContent:
    return _from_json("hero.json", HeroContent)


def default_trust() -> TrustContent:
    return _from_json("trust.json", TrustContent)


def default_about() -> AboutContent:
    return _from_json("about.json", AboutContent)


def default_philosophy() -> PhilosophyContent:
    return _from_json("philosophy.json", PhilosophyContent)


def default_services() -> ServicesContent:
    return _from_json("services.json", ServicesContent)


def default_markets() -> MarketsContent:
    return _from_json("markets.json", MarketsContent)


def default_calculator() -> CalculatorContent:
    return _from_json("calculator.json", CalculatorContent)


def default_insights() -> InsightsContent:
    return _from_json("insights.json", InsightsContent)


def default_coverage() -> CoverageContent:
    return _from_json("coverage.json", CoverageContent)


def default_clients() -> ClientsContent:
    return _from_json("clients.json", ClientsContent)


def default_contact() -> ContactContent:
    return _from_json("contact.json", ContactContent)


def default_membership() -> MembershipContent:
    return _from_json("membership.json", MembershipContent)


def default_blog_store() -> BlogStore:
    loaded = load_json_model(DATA_DIR / "blog.json", BlogStore)
    return loaded if loaded is not None else BlogStore()


def default_ai_banner() -> dict:
    from app.core.content_storage import load_raw_json

    return load_raw_json(DATA_DIR / "ai_banner.json", default={}) or {}


def default_partner() -> dict:
    from app.core.content_storage import load_raw_json

    return load_raw_json(DATA_DIR / "partner.json", default={}) or {}
