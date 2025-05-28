from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import defaultdict
import os
from kb_manager import load_kb_and_embed, search_kb
from utils import (
    classify_query_with_llm, get_technical_response, 
    log_to_file, should_escalate_by_sentiment, 
    extract_sales_fields, is_complex_sales_inquiry,
    session_should_end
)

BASE_DIR = os.path.dirname(__file__)
FEATURES_FILE = os.path.join(BASE_DIR, "features.txt")
SALES_FILE = os.path.join(BASE_DIR, "sales_req.txt")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize knowledge base
load_kb_and_embed()

# Session stores
session_store = defaultdict(list)  # Full conversation history
sales_progress = defaultdict(dict) # Sales state machine
tech_progress = defaultdict(dict)  # Technical issue resolution state
feature_progress = defaultdict(dict)  # Feature request state

class QueryInput(BaseModel):
    session_id: str
    message: str

def update_session(session_id: str, role: str, content: str):
    session_store[session_id].append({"role": role, "content": content})

def reset_flow(session_id: str, flow_type: str):
    if flow_type == "sales":
        sales_progress.pop(session_id, None)
    elif flow_type == "tech":
        tech_progress.pop(session_id, None)
    elif flow_type == "feature":
        feature_progress.pop(session_id, None)
    elif flow_type == "all":
        sales_progress.pop(session_id, None)
        tech_progress.pop(session_id, None)
        feature_progress.pop(session_id, None)

@app.post("/chat/")
async def chat(query: QueryInput):
    session_id = query.session_id
    user_message = query.message.strip()
    
    # Update session with user message
    update_session(session_id, "user", user_message)
    
    # Check for session termination phrases
    if session_should_end(user_message):
        response = "You're welcome! If you need further assistance, feel free to reach out. Have a great day!"
        update_session(session_id, "assistant", response)
        reset_flow(session_id, "all")
        return {"response": response}
    
    # Global escalation check (negative sentiment)
    if should_escalate_by_sentiment(user_message):
        response = "We're sorry you're having difficulties. We've escalated your issue to a human agent who will contact you shortly."
        update_session(session_id, "assistant", response)
        return {"response": response}
    
    # Check existing flows first
    if session_id in tech_progress:
        return handle_technical_flow(session_id, user_message)
    elif session_id in sales_progress:
        return handle_sales_flow(session_id, user_message)
    elif session_id in feature_progress:
        return handle_feature_flow(session_id, user_message)
    
    # Classify new inquiry
    classification = classify_query_with_llm(
        session_store[session_id],
        user_message
    )
    
    if "Technical" in classification:
        return handle_technical_flow(session_id, user_message, new_issue=True)
    elif "Feature" in classification:
        return handle_feature_flow(session_id, user_message, new_request=True)
    elif "Sales" in classification:
        return handle_sales_flow(session_id, user_message, new_lead=True)
    
    # Fallback
    response = "I'm not sure how to handle this request. I'll escalate it to a human agent."
    update_session(session_id, "assistant", response)
    return {"response": response}

def handle_technical_flow(session_id: str, message: str, new_issue: bool = False):
    # Initialize tech progress
    if new_issue or session_id not in tech_progress:
        tech_progress[session_id] = {
            "issue": message,
            "attempts": 0,
            "resolved": False
        }
    
    state = tech_progress[session_id]
    
    # Check if previous solution worked
    if not new_issue:
        if "yes" in message.lower():
            state["resolved"] = True
            response = "Great! Let me know if you need anything else."
            update_session(session_id, "assistant", response)
            reset_flow(session_id, "tech")
            return {"response": response}
        elif "no" in message.lower():
            state["attempts"] += 1
    
    # Escalate after 2 failed attempts or complex issue
    if state["attempts"] >= 2 or should_escalate_by_sentiment(message):
        response = "I've escalated this to our technical team. They'll contact you shortly."
        update_session(session_id, "assistant", response)
        reset_flow(session_id, "tech")
        return {"response": response}
    
    # Search knowledge base
    results = search_kb(state["issue"])
    if results and results['documents']:
        # Use conversation-aware response generation
        response = get_technical_response(
            session_store[session_id],
            results['documents'][0]
        )
        state["attempts"] += 1
    else:
        response = "Thanks for your query. I couldn't find an immediate solution. I've escalated this to our technical team."
        reset_flow(session_id, "tech")
    
    update_session(session_id, "assistant", response)
    return {"response": response}

def handle_sales_flow(session_id: str, message: str, new_lead: bool = False):
    if new_lead or session_id not in sales_progress:
        if is_complex_sales_inquiry(message):
            response = "Your inquiry requires personalized attention. We've escalated it to our sales team."
            update_session(session_id, "assistant", response)
            return {"response": response}
        sales_progress[session_id] = {
            "fields": {"name": "", "company": "", "team_size": "", "sales_query": ""},
            "last_prompted_field": None
        }

    state = sales_progress[session_id]
    fields = state["fields"]

    # Extract relevant fields from message using LLM
    extracted = extract_sales_fields(message)
    print(f"[SALES] Extracted fields: {extracted}")

    # Update fields with extracted data
    updated = False
    for field in fields:
        if not fields[field] and extracted.get(field):
            fields[field] = extracted[field].strip()
            updated = True

    # If no fields updated and we have a last prompted field, try direct assignment
    if not updated and state["last_prompted_field"]:
        field = state["last_prompted_field"]
        if not fields[field]:
            fields[field] = message.strip()
            updated = True

    # Determine next missing field
    required_fields = ["name", "company", "team_size", "sales_query"]
    next_field = None
    for field in required_fields:
        if not fields[field]:
            next_field = field
            break

    # If all fields are present, log and complete
    if not next_field:
        entry = (
            f"Name: {fields['name']}\n"
            f"Company: {fields['company']}\n"
            f"Team Size: {fields['team_size']}\n"
            f"Message: {fields['sales_query']}"
        )
        log_to_file(SALES_FILE, entry)

        response = (
            f"Thanks {fields['name']} from {fields['company']} with a team of {fields['team_size']}.\n"
            "We’ve recorded your query and our sales team will reach out to you shortly."
        )
        update_session(session_id, "assistant", response)
        reset_flow(session_id, "sales")
        return {"response": response}

    # Prompt for missing field
    prompts = {
        "name": "Could you please provide your name?",
        "company": "What company are you representing?",
        "team_size": "How many people are on your team?",
        "sales_query": "What is your sales or business query?"
    }
    response = prompts[next_field]
    state["last_prompted_field"] = next_field  # Remember last prompted field
    update_session(session_id, "assistant", response)
    return {"response": response}

def handle_feature_flow(session_id: str, message: str, new_request: bool = False):
    if new_request or session_id not in feature_progress:
        feature_progress[session_id] = {"description": message}
        response = "Thank you for your suggestion! We've logged your feature request."
        log_to_file(FEATURES_FILE, f"Feature Request: {message}")
    else:
        feature_progress[session_id]["description"] += f" {message}"
        response = "I've updated your feature request with additional details."
    
    update_session(session_id, "assistant", response)
    
    # Reset after logging
    reset_flow(session_id, "feature")
    return {"response": response}
