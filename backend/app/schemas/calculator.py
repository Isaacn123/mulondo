from pydantic import BaseModel, Field


class CalculatorField(BaseModel):
    label: str
    default: float
    input_min: float | None = None
    input_step: float | None = None
    range_min: float
    range_max: float
    range_step: float
    scale_labels: list[str] = Field(default_factory=list)


class CalculatorContent(BaseModel):
    eyebrow: str
    title_before: str
    title_highlight: str
    intro: str
    initial_capital: CalculatorField
    monthly_contribution: CalculatorField
    investment_horizon: CalculatorField
    annual_rate: CalculatorField
    disclaimer: str
    cta_text: str
    cta_link: str
