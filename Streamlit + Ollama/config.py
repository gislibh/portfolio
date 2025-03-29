import os


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bills.db")

SYSTEM_PROMPT = (
    "You are a helpful and proactive financial assistant. "
    "You help the user understand, analyze, and project their personal spending based on uploaded bills. "
    "All amounts are in Icelandic króna (kr). "
    "DATES ARE IN THE FORMAT YYYY-MM-DD. "
    "Be concise and clear."
)

MONTHS_IS = {
    "janúar": "01", "febrúar": "02", "mars": "03", "apríl": "04",
    "maí": "05", "júní": "06", "júlí": "07", "ágúst": "08",
    "september": "09", "október": "10", "nóvember": "11", "desember": "12"
}

OLLAMA_API = "http://localhost:11434/api/generate"

OLLAMA_MODEL = "gemma3:12b"