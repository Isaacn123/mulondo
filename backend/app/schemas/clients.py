from pydantic import BaseModel, Field


class ClientsContent(BaseModel):
    eyebrow: str
    title_before: str
    title_highlight: str
    profiles: list[str] = Field(default_factory=list)
