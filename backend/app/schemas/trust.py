from typing import Literal, Union

from pydantic import BaseModel, Field


class CounterTrustStat(BaseModel):
    type: Literal["counter"] = "counter"
    value: int
    suffix: str = ""
    label: str


class TextTrustStat(BaseModel):
    type: Literal["text"] = "text"
    title: str
    label: str


TrustStat = Union[CounterTrustStat, TextTrustStat]


class TrustContent(BaseModel):
    stats: list[TrustStat] = Field(min_length=4, max_length=4)
    note_before: str
    countries: str
    note_after: str
