import os
import json
import re
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "llama3-70b-8192"  # Added constant model name

def log_to_file(filename: str, content: str):
    with open(filename, "a") as f:
        f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}]\n{content.strip()}\n")

def classify_query_with_llm(history: list, current_message: str) -> str:
    prompt = (
        "Classify this customer message into Technical, Feature, or Sales. "
        "please be critical when differentiating between feature or sales user may be ambigious about what they are asking\n"
        "Consider conversation context:\n"
        "Conversation History:\n"
    )
    
    for msg in history[-3:]:
        role = "Customer" if msg["role"] == "user" else "Agent"
        prompt += f"{role}: {msg['content']}\n"
    
    prompt += f"Current Message: {current_message}\nClassification:"
    
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=20,
    )
    return completion.choices[0].message.content.strip()

def get_technical_response(history: list, kb_docs: list) -> str:
    context = "\n".join(
        f"{msg['role'].capitalize()}: {msg['content']}" 
        for msg in history[-4:]
    )
    
    docs_str = "\n".join(kb_docs[:3])
    
    prompt = (
        f"Conversation Context:\n{context}\n\n"
        f"Knowledge Base Snippets:\n{docs_str}\n\n"
        "Generate a helpful response that:\n"
        "1. Thanks the customer\n"
        "2. Summarizes the issue\n"
        "3. Provides relevant solution from KB\n"
        "4. Asks if this resolves their issue"
    )
    
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=1024,
    )
    return completion.choices[0].message.content.strip()

def should_escalate_by_sentiment(message: str) -> bool:
    prompt = (
        "Determine if this message expresses VERY NEGATIVE sentiment "
        "(anger, frustration, urgency) requiring human escalation. "
        "Reply ONLY with 'YES' or 'NO':\n"
        f"Message: {message}"
    )
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=5,
    )
    return "YES" in response.choices[0].message.content.strip().upper()

def is_complex_sales_inquiry(message: str) -> bool:
    prompt = (
        "Is this sales inquiry complex? (e.g., enterprise solution, "
        "custom pricing, integration needs). Reply ONLY 'YES' or 'NO':\n"
        f"Message: {message}"
    )
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=5,
    )
    return "YES" in response.choices[0].message.content.strip().upper()

def extract_sales_fields(message: str) -> dict:
    system_prompt = """
You are an AI assistant helping to extract structured fields from a customer's message. 
Always return a JSON object with the keys: name, company, team_size, sales_query.
If a value is not mentioned, leave it as an empty string.
Examples:
1. User: "Hi, I'm John from Acme Inc with 10 people. We need sales info"
   Output: {"name": "John", "company": "Acme Inc", "team_size": "10", "sales_query": "We need sales info"}
2. User: "Anmol"
   Output: {"name": "Anmol", "company": "", "team_size": "", "sales_query": ""}
3. User: "My company is Google"
   Output: {"name": "", "company": "Google", "team_size": "", "sales_query": ""}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return {
            "name": data.get("name", "").strip(),
            "company": data.get("company", "").strip(),
            "team_size": data.get("team_size", "").strip(),
            "sales_query": data.get("sales_query", "").strip()
        }
    except json.JSONDecodeError:
        # Fallback to simple extraction
        return {
            "name": message if message.strip().isalpha() else "",
            "company": "",
            "team_size": "",
            "sales_query": message
        }
    except Exception as e:
        print(f"[extract_sales_fields] Error: {str(e)}")
        return {"name": "", "company": "", "team_size": "", "sales_query": ""}

def session_should_end(message: str) -> bool:
    end_phrases = [
        "thank you", "thanks", "got it", "okay", "that's all", 
        "no more", "appreciate it", "done", "resolved"
    ]
    return any(phrase in message.lower() for phrase in end_phrases)