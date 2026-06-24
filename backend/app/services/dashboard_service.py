import json
from calendar import month_abbr
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.services import (
    about_service,
    blog_service,
    calculator_service,
    clients_service,
    contact_service,
    coverage_service,
    credentials_service,
    hero_service,
    investor_resource_service,
    insights_service,
    kyc_service,
    markets_service,
    membership_service,
    media_service,
    philosophy_service,
    services_service,
    survey_service,
    trust_service,
    user_service,
)


@dataclass
class SectionStatus:
    name: str
    configured: bool
    admin_url: str


@dataclass
class DashboardStats:
    users_total: int = 0
    users_active: int = 0
    users_admin: int = 0
    investors_total: int = 0
    investors_active: int = 0
    investor_resources_total: int = 0
    investor_resources_published: int = 0
    investor_resources_drafts: int = 0
    kyc_pending: int = 0
    kyc_approved: int = 0
    kyc_rejected: int = 0
    recent_kyc_pending: list = field(default_factory=list)
    blog_total: int = 0
    blog_published: int = 0
    blog_drafts: int = 0
    media_total: int = 0
    media_published: int = 0
    media_drafts: int = 0
    research_articles: int = 0
    service_cards: int = 0
    membership_modules: int = 0
    membership_tiers: int = 0
    cms_sections_total: int = 0
    cms_sections_configured: int = 0
    cms_completion_percent: int = 0
    cms_sections: list[SectionStatus] = field(default_factory=list)
    recent_posts: list = field(default_factory=list)
    recent_media: list = field(default_factory=list)
    recent_investor_resources: list = field(default_factory=list)
    chart_area_labels: list[str] = field(default_factory=list)
    chart_area_data: list[int] = field(default_factory=list)
    chart_pie_labels: list[str] = field(default_factory=list)
    chart_pie_data: list[int] = field(default_factory=list)
    chart_pie_colors: list[str] = field(default_factory=list)


def _parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _monthly_blog_activity(posts) -> tuple[list[str], list[int]]:
    now = datetime.now(timezone.utc)
    months: list[tuple[int, int]] = []
    for offset in range(11, -1, -1):
        month_index = now.month - offset
        year = now.year
        while month_index <= 0:
            month_index += 12
            year -= 1
        months.append((year, month_index))

    counts = Counter()
    for post in posts:
        dt = _parse_dt(post.updated_at) or _parse_dt(post.created_at) or _parse_dt(post.published_at)
        if dt is None:
            continue
        counts[(dt.year, dt.month)] += 1

    labels = [month_abbr[month] for _, month in months]
    data = [counts[key] for key in months]
    return labels, data


def _section(name: str, admin_url: str, loader, check) -> SectionStatus:
    try:
        content = loader()
        configured = bool(check(content))
    except Exception:
        configured = False
    return SectionStatus(name=name, configured=configured, admin_url=admin_url)


