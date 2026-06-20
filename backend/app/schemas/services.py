from pydantic import BaseModel, Field


class ServiceCard(BaseModel):
    slug: str
    icon: str
    title: str
    description: str


class ServicesContent(BaseModel):
    eyebrow: str
    title_before: str
    title_highlight: str
    cards: list[ServiceCard] = Field(min_length=6, max_length=6)


SERVICE_SLUGS = (
    "portfolio-management",
    "institutional-advisory",
    "wealth-consulting",
    "market-intelligence",
    "risk-management",
    "financial-education",
)

SERVICE_LABELS = {
    "portfolio-management": "Portfolio Management",
    "institutional-advisory": "Institutional Advisory",
    "wealth-consulting": "Wealth Consulting",
    "market-intelligence": "Market Intelligence",
    "risk-management": "Risk Management Frameworks",
    "financial-education": "Financial Education",
}
