from sqlalchemy import MetaData, Table
from app.database.db import SessionLocal

db = SessionLocal()

try:
    crop_diseases = Table("crop_diseases", MetaData(), autoload_with=db.bind)
    table_columns = set(crop_diseases.columns.keys())

    seed_rows = [
        {
            "crop_name": "Tomato",
            "disease_name": "Early Blight",
            "type": "fungal",
            "symptoms": "Dark brown spots on leaves",
            "treatment": "Apply copper fungicide",
            "prevention": "Avoid overhead irrigation",
        },
        {
            "crop_name": "Brinjal",
            "disease_name": "Bacterial Wilt",
            "type": "bacterial",
            "symptoms": "Sudden wilting of plant",
            "treatment": "Remove infected plants",
            "prevention": "Use resistant varieties",
        },
        {
            "crop_name": "Rice",
            "disease_name": "Bacterial Leaf Blight",
            "type": "bacterial",
            "symptoms": "Leaf wilting with yellow to brown drying from tips.",
            "treatment": "Use recommended bactericide and balanced fertilization.",
            "prevention": "Use resistant varieties and avoid excess nitrogen.",
        },
    ]

    rows_to_insert = []
    for row in seed_rows:
        rows_to_insert.append({k: v for k, v in row.items() if k in table_columns})

    db.execute(crop_diseases.insert(), rows_to_insert)
    db.commit()
    print("Diseases seeded successfully.")
finally:
    db.close()