def get_dashboard_stats(db: Session) -> DashboardStats:
    users = user_service.list_users(db)
    investors_total, investors_active = user_service.count_investors(db)
    posts = blog_service.list_posts()
    published = [post for post in posts if post.status == "published"]
    drafts = [post for post in posts if post.status == "draft"]

    media_items = []
    media_published_count = 0
    media_drafts_count = 0
    try:
        media_items = media_service.list_items()
        media_published_count = sum(1 for item in media_items if item.status == "published")
        media_drafts_count = sum(1 for item in media_items if item.status == "draft")
    except Exception:
        pass

    investor_resources = []
    investor_resources_published = 0
    investor_resources_drafts = 0
    try:
        investor_resources = investor_resource_service.list_resources()
        investor_resources_published = sum(1 for item in investor_resources if item.status == "published")
        investor_resources_drafts = sum(1 for item in investor_resources if item.status == "draft")
    except Exception:
        pass

    research_count = 0
    try:
        insights = insights_service.load_insights()
        research_count = len([a for a in insights.research_articles if a.title.strip()])
    except Exception:
        pass

    service_count = 0
    try:
        services = services_service.load_services()
        service_count = len(services.cards)
    except Exception:
        pass

    membership_modules = 0
    membership_tiers = 0
    try:
        membership = membership_service.load_membership()
        membership_modules = len(membership.modules)
        membership_tiers = len(membership.tiers)
    except Exception:
        pass

    kyc_counts = {k: 0 for k in ("pending", "approved", "rejected", "draft")}
    recent_kyc_pending = []
    try:
        kyc_counts = kyc_service.count_by_status(db)
        recent_kyc_pending = kyc_service.list_submissions(db, status="pending", limit=5)
    except Exception:
        pass

    cms_sections = [
        _section("Homepage Hero", "/admin/homepage/hero", hero_service.load_hero,
                 lambda c: bool(c.title_before.strip() or c.title_highlight.strip())),
        _section("Trust Stats", "/admin/homepage/trust", trust_service.load_trust,
                 lambda c: bool(c.stats)),
        _section("Money Academy Survey", "/admin/homepage/survey", survey_service.load_survey,
                 lambda c: bool(c.screens)),
        _section("About", "/admin/homepage/about", about_service.load_about,
                 lambda c: bool(c.title_before.strip() or c.title_highlight.strip())),
        _section("Credentials", "/admin/homepage/credentials", credentials_service.load_credentials,
                 lambda c: bool(c.credentials)),
        _section("Philosophy", "/admin/homepage/philosophy", philosophy_service.load_philosophy,
                 lambda c: bool(c.title_before.strip() or c.title_highlight.strip())),
        _section("Services", "/admin/services", services_service.load_services,
                 lambda c: bool(c.cards)),
        _section("Markets", "/admin/markets", markets_service.load_markets,
                 lambda c: bool(c.title_before.strip() or c.title_highlight.strip())),
        _section("Calculator", "/admin/calculator", calculator_service.load_calculator,
                 lambda c: bool(c.title_before.strip() or c.title_highlight.strip())),
        _section("Insights", "/admin/insights", insights_service.load_insights,
                 lambda c: bool(c.title_before.strip() or c.title_highlight.strip())),
        _section("Coverage", "/admin/coverage", coverage_service.load_coverage,
                 lambda c: bool(c.title_before.strip() or c.title_highlight.strip())),
        _section("Clients", "/admin/clients", clients_service.load_clients,
                 lambda c: bool(c.title_before.strip() or c.title_highlight.strip())),
        _section("Contact", "/admin/contact", contact_service.load_contact,
                 lambda c: bool(c.title_before.strip() or c.title_highlight.strip())),
        _section("Membership", "/admin/membership", membership_service.load_membership,
                 lambda c: bool(c.title_before.strip() or c.title_highlight.strip())),
    ]

    configured_count = sum(1 for section in cms_sections if section.configured)
    total_sections = len(cms_sections)
    completion = round((configured_count / total_sections) * 100) if total_sections else 0

    area_labels, area_data = _monthly_blog_activity(posts)

    pie_labels = ["Published Posts", "Draft Posts", "Research Articles", "Service Pages", "Membership Modules"]
    pie_data = [len(published), len(drafts), research_count, service_count, membership_modules]
    pie_colors = ["#4e73df", "#858796", "#1cc88a", "#36b9cc", "#f6c23e"]

    # Drop empty pie slices so the chart stays readable.
    filtered_labels: list[str] = []
    filtered_data: list[int] = []
    filtered_colors: list[str] = []
    for label, value, color in zip(pie_labels, pie_data, pie_colors):
        if value > 0:
            filtered_labels.append(label)
            filtered_data.append(value)
            filtered_colors.append(color)
    if not filtered_labels:
        filtered_labels = ["No content yet"]
        filtered_data = [1]
        filtered_colors = ["#eaecf4"]

    return DashboardStats(
        users_total=len(users),
        users_active=sum(1 for user in users if user.is_active),
        users_admin=sum(1 for user in users if user.is_admin and user.is_active),
        investors_total=investors_total,
        investors_active=investors_active,
        investor_resources_total=len(investor_resources),
        investor_resources_published=investor_resources_published,
        investor_resources_drafts=investor_resources_drafts,
        kyc_pending=kyc_counts.get("pending", 0),
        kyc_approved=kyc_counts.get("approved", 0),
        kyc_rejected=kyc_counts.get("rejected", 0),
        recent_kyc_pending=recent_kyc_pending,
        blog_total=len(posts),
        blog_published=len(published),
        blog_drafts=len(drafts),
        media_total=len(media_items),
        media_published=media_published_count,
        media_drafts=media_drafts_count,
        research_articles=research_count,
        service_cards=service_count,
        membership_modules=membership_modules,
        membership_tiers=membership_tiers,
        cms_sections_total=total_sections,
        cms_sections_configured=configured_count,
        cms_completion_percent=completion,
        cms_sections=cms_sections,
        recent_posts=posts[:5],
        recent_media=media_items[:5],
        recent_investor_resources=investor_resources[:5],
        chart_area_labels=area_labels,
        chart_area_data=area_data,
        chart_pie_labels=filtered_labels,
        chart_pie_data=filtered_data,
        chart_pie_colors=filtered_colors,
    )


def chart_payload(stats: DashboardStats) -> str:
    return json.dumps(
        {
            "areaLabels": stats.chart_area_labels,
            "areaData": stats.chart_area_data,
            "pieLabels": stats.chart_pie_labels,
            "pieData": stats.chart_pie_data,
            "pieColors": stats.chart_pie_colors,
        }
    )
