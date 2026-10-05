import os
import json
import glob
import re
from datetime import datetime

import streamlit as st
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

load_dotenv()

APP_TITLE = "Vimala AI Support Agent"
KNOWLEDGE_FOLDER = "knowledge_base"
TICKET_FILE = "tickets.json"

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "").strip()

MODEL = os.getenv("MODEL", "Qwen/Qwen3.8-27B")

# ---------------------------------------------------------
# STREAMLIT PAGE
# ---------------------------------------------------------

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# CSS
# ---------------------------------------------------------

st.markdown(
    """
    <style>

    .stApp {
        background: linear-gradient(
            135deg,
            #ffffff 0%,
            #f7f5ff 45%,
            #eef7ff 100%
        );
    }

    [data-testid="stSidebar"] {
        background: #f1f3f7;
    }

    .main-title {
        font-size: 42px;
        font-weight: 800;
        color: #26344f;
        margin-bottom: 12px;
    }

    .online-box {
        background: #e5f8eb;
        border-radius: 10px;
        padding: 16px 18px;
        color: #08752b;
        font-size: 16px;
        margin-bottom: 20px;
    }

    .feature-text {
        color: #7b7192;
        font-size: 14px;
        margin-bottom: 30px;
    }

    .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #17243d;
        margin-top: 10px;
        margin-bottom: 12px;
    }

    .info-card {
        background: white;
        border-radius: 14px;
        padding: 16px;
        border: 1px solid #e5e7ef;
        box-shadow: 0 3px 15px rgba(60, 60, 100, 0.06);
    }

    .success-card {
        background: #eaf8ef;
        border-left: 5px solid #28a745;
        padding: 14px;
        border-radius: 8px;
        margin: 10px 0;
    }

    .warning-card {
        background: #fff7df;
        border-left: 5px solid #e6a700;
        padding: 14px;
        border-radius: 8px;
        margin: 10px 0;
    }

    .ticket-card {
        background: #f5f0ff;
        border-left: 5px solid #7657d9;
        padding: 14px;
        border-radius: 8px;
        margin: 10px 0;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "product_knowledge" not in st.session_state:
    st.session_state.product_knowledge = ""

if "product_name" not in st.session_state:
    st.session_state.product_name = ""

if "tnpsc_results" not in st.session_state:
    st.session_state.tnpsc_results = []

if "last_ticket" not in st.session_state:
    st.session_state.last_ticket = None

if "escalated" not in st.session_state:
    st.session_state.escalated = False


# ---------------------------------------------------------
# KNOWLEDGE BASE
# ---------------------------------------------------------

def load_knowledge_base():
    documents = []

    os.makedirs(KNOWLEDGE_FOLDER, exist_ok=True)

    files = glob.glob(
        os.path.join(KNOWLEDGE_FOLDER, "*.txt")
    )

    for file_path in files:
        try:
            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:
                text = f.read().strip()

            if text:
                documents.append(
                    {
                        "file": os.path.basename(file_path),
                        "text": text
                    }
                )

        except Exception:
            continue

    return documents


knowledge_docs = load_knowledge_base()


# ---------------------------------------------------------
# SIMPLE RAG SEARCH
# ---------------------------------------------------------

def tokenize(text):
    return set(
        re.findall(
            r"[a-zA-Z0-9]+",
            text.lower()
        )
    )


def search_knowledge(query, top_k=4):

    if not knowledge_docs:
        return []

    query_words = tokenize(query)

    if not query_words:
        return []

    scored = []

    for doc in knowledge_docs:

        doc_words = tokenize(doc["text"])

        score = len(
            query_words.intersection(doc_words)
        )

        if score > 0:
            scored.append(
                (
                    score,
                    doc
                )
            )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [
        item[1]
        for item in scored[:top_k]
    ]


# ---------------------------------------------------------
# TICKET DATABASE
# ---------------------------------------------------------

def load_tickets():

    if not os.path.exists(TICKET_FILE):
        return []

    try:
        with open(
            TICKET_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []


def save_tickets(tickets):

    try:
        with open(
            TICKET_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                tickets,
                f,
                indent=4,
                ensure_ascii=False
            )
        return True

    except Exception:
        return False


def create_ticket(question, category="General"):

    tickets = load_tickets()

    ticket_id = (
        f"VIM-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )

    ticket = {
        "ticket_id": ticket_id,
        "question": question,
        "category": category,
        "status": "Open",
        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    tickets.append(ticket)

    save_tickets(tickets)

    return ticket


# ---------------------------------------------------------
# ONLINE PRODUCT SEARCH
# ---------------------------------------------------------

def search_product_online(product_name):

    if not SERPAPI_KEY:
        return (
            "Online product search is not configured yet. "
            "Add SERPAPI_KEY to your .env file."
        )

    try:

        params = {
            "engine": "google",
            "q": product_name,
            "api_key": SERPAPI_KEY,
            "num": 5
        }

        response = requests.get(
            "https://serpapi.com/search.json",
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            return (
                "Unable to connect to the online search service."
            )

        data = response.json()

        results = data.get(
            "organic_results",
            []
        )

        if not results:
            return (
                f"No online information found for {product_name}."
            )

        output = []

        for item in results[:5]:

            title = item.get(
                "title",
                "No title"
            )

            snippet = item.get(
                "snippet",
                ""
            )

            link = item.get(
                "link",
                ""
            )

            output.append(
                f"Title: {title}\n"
                f"Information: {snippet}\n"
                f"Link: {link}"
            )

        return "\n\n".join(output)

    except requests.RequestException:
        return (
            "Internet search connection failed. "
            "Please check your internet connection."
        )

    except Exception as e:
        return (
            f"Product search error: {str(e)}"
        )


# ---------------------------------------------------------
# TNPSC BOOK SEARCH
# ---------------------------------------------------------

def search_tnpsc_books(query):

    if not query.strip():
        return []

    search_query = (
        f"TNPSC books {query}"
    )

    if SERPAPI_KEY:

        try:

            params = {
                "engine": "google",
                "q": search_query,
                "api_key": SERPAPI_KEY,
                "num": 5
            }

            response = requests.get(
                "https://serpapi.com/search.json",
                params=params,
                timeout=15
            )

            if response.status_code == 200:

                data = response.json()

                results = data.get(
                    "organic_results",
                    []
                )

                return results[:5]

        except Exception:
            pass

    # Safe fallback if API unavailable
    return [
        {
            "title": f"TNPSC {query} Books",
            "snippet": (
                "Search for TNPSC preparation books "
                f"related to {query}."
            ),
            "link": ""
        }
    ]


# ---------------------------------------------------------
# KEYWORD DETECTION
# ---------------------------------------------------------

def needs_human(question):

    keywords = [
        "human",
        "agent",
        "person",
        "representative",
        "customer care",
        "support agent",
        "talk to someone",
        "manager"
    ]

    q = question.lower()

    return any(
        word in q
        for word in keywords
    )


def detect_category(question):

    q = question.lower()

    if "refund" in q:
        return "Refund"

    if "shipping" in q or "delivery" in q:
        return "Shipping"

    if "warranty" in q:
        return "Warranty"

    if "price" in q or "cost" in q:
        return "Price"

    if "track" in q or "order" in q:
        return "Order Tracking"

    if "product" in q:
        return "Product"

    return "General"


# ---------------------------------------------------------
# AI RESPONSE
# ---------------------------------------------------------

def local_support_response(question):

    q = question.lower()

    docs = search_knowledge(
        question,
        top_k=4
    )

    # Product context
    product_context = ""

    if st.session_state.product_knowledge:
        product_context = (
            "\n\nPRODUCT INFORMATION:\n"
            + st.session_state.product_knowledge[:5000]
        )

    # Human escalation
    if needs_human(question):

        st.session_state.escalated = True

        ticket = create_ticket(
            question,
            "Human Escalation"
        )

        st.session_state.last_ticket = ticket

        return (
            "I understand. I am escalating this "
            "conversation to a human support agent.\n\n"
            f"Ticket ID: {ticket['ticket_id']}"
        )

    # RAG response
    if docs:

        best = docs[0]["text"]

        # Keep response short
        if len(best) > 700:
            best = best[:700] + "..."

        return (
            f"Based on our knowledge base:\n\n"
            f"{best}\n\n"
            "If your case is not covered, I can create "
            "a support ticket."
        )

    # Product response
    if product_context:

        return (
            f"I found information for "
            f"{st.session_state.product_name}.\n\n"
            f"{product_context[:700]}"
        )

    # Common questions
    if "refund" in q:

        return (
            "Customers can request a refund for eligible "
            "orders according to the refund policy. "
            "Eligibility depends on order status and "
            "the applicable return period."
        )

    if "shipping" in q or "delivery" in q:

        return (
            "Shipping and delivery information depends "
            "on the order and destination. "
            "Please provide your order details."
        )

    if "warranty" in q:

        return (
            "Warranty coverage depends on the product "
            "and applicable warranty terms. "
            "I can create a ticket if your case needs "
            "further review."
        )

    if "price" in q:

        return (
            "Please provide the product name so I can "
            "help you check the available product "
            "information."
        )

    if "track" in q:

        return (
            "Please provide your order number so the "
            "support team can help with order tracking."
        )

    return (
        "I could not find an exact answer in the "
        "knowledge base.\n\n"
        "Please provide more details, or ask me to "
        "create a support ticket."
    )


# ---------------------------------------------------------
# OPTIONAL HUGGING FACE AI
# ---------------------------------------------------------

def hf_ai_response(question, context):

    if not HF_TOKEN:
        return None

    try:

        from huggingface_hub import InferenceClient

        client = InferenceClient(
            token=HF_TOKEN
        )

        prompt = f"""
You are Vimala AI Customer Support Agent.

Rules:
- Answer only from the provided context.
- Do not invent information.
- Keep the answer short.
- If information is unavailable, say that you cannot confirm it.
- If the user asks for a human agent, escalate.

Knowledge:
{context}

Customer question:
{question}

Answer:
"""

        result = client.chat_completion(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=MODEL,
            max_tokens=250,
            temperature=0.2
        )

        return result.choices[0].message.content

    except Exception:
        return None


def generate_answer(question):

    docs = search_knowledge(
        question,
        top_k=4
    )

    context_parts = []

    for doc in docs:
        context_parts.append(
            doc["text"]
        )

    if st.session_state.product_knowledge:
        context_parts.append(
            st.session_state.product_knowledge
        )

    context = "\n\n".join(
        context_parts
    )

    ai_answer = hf_ai_response(
        question,
        context
    )

    if ai_answer:
        return ai_answer

    return local_support_response(
        question
    )


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.markdown(
        "## ⚙️ Agent Controls"
    )

    st.write(
        f"**Knowledge Files:** {len(knowledge_docs)}"
    )

    st.write(
        f"**AI Model:** {MODEL}"
    )

    st.divider()

    # -----------------------------------------------------
    # PRODUCT SEARCH
    # -----------------------------------------------------

    st.markdown(
        "### 🔎 Online Product Search"
    )

    product_name = st.text_input(
        "Product name",
        placeholder="Example: Hair Oil",
        key="product_input"
    )

    if st.button(
        "Search Product",
        use_container_width=True
    ):

        if product_name.strip():

            with st.spinner(
                "Searching product..."
            ):

                result = search_product_online(
                    product_name.strip()
                )

            st.session_state.product_name = (
                product_name.strip()
            )

            st.session_state.product_knowledge = result

            st.success(
                "Product information loaded."
            )

        else:

            st.warning(
                "Enter a product name."
            )

    st.divider()

    # -----------------------------------------------------
    # TNPSC BOOKS
    # -----------------------------------------------------

    st.markdown(
        "### 📚 TNPSC Books"
    )

    tnpsc_query = st.text_input(
        "Search TNPSC books",
        placeholder="Example: Group 4 Tamil"
    )

    if st.button(
        "Search TNPSC Books",
        use_container_width=True
    ):

        if tnpsc_query.strip():

            with st.spinner(
                "Searching TNPSC books..."
            ):

                results = search_tnpsc_books(
                    tnpsc_query.strip()
                )

            st.session_state.tnpsc_results = results

            st.success(
                f"Found {len(results)} result(s)."
            )

        else:

            st.warning(
                "Enter a TNPSC book topic."
            )

    # Show TNPSC results
    if st.session_state.tnpsc_results:

        st.markdown(
            "#### Search Results"
        )

        for result in st.session_state.tnpsc_results:

            title = result.get(
                "title",
                "TNPSC Book"
            )

            snippet = result.get(
                "snippet",
                ""
            )

            link = result.get(
                "link",
                ""
            )

            st.markdown(
                f"**{title}**"
            )

            if snippet:
                st.caption(snippet)

            if link:
                st.markdown(
                    f"[Open Result]({link})"
                )

    st.divider()

    # -----------------------------------------------------
    # TICKET
    # -----------------------------------------------------

    st.markdown(
        "### 🎫 Support Ticket"
    )

    ticket_question = st.text_area(
        "Issue",
        placeholder="Describe your problem..."
    )

    if st.button(
        "Create Ticket",
        use_container_width=True
    ):

        if ticket_question.strip():

            ticket = create_ticket(
                ticket_question.strip(),
                detect_category(
                    ticket_question
                )
            )

            st.session_state.last_ticket = ticket

            st.success(
                f"Ticket created: {ticket['ticket_id']}"
            )

        else:

            st.warning(
                "Enter your issue."
            )

    if st.session_state.last_ticket:

        ticket = st.session_state.last_ticket

        st.info(
            f"Ticket ID: {ticket['ticket_id']}\n\n"
            f"Status: {ticket['status']}"
        )

    # -----------------------------------------------------
    # CLEAR CHAT
    # -----------------------------------------------------

    st.divider()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []
        st.session_state.escalated = False

        st.rerun()


# ---------------------------------------------------------
# MAIN AREA
# ---------------------------------------------------------

st.markdown(
    '<div class="main-title">🤖 Vimala AI Support Agent</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="online-box">
        🟢 AI Customer Support Agent is Online
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="feature-text">
        RAG • Online Product Search • TNPSC Books •
        Tickets • Human Escalation
    </div>
    """,
    unsafe_allow_html=True
)

# Product status
if st.session_state.product_name:

    st.markdown(
        f"""
        <div class="success-card">
        🛍️ <b>Active Product:</b>
        {st.session_state.product_name}
        </div>
        """,
        unsafe_allow_html=True
    )

# Escalation status
if st.session_state.escalated:

    st.markdown(
        """
        <div class="warning-card">
        👨‍💼 <b>Human Escalation Active</b><br>
        Your request has been forwarded to support.
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------------------------------------------------------
# CHAT HISTORY
# ---------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ---------------------------------------------------------
# CHAT INPUT
# ---------------------------------------------------------

question = st.chat_input(
    "Ask your customer support question..."
)

if question:

    # User message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    # AI response
    with st.chat_message("assistant"):

        with st.spinner(
            "AI is thinking..."
        ):

            answer = generate_answer(
                question
            )

        st.markdown(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )