"""
modules/complaints/service.py
─────────────────────────────────────────────────────────
Complaint workflow service — business logic layer.

All state lives in ``st.session_state[_STORE_KEY]`` (a list of dicts).
To integrate with Firestore or another DB, replace _get_store() and
_save_store() with real I/O; the public API stays the same.
─────────────────────────────────────────────────────────
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

import streamlit as st

from shared.constants import COMPLAINT_STATUSES
from shared.utils import utc_now_iso

# ─────────────────────────────────────────────────────────────────────────────
# Category list  (imported by other parts of this module)
# ─────────────────────────────────────────────────────────────────────────────
CATEGORIES: list[str] = [
    "Hygiene",
    "Food Quality",
    "Expired Food",
    "Suspected Adulteration",
    "Foreign Object",
    "Packaging",
    "Mislabeling",
    "Other",
]

# ─────────────────────────────────────────────────────────────────────────────
# Internal store helpers  (swap for real DB I/O on integration)
# ─────────────────────────────────────────────────────────────────────────────
_STORE_KEY = "complaints_store"


def _get_store() -> list[dict]:
    """Return the in-memory complaint store, seeding it on first access."""
    if _STORE_KEY not in st.session_state:
        st.session_state[_STORE_KEY] = _seed_data()
    return st.session_state[_STORE_KEY]


def _save_store(store: list[dict]) -> None:
    """Persist the store back to session state (swap for DB write)."""
    st.session_state[_STORE_KEY] = store


def _generate_id() -> str:
    """Generate a unique complaint ID in SSC-YYYYMMDD-XXXXXX format."""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"SSC-{today}-{suffix}"


# ─────────────────────────────────────────────────────────────────────────────
# Seed / mock data  (8 sample complaints spanning all categories & statuses)
# ─────────────────────────────────────────────────────────────────────────────
def _seed_data() -> list[dict]:
    today = date.today()

    def _days_ago(n: int) -> str:
        return str(today - timedelta(days=n))

    return [
        {
            "id": "SSC-20241001-A1B2C3",
            "title": "Cockroach found near food preparation area",
            "description": (
                "Observed live cockroaches near the food preparation area inside a "
                "local restaurant kitchen. The area was visibly dirty and unhygienic. "
                "Staff appeared unaware of the pest infestation."
            ),
            "category": "Hygiene",
            "location": "Mumbai, Maharashtra",
            "incident_date": _days_ago(15),
            "status": "Under Review",
            "submitted_at": utc_now_iso(),
            "submitted_by": "user_demo_1",
            "image_filename": None,
            "admin_notes": "Inspection scheduled for next week.",
            "nlp_predicted": True,
            "nlp_confidence": 0.88,
        },
        {
            "id": "SSC-20241003-D4E5F6",
            "title": "Expired milk sold at neighbourhood grocery store",
            "description": (
                "Purchased a 1-litre milk packet whose best-before date had already "
                "passed by 5 days. The store continues to stock and sell expired dairy "
                "products without any quality check."
            ),
            "category": "Expired Food",
            "location": "Delhi, NCR",
            "incident_date": _days_ago(13),
            "status": "Submitted",
            "submitted_at": utc_now_iso(),
            "submitted_by": "user_demo_2",
            "image_filename": None,
            "admin_notes": "",
            "nlp_predicted": True,
            "nlp_confidence": 0.91,
        },
        {
            "id": "SSC-20241005-G7H8I9",
            "title": "Glass shard found inside sealed biscuit packet",
            "description": (
                "Opened a factory-sealed biscuit packet and discovered a small glass "
                "shard approximately 1 cm in length. The packet seal appeared intact "
                "before opening. This is a serious safety hazard."
            ),
            "category": "Foreign Object",
            "location": "Bengaluru, Karnataka",
            "incident_date": _days_ago(11),
            "status": "Verification Required",
            "submitted_at": utc_now_iso(),
            "submitted_by": "user_demo_3",
            "image_filename": None,
            "admin_notes": "User asked to submit physical evidence at nearest office.",
            "nlp_predicted": True,
            "nlp_confidence": 0.85,
        },
        {
            "id": "SSC-20241007-J0K1L2",
            "title": "Suspected adulterated cooking oil — unusual smell",
            "description": (
                "Cooking oil purchased from a local market appears heavily diluted and "
                "has an unusual chemical smell not present in genuine products. Suspected "
                "adulteration with a non-food substance."
            ),
            "category": "Suspected Adulteration",
            "location": "Jaipur, Rajasthan",
            "incident_date": _days_ago(9),
            "status": "Action / Response",
            "submitted_at": utc_now_iso(),
            "submitted_by": "user_demo_4",
            "image_filename": None,
            "admin_notes": "Sample collected and sent to FSSAI lab for analysis.",
            "nlp_predicted": True,
            "nlp_confidence": 0.79,
        },
        {
            "id": "SSC-20241009-M3N4O5",
            "title": "Peanut allergen not declared on snack packaging label",
            "description": (
                "A popular snack product does not mention peanuts in its ingredients "
                "list, yet the product clearly contains them. This is a critical "
                "mislabeling issue that could endanger allergy sufferers."
            ),
            "category": "Mislabeling",
            "location": "Chennai, Tamil Nadu",
            "incident_date": _days_ago(7),
            "status": "Closed",
            "submitted_at": utc_now_iso(),
            "submitted_by": "user_demo_5",
            "image_filename": None,
            "admin_notes": "Manufacturer notified. Partial label recall initiated by retailer.",
            "nlp_predicted": True,
            "nlp_confidence": 0.83,
        },
        {
            "id": "SSC-20241011-P6Q7R8",
            "title": "Fruit juice bottle with broken seal and leaking cap",
            "description": (
                "Purchased a 500 ml fruit juice bottle whose tamper-evident seal was "
                "already broken. The cap was leaking from the side. The damaged "
                "packaging may indicate tampering or faulty manufacturing."
            ),
            "category": "Packaging",
            "location": "Pune, Maharashtra",
            "incident_date": _days_ago(5),
            "status": "Submitted",
            "submitted_at": utc_now_iso(),
            "submitted_by": "user_demo_6",
            "image_filename": None,
            "admin_notes": "",
            "nlp_predicted": True,
            "nlp_confidence": 0.76,
        },
        {
            "id": "SSC-20241013-S9T0U1",
            "title": "Stale bread with visible mould sold at bakery",
            "description": (
                "Bread purchased from a popular bakery chain tasted stale and had "
                "visible green mould on the inside after slicing. Poor quality control "
                "and inadequate freshness checks are evident."
            ),
            "category": "Food Quality",
            "location": "Hyderabad, Telangana",
            "incident_date": _days_ago(3),
            "status": "Under Review",
            "submitted_at": utc_now_iso(),
            "submitted_by": "user_demo_7",
            "image_filename": None,
            "admin_notes": "",
            "nlp_predicted": True,
            "nlp_confidence": 0.72,
        },
        {
            "id": "SSC-20241015-V2W3X4",
            "title": "Unidentified dark substance found in canned vegetables",
            "description": (
                "Opened a can of mixed vegetables and found a dark, unidentified "
                "solid substance at the bottom. The substance was not present on "
                "the label ingredients list. Origin is unclear."
            ),
            "category": "Other",
            "location": "Kolkata, West Bengal",
            "incident_date": _days_ago(1),
            "status": "Submitted",
            "submitted_at": utc_now_iso(),
            "submitted_by": "user_demo_8",
            "image_filename": None,
            "admin_notes": "",
            "nlp_predicted": False,
            "nlp_confidence": 0.0,
        },
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_all_complaints() -> list[dict]:
    """
    Return all complaints.
    Integration note: replace with a Firestore / DB query.
    """
    return list(_get_store())


def get_complaint_by_id(complaint_id: str) -> dict | None:
    """Return a single complaint dict by ID, or None if not found."""
    for c in _get_store():
        if c["id"] == complaint_id:
            return c
    return None


def submit_complaint(
    title: str,
    description: str,
    category: str,
    location: str,
    incident_date: date,
    image_filename: str | None = None,
    image_bytes: bytes | None = None,   # kept for future Storage integration
    nlp_predicted: bool = False,
    nlp_confidence: float = 0.0,
    submitted_by: str = "anonymous",
) -> dict:
    """
    Create and persist a new complaint.

    Returns the saved complaint dict including the generated ID.
    Integration note: replace _save_store() with a Firestore write.
    The ``image_bytes`` parameter is accepted but not stored in-memory;
    it is ready to be uploaded to Firebase Storage on integration.
    """
    store = _get_store()
    new_complaint: dict[str, Any] = {
        "id": _generate_id(),
        "title": title.strip(),
        "description": description.strip(),
        "category": category,
        "location": location.strip(),
        "incident_date": str(incident_date),
        "status": COMPLAINT_STATUSES[0],   # "Submitted"
        "submitted_at": utc_now_iso(),
        "submitted_by": submitted_by,
        "image_filename": image_filename,
        "admin_notes": "",
        "nlp_predicted": nlp_predicted,
        "nlp_confidence": nlp_confidence,
    }
    store.append(new_complaint)
    _save_store(store)
    return new_complaint


def update_complaint_status(
    complaint_id: str,
    new_status: str,
    admin_notes: str = "",
) -> bool:
    """
    Update the status (and optionally admin notes) of an existing complaint.

    Returns True if the complaint was found and updated, False otherwise.
    """
    if new_status not in COMPLAINT_STATUSES:
        return False
    store = _get_store()
    for c in store:
        if c["id"] == complaint_id:
            c["status"] = new_status
            if admin_notes.strip():
                c["admin_notes"] = admin_notes.strip()
            _save_store(store)
            return True
    return False


def get_stats() -> dict:
    """
    Return aggregate complaint statistics for the dashboard.

    Keys returned:
      total       : int
      open        : int  (all statuses except Closed)
      by_status   : dict[str, int]
      by_category : dict[str, int]
    """
    store = _get_store()
    by_status: dict[str, int] = {s: 0 for s in COMPLAINT_STATUSES}
    by_category: dict[str, int] = {cat: 0 for cat in CATEGORIES}

    for c in store:
        s = c.get("status", COMPLAINT_STATUSES[0])
        cat = c.get("category", "Other")
        if s in by_status:
            by_status[s] += 1
        if cat in by_category:
            by_category[cat] += 1

    return {
        "total": len(store),
        "open": sum(v for k, v in by_status.items() if k != "Closed"),
        "by_status": by_status,
        "by_category": by_category,
    }