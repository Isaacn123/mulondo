"""Rename legacy 'Sign into Moodle' navigation labels in cms_documents.

Run once on production after deploy:

    docker compose exec backend python -m app.scripts.patch_navigation_moodle_label
"""
from __future__ import annotations

from app.database import SessionLocal
from app.models.cms_document import CmsDocument

MOODLE_LOGIN = {
    "key": "moodle-login",
    "label": "Sign In to AISkills",
    "href": "/moodle/login",
    "enabled": True,
    "show_in_header": True,
    "show_in_footer": True,
    "sort_order": 24,
    "style": "link",
}


def patch() -> None:
    db = SessionLocal()
    try:
        row = db.query(CmsDocument).filter(CmsDocument.slug == "navigation").one_or_none()
        if row is None:
            print("No navigation document in cms_documents.")
            return

        content = dict(row.content)
        links: list[dict] = list(content.get("links") or [])
        changed = False
        has_moodle_login = False

        for link in links:
            label = str(link.get("label") or "")
            href = str(link.get("href") or "")
            if link.get("key") == "moodle-login":
                has_moodle_login = True
            if "sign" in label.lower() and "moodle" in label.lower():
                link["label"] = "Sign In to AISkills"
                link["href"] = "/moodle/login"
                link["key"] = "moodle-login"
                link["enabled"] = True
                link["show_in_header"] = True
                link["show_in_footer"] = True
                link.setdefault("sort_order", 24)
                link.setdefault("style", "link")
                has_moodle_login = True
                changed = True
            if link.get("key") == "moodle" and href in ("#moodle", "/#moodle"):
                if str(link.get("label") or "").strip().lower() == "moodle":
                    link["label"] = "AISkills"
                    changed = True
            elif link.get("key") == "moodle" and href == "/moodle/login":
                link["label"] = "Sign In to AISkills"
                link["key"] = "moodle-login"
                changed = True
                has_moodle_login = True

        if not has_moodle_login:
            links.append(dict(MOODLE_LOGIN))
            changed = True

        if not changed:
            print("Navigation already uses AISkills sign-in labels.")
            return

        content["links"] = links
        row.content = content
        db.commit()
        print("Updated navigation: Sign In to AISkills (header + footer).")
    finally:
        db.close()


def main() -> None:
    patch()


if __name__ == "__main__":
    main()
