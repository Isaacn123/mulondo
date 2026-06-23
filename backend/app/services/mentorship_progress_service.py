from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.mentee_progress import MenteeModuleProgress


def module_key(stage_index: int, module_index: int) -> str:
    return f"{stage_index}-{module_index}"


def parse_module_key(key: str) -> tuple[int, int] | None:
    parts = key.split("-", 1)
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def get_progress(db: Session, user_id: int, key: str) -> MenteeModuleProgress | None:
    return (
        db.query(MenteeModuleProgress)
        .filter(MenteeModuleProgress.user_id == user_id, MenteeModuleProgress.module_key == key)
        .one_or_none()
    )


def list_progress_for_user(db: Session, user_id: int) -> dict[str, MenteeModuleProgress]:
    rows = db.query(MenteeModuleProgress).filter(MenteeModuleProgress.user_id == user_id).all()
    return {row.module_key: row for row in rows}


def mark_reading_complete(db: Session, user_id: int, key: str) -> MenteeModuleProgress:
    row = get_progress(db, user_id, key)
    if row is None:
        row = MenteeModuleProgress(
            user_id=user_id,
            module_key=key,
            reading_completed=True,
            quiz_passed=False,
            quiz_score_percent=0,
            points_awarded=0,
        )
        db.add(row)
    else:
        row.reading_completed = True
    db.commit()
    db.refresh(row)
    return row


def record_quiz_attempt(
    db: Session,
    user_id: int,
    key: str,
    *,
    score_percent: int,
    passed: bool,
    award_points: int,
) -> MenteeModuleProgress:
    row = get_progress(db, user_id, key)
    if row is None:
        row = MenteeModuleProgress(
            user_id=user_id,
            module_key=key,
            reading_completed=True,
            quiz_passed=passed,
            quiz_score_percent=score_percent,
            points_awarded=award_points if passed else 0,
            completed_at=datetime.now(timezone.utc) if passed else None,
        )
        db.add(row)
    else:
        row.reading_completed = True
        if passed and not row.quiz_passed:
            row.quiz_passed = True
            row.points_awarded = award_points
            row.completed_at = datetime.now(timezone.utc)
        row.quiz_score_percent = max(row.quiz_score_percent, score_percent)
    db.commit()
    db.refresh(row)
    return row


def total_points(db: Session, user_id: int) -> int:
    rows = db.query(MenteeModuleProgress).filter(MenteeModuleProgress.user_id == user_id).all()
    return sum(row.points_awarded for row in rows)


def completed_module_count(db: Session, user_id: int) -> int:
    return (
        db.query(MenteeModuleProgress)
        .filter(MenteeModuleProgress.user_id == user_id, MenteeModuleProgress.quiz_passed.is_(True))
        .count()
    )
