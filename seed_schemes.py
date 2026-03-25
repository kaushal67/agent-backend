from app.database.db import SessionLocal
from app.models import Scheme

db = SessionLocal()

schemes_data = [
    {
        "name": "PM-KISAN",
        "description": "Income support scheme for farmers.",
        "eligibility": "Small and marginal farmers owning cultivable land.",
        "benefits": "₹6000 per year in three installments.",
        "state": "India"
    },
    {
        "name": "PMFBY (Pradhan Mantri Fasal Bima Yojana)",
        "description": "Crop insurance scheme.",
        "eligibility": "Farmers growing notified crops.",
        "benefits": "Insurance coverage for crop losses.",
        "state": "India"
    },
    {
        "name": "Karnataka Raitha Siri Scheme",
        "description": "Support scheme for farmers in Karnataka.",
        "eligibility": "Registered farmers in Karnataka.",
        "benefits": "Subsidy and financial support.",
        "state": "Karnataka"
    },
    {
        "name": "Soil Health Card Scheme",
        "description": "Provides soil testing and nutrient advisory.",
        "eligibility": "All farmers.",
        "benefits": "Free soil health reports.",
        "state": "India"
    },
    {
        "name": "Kisan Credit Card (KCC)",
        "description": "Provides credit access to farmers.",
        "eligibility": "Farmers engaged in agriculture.",
        "benefits": "Low-interest loans.",
        "state": "India"
    }
]

for data in schemes_data:
    scheme = Scheme(**data)
    db.add(scheme)

db.commit()
db.close()

print("Schemes seeded successfully.")