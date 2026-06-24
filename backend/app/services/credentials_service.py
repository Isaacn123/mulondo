import json
from pathlib import Path

from app.schemas.content_defaults import default_credentials
from app.schemas.credentials import CredentialItem, CredentialsContent

BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = BASE_DIR / "data" / "credentials.json"


def load_credentials() -> CredentialsContent:
    if CREDENTIALS_FILE.is_file():
        try:
            return CredentialsContent.model_validate_json(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            pass
    return default_credentials()


def save_credentials(content: CredentialsContent) -> CredentialsContent:
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CREDENTIALS_FILE.open("w", encoding="utf-8") as handle:
        json.dump(content.model_dump(), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return content


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
