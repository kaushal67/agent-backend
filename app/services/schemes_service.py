from typing import List

from sqlalchemy.orm import Session

from app.models import Scheme

DEFAULT_SCHEMES = [
    {
        "name": "PM-KISAN",
        "description": "Income support scheme for farmers.",
        "eligibility": "Small and marginal farmers owning cultivable land.",
        "benefits": "Rs 6000 per year in three installments.",
        "state": "India",
    },
    {
        "name": "PMFBY (Pradhan Mantri Fasal Bima Yojana)",
        "description": "Crop insurance scheme.",
        "eligibility": "Farmers growing notified crops.",
        "benefits": "Insurance coverage for crop losses.",
        "state": "India",
    },
    {
        "name": "Soil Health Card Scheme",
        "description": "Provides soil testing and nutrient advisory.",
        "eligibility": "All farmers.",
        "benefits": "Free soil health reports.",
        "state": "India",
    },
    {
        "name": "Kisan Credit Card (KCC)",
        "description": "Provides credit access to farmers.",
        "eligibility": "Farmers engaged in agriculture.",
        "benefits": "Low-interest agricultural loans.",
        "state": "India",
    },
    {
        "name": "Karnataka Raitha Siri Scheme",
        "description": "Support scheme for farmers in Karnataka.",
        "eligibility": "Registered farmers in Karnataka.",
        "benefits": "State subsidy and financial support.",
        "state": "Karnataka",
    },
]


def _normalize_state(state: str) -> str:
    value = (state or "").strip()
    return value if value else "India"


def _ensure_seeded(db: Session) -> None:
    if db.query(Scheme).count() > 0:
        return

    for row in DEFAULT_SCHEMES:
        db.add(Scheme(**row))
    db.commit()


def get_schemes_by_state(db: Session, state: str) -> List[Scheme]:
    _ensure_seeded(db)
    normalized_state = _normalize_state(state)

    # Prefer user location first.
    matches = db.query(Scheme).filter(Scheme.state.ilike(f"%{normalized_state}%")).all()
    if matches:
        return matches

    # Fallback to national schemes if region-specific data is unavailable.
    if normalized_state.lower() != "india":
        national = db.query(Scheme).filter(Scheme.state.ilike("%India%")).all()
        if national:
            return national

    # Final fallback: return any available entries.
    return db.query(Scheme).all()
