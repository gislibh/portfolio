import fitz
import re
import datetime
import requests
import json
import streamlit as st
from Bill import Bill

from config import SYSTEM_PROMPT, MONTHS_IS, OLLAMA_API, OLLAMA_MODEL

def extract_text_from_pdf(pdf_file):
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    return text

def convert_date(date_str):
    match = re.match(r"(\d{1,2})\.\s*(\w+)\s*(\d{4})", date_str)
    if match:
        day, month_name, year = match.groups()
        month_num = MONTHS_IS.get(month_name.lower())
        if month_num:
            return f"{day.zfill(2)}.{month_num}.{year}"
    return date_str  

def extract_info(text):
    date_pattern = r"(?:Gjalddagi|Dagsetning)\s*:?\s*(\d{1,2}\.\s?\w+\s?\d{4}|\d{2}\.\d{2}\.\d{4})"
    
    amount_patterns = [
        r"Samtals[:\s]*([\d\. ]+)\s*kr\.",  # ON & RVK
        r"Samtals(?:[:\s]| ISK með VSK\s*)([\d\. ]+)(?:\s*kr\.)?"  # Hringdu
    ]
    
    email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"

    date = re.search(date_pattern, text)
    email = re.search(email_pattern, text)
    
    amount = None
    for pattern in amount_patterns:
        match = re.search(pattern, text)
        if match:
            amount = match.group(1).replace(".", "").rstrip()
            break  

    date_str = date.group(1) if date else None
    if date_str:
        date_str = convert_date(date_str)

    return Bill(
        creditor=email.group() if email else "Unknown",
        date=date_str,
        amount=amount
    )

def parse_date(date_str):
    return datetime.datetime.strptime(date_str, "%d.%m.%Y")


def build_full_prompt(messages: list, system_prompt: str = None, custom_system_prompt: str = None) -> str:
    prompt_lines = []
    if custom_system_prompt:
        prompt_lines.append(f"System: {custom_system_prompt}")
    else:
        prompt_lines.append(f"System: {SYSTEM_PROMPT}")
    
    if system_prompt:
        prompt_lines.append(f"(Summary of earlier conversation): {system_prompt}")

    for msg in messages:
        if msg["role"] == "user":
            prompt_lines.append(f"User: {msg['content']}")
        else:
            prompt_lines.append(f"Assistant: {msg['content']}")

    return "\n".join(prompt_lines)



def summarize_history(messages: list) -> str:
    summary = []
    for msg in messages:
        if msg["role"] == "user":
            summary.append(f"User asked about: {msg['content']}")
        elif msg["role"] == "assistant":
            summary.append(f"Assistant replied briefly: {msg['content'][:100]}...")
    return " | ".join(summary)

def ask_ollama(messages: list, injected_prompt="") -> str:
    url = OLLAMA_API

    MAX_TURNS = 12  # Max back-and-forths to keep verbatim
    short_history = messages[-MAX_TURNS:]
    summary = summarize_history(messages[:-MAX_TURNS]) if len(messages) > MAX_TURNS else None

    if injected_prompt:
        combined_system = f"{SYSTEM_PROMPT}\n\n{injected_prompt}"
    else:
        combined_system = SYSTEM_PROMPT

    full_prompt = build_full_prompt(short_history, system_prompt=summary, custom_system_prompt=combined_system)

    payload = {
        "prompt": full_prompt,
        "model": OLLAMA_MODEL,
    }

    response = requests.post(url, json=payload)

    final_text = []
    for line in response.text.splitlines():
        if not line.strip():
            continue
        parsed = json.loads(line)
        final_text.append(parsed.get("response", ""))
        
    return "".join(final_text)

def create_financial_prompt_injection(bills, transactions):
    """
    Creates a prompt injection that includes a summary of bills and transactions.
    
    Parameters:
        bills (list): A list of Bill objects.
        transactions (list): A list of transaction dictionaries (e.g. from Transaction.to_dict()).
    
    Returns:
        str: A string to be injected into the LLM prompt.
    """
    prompt_lines = ["Financial Data Summary:"]
    
    if bills:
        prompt_lines.append("Bills:")
        for bill in bills:
            prompt_lines.append(f"- {bill.creditor}: {int(bill.amount)} kr on {bill.date}")
    else:
        prompt_lines.append("No bills available.")
    
    if transactions:
        prompt_lines.append("\nTransactions:")
        for t in transactions:
            prompt_lines.append(f"- {t['creditor']}: {int(t['amount'])} kr on {t['trans_date']}")
    else:
        prompt_lines.append("No transactions available.")
    
    return "\n".join(prompt_lines)



