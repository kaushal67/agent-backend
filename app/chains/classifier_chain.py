# app/chains/classifier_chain.py

import os, json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0
)

prompt = PromptTemplate(
    input_variables=["text"],
    template="""
You are an agricultural query classifier.

Classify the farmer query strictly into one of these intents:

1. weather → if the question is about temperature, rainfall, humidity, climate impact, forecast, or weather effects on crops.
2. crop_problem → if asking about diseases, pests, symptoms, damage, treatment, or prevention.
3. irrigation → if asking about watering methods or water management.
4. subsidy → if asking about government schemes or financial support.

Examples:
- "How is weather affecting tomato crop?" → weather
- "My tomato leaves have brown spots" → crop_problem
- "How much water does rice need?" → irrigation
- "What subsidy is available for farmers?" → subsidy

Message: {text}

Return ONLY valid JSON in this format:
{{
  "intent": "...",
  "urgency": "low/medium/high"
}}
"""
)

def classify(text: str):
    chain = prompt | llm
    response = chain.invoke({"text": text})

    content = response.content.strip()
    content = content.replace("```json", "").replace("```", "")

    try:
        return json.loads(content)
    except Exception:
        return {"error": "Invalid JSON", "raw": content}
