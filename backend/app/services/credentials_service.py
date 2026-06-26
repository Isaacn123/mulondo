from pathlib import Path

from app.schemas.content_defaults import default_credentials
from app.schemas.credentials import CredentialItem, CredentialsContent
from app.services import cms_document_service

BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = BASE_DIR / "data" / "credentials.json"
CREDENTIALS_SLUG = "credentials"


def load_credentials() -> CredentialsContent:
    return cms_document_service.load_model(
        slug=CREDENTIALS_SLUG,
        model=CredentialsContent,
        json_path=CREDENTIALS_FILE,
        default_factory=default_credentials,
    )


def save_credentials(content: CredentialsContent) -> CredentialsContent:
    return cms_document_service.save_model(
        slug=CREDENTIALS_SLUG,
        content=content,
        json_path=CREDENTIALS_FILE,
    )


def delete_credentials() -> bool:
    return cms_document_service.delete_document(slug=CREDENTIALS_SLUG, json_path=CREDENTIALS_FILE)


def public_credentials() -> CredentialsContent:
    data = load_credentials()
    visible = [item for item in sorted(data.credentials, key=lambda c: c.sort_order) if item.enabled]
    return data.model_copy(update={"credentials": visible})


def credentials_from_form(form) -> list[CredentialItem]:
    keys = [str(key).strip() for key in form.getlist("credential_key") if str(key).strip()]
    items: list[CredentialItem] = []
    for index, key in enumerate(keys):
        items.append(
            CredentialItem(
                key=key,
                enabled=f"{key}_enabled" in form,
                credential_name=(form.get(f"{key}_credential_name") or "").strip(),
                issuer_name=(form.get(f"{key}_issuer_name") or "").strip(),
                issuer_logo_url=(form.get(f"{key}_issuer_logo_url") or "").strip(),
                status=(form.get(f"{key}_status") or "").strip(),
                year=(form.get(f"{key}_year") or "").strip(),
                description=(form.get(f"{key}_description") or "").strip(),
                verify_url=(form.get(f"{key}_verify_url") or "").strip(),
                verify_label=(form.get(f"{key}_verify_label") or "Verify credential").strip() or "Verify credential",
                sort_order=index,
            )
        )
    return [item for item in items if item.credential_name and item.issuer_name]
