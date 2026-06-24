from pydantic import BaseModel, Field


class CredentialItem(BaseModel):
    key: str
    enabled: bool = True
    credential_name: str
    issuer_name: str
    issuer_logo_url: str = ""
    status: str = ""
    year: str = ""
    description: str = ""
    verify_url: str = ""
    verify_label: str = "Verify credential"
    sort_order: int = 0


class CredentialsContent(BaseModel):
    eyebrow: str = "Professional Accreditation"
    title_before: str = "Credentials &"
    title_highlight: str = "Recognition"
    intro: str = (
        "Verified professional qualifications — issuer details and links below, "
        "not certificate scans."
    )
    footnote: str = "Full certificates available on request for due diligence."
    credentials: list[CredentialItem] = Field(default_factory=list)
