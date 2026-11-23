import os
import html
import textwrap
from datetime import datetime

import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from graph import app


# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="TripPilot AI — Multi-Agent Travel Planner",
    page_icon="✈️",
    layout="wide",
)

# -------------------------------------------------------------------
# Styling — preserves the original TripPilot AI red-and-white design
# -------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"], .stApp {
        font-family: 'Inter', sans-serif;
        background: #fffafa !important;
        color: #202636 !important;
    }
    [data-testid="stHeader"] { background: rgba(255,255,255,.92) !important; }
    .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1200px; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #a70e1b 0%, #c91424 60%, #8f0d18 100%) !important;
        border-right: 1px solid #8f0d18 !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown { color: #fff !important; }
    section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.25) !important; }
    .sidebar-title { color: #fff; font-size: 1.05rem; font-weight: 800; margin: 1rem 0 .5rem; }
    .sidebar-chip {
        background: rgba(255,255,255,.11); border: 1px solid rgba(255,255,255,.18);
        border-radius: 9px; padding: .45rem .75rem; margin-bottom: .4rem;
        font-size: .83rem; color: #fff;
    }

    .hero-wrapper {
        position: relative; isolation: isolate; width: 100%; min-height: 280px;
        border-radius: 20px; overflow: hidden; margin-bottom: 1.5rem;
        border: 1px solid #f0dadd;
        box-shadow: 0 12px 35px rgba(139,15,28,.10);
        background-image:
            linear-gradient(rgba(0,0,0,.48), rgba(0,0,0,.56)),
            url("https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1600&q=85");
        background-size: cover; background-position: center;
    }
    .hero-content {
        min-height: 280px; display: flex; flex-direction: column;
        align-items: center; justify-content: center; text-align: center;
        padding: clamp(1.25rem, 4vw, 2rem);
    }
    .hero-badge {
        background: rgba(201,20,36,.28); border: 1px solid rgba(255,190,197,.6);
        color: #fff; font-size: .75rem; font-weight: 700; letter-spacing: .12em;
        text-transform: uppercase; padding: .3rem .9rem; border-radius: 20px;
        margin-bottom: .9rem;
    }
    .hero-title {
        font-size: clamp(1.55rem, 4vw, 2.6rem); font-weight: 800;
        color: #fff; margin: 0 0 .6rem; line-height: 1.2;
    }
    .hero-sub { max-width: 650px; color: #f3e9ea; font-size: 1rem; line-height: 1.6; }

    .input-card {
        background: #fff; border: 1px solid #f0dadd; border-radius: 16px;
        padding: 1.3rem 1.5rem; margin-bottom: 1.2rem;
        box-shadow: 0 5px 18px rgba(80,20,30,.04);
    }
    .input-label { color: #b70e1e; font-size: .8rem; font-weight: 800;
        letter-spacing: .1em; text-transform: uppercase; margin-bottom: .5rem; }
    .sec-head {
        display: flex; align-items: center; gap: .6rem; margin: 1.8rem 0 .75rem;
        padding-bottom: .5rem; border-bottom: 1px solid #f0dadd;
    }
    .sec-head span { font-size: 1.12rem; font-weight: 700; color: #151b29; }

    .metric-row { display: flex; gap: 1rem; margin: 1.2rem 0; }
    .metric-box {
        flex: 1; background: #fff; border: 1px solid #f0dadd; border-radius: 12px;
        padding: 1rem 1.2rem; text-align: center;
        box-shadow: 0 5px 15px rgba(70,20,25,.035);
    }
    .metric-val { font-size: 1.7rem; font-weight: 800; color: #c91424; }
    .metric-lbl { font-size: .75rem; color: #697386; margin-top: .2rem;
        text-transform: uppercase; letter-spacing: .08em; }

    .final-card {
        background: #fff; border: 1px solid #f0dadd; border-left: 5px solid #c91424;
        border-radius: 14px; padding: 1.5rem; line-height: 1.8; color: #273044;
        box-shadow: 0 6px 20px rgba(70,20,25,.045);
    }
    .save-bar {
        background: #fff5f5; border: 1px solid #f0dadd; border-radius: 10px;
        padding: .85rem 1.2rem; color: #7f2430; font-size: .88rem; margin-top: .5rem;
    }
    .save-bar code { color: #a30f1e; background: #ffe5e7; }

    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        border-radius: 11px !important; font-weight: 700 !important;
    }
    div[data-testid="stButton"] > button {
        background: #fff !important; color: #202636 !important;
        border: 1px solid #f0d5d8 !important;
        box-shadow: 0 4px 12px rgba(80,20,30,.045) !important;
    }
    div[data-testid="stButton"] > button:hover {
        background: #fff4f5 !important; color: #b70e1e !important;
        border-color: #e72b3a !important;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        color: #fff !important; background: linear-gradient(100deg,#ed2636,#b70e1e) !important;
        border: none !important; box-shadow: 0 8px 20px rgba(201,20,36,.20) !important;
    }
    div[data-testid="stDownloadButton"] > button {
        background: #fff1f2 !important; color: #a70e1b !important;
        border: 1px solid #f0cdd1 !important;
    }

    .stTextArea textarea, .stTextInput input {
        background: #fff !important; color: #202636 !important;
        border: 1px solid #e8cfd2 !important; border-radius: 10px !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #c91424 !important; box-shadow: 0 0 0 3px rgba(201,20,36,.10) !important;
    }
    .stTextArea textarea::placeholder, input[type="text"]::placeholder { color: #929aaa !important; }
    .stTextInput label, .stTextArea label, .stRadio label, .stSelectbox label {
        color: #9d1421 !important; font-weight: 700 !important;
    }
    .stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th { color: #374151; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #151b29; }
    [data-testid="stStatusWidget"] {
        background: #fff !important; border: 1px solid #f0dadd !important;
        border-radius: 13px !important; box-shadow: 0 4px 14px rgba(70,20,25,.04) !important;
    }
    [data-testid="stStatusWidget"] * { color: #273044 !important; }
    .stAlert { border-radius: 10px !important; }

    #MainMenu, footer { visibility: hidden; }

    @media (max-width: 800px) {
        .hero-wrapper, .hero-content { min-height: 250px; }
        .hero-title { font-size: clamp(1.4rem, 6vw, 1.8rem); }
        .metric-row { flex-direction: column; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------------
# Small helpers
# -------------------------------------------------------------------
def render_section(title: str) -> None:
    st.markdown(
        f"<div class='sec-head'><span>{html.escape(title)}</span></div>",
        unsafe_allow_html=True,
    )


def save_plan(query: str, user_id: str, data: dict) -> tuple[str, str]:
    """Save the generated plan as Markdown and return (filename, content)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"travelplan_{timestamp}.md"
    save_dir = os.path.join(os.path.dirname(__file__), "travel_plans")
    os.makedirs(save_dir, exist_ok=True)

    content = f"""# TripPilot AI — Travel Plan

**Query:** {query}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**User ID:** {user_id}

---

## ✈️ Flight Information

{data.get('flight_results') or 'Not requested or no result returned.'}

---

## 🏨 Hotel Information

{data.get('hotel_results') or 'Not requested or no result returned.'}

---

## 🌤️ Weather Information

{data.get('weather_results') or 'Not requested or no result returned.'}

---

## 💰 Budget Assessment

{data.get('budget_results') or 'Not requested or no result returned.'}

---

## 🗓️ Draft Itinerary

{data.get('itinerary') or 'No draft itinerary returned.'}

---

## 🧠 Final Travel Plan

{data.get('final_response') or 'No final response returned.'}

---

**LLM calls:** {data.get('llm_calls', 0)}
"""
    path = os.path.join(save_dir, filename)
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)
    return filename, content


def apply_update(target: dict, update: dict) -> None:
    """Merge one LangGraph node update into the display state."""
    if not isinstance(update, dict):
        return
    for key in (
        "selected_agents",
        "supervisor_reasoning",
        "trip_constraints",
        "flight_results",
        "hotel_results",
        "weather_results",
        "budget_results",
        "itinerary",
        "approval_request",
        "human_feedback",
        "approved",
        "final_response",
        "llm_calls",
    ):
        if key in update:
            target[key] = update[key]


def run_graph(input_or_command, config: dict, display_state: dict) -> dict | None:
    """Stream graph updates, render agent activity, and return interrupt data if paused."""
    interrupt_payload = None

    for chunk in app.stream(input_or_command, config=config, stream_mode="updates"):
        if not isinstance(chunk, dict):
            continue

        # LangGraph emits interrupts as a special top-level update.
        if "__interrupt__" in chunk:
            values = chunk["__interrupt__"]
            if values:
                first = values[0]
                interrupt_payload = getattr(first, "value", first)
            continue

        for node_name, node_update in chunk.items():
            if node_name == "__metadata__":
                continue

            if isinstance(node_update, dict) and "__interrupt__" in node_update:
                values = node_update["__interrupt__"]
                if values:
                    first = values[0]
                    interrupt_payload = getattr(first, "value", first)
                continue

            apply_update(display_state, node_update)

            icon, label = AGENT_META.get(node_name, ("⚙️", node_name.replace("_", " ").title()))
            with st.status(f"{icon}  {label}", state="complete", expanded=False):
                if node_name == "supervisor":
                    selected = display_state.get("selected_agents", [])
                    st.write("Selected specialists:", ", ".join(selected) if selected else "None")
                    reasoning = display_state.get("supervisor_reasoning")
                    if reasoning:
                        st.write(reasoning)
                    if display_state.get("final_response") and not selected:
                        st.warning(display_state["final_response"])
                elif node_name == "flight_agent":
                    st.markdown(display_state.get("flight_results") or "_No flight data returned._")
                elif node_name == "hotel_agent":
                    st.markdown(display_state.get("hotel_results") or "_No hotel data returned._")
                elif node_name == "weather_agent":
                    st.markdown(display_state.get("weather_results") or "_No weather data returned._")
                elif node_name == "budget_agent":
                    st.markdown(display_state.get("budget_results") or "_No budget assessment returned._")
                elif node_name == "itinerary_agent":
                    st.markdown(display_state.get("itinerary") or "_No draft itinerary returned._")
                elif node_name == "human_approval":
                    st.info("The graph is waiting for your approval or feedback.")
                elif node_name == "final_response":
                    st.markdown(display_state.get("final_response") or "_No final response returned._")

    return interrupt_payload


# -------------------------------------------------------------------
# New-conversation callback and session initialization
# -------------------------------------------------------------------
def start_new_conversation() -> None:
    """Clear the current UI conversation and assign a fresh LangGraph thread ID."""
    st.session_state.pop("pending_approval", None)
    st.session_state.pop("display_state", None)
    st.session_state.pop("last_plan", None)

    # These assignments are safe here because this function runs as a
    # Streamlit callback before the script reruns and recreates the widgets.
    st.session_state["user_id"] = (
        f"user_{datetime.now().strftime('%H%M%S%f')}"
    )
    st.session_state["trip_query"] = ""


if "user_id" not in st.session_state:
    st.session_state["user_id"] = "user_raj"

if "trip_query" not in st.session_state:
    st.session_state["trip_query"] = ""


# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown("<div class='sidebar-title'>✈️ TripPilot AI</div>", unsafe_allow_html=True)
    st.markdown("---")

    user_id = st.text_input(
        "👤 User ID",
        help="Session ID used by LangGraph checkpointing for this travel conversation.",
        key="user_id",
    )

    st.markdown("<div class='sidebar-title'>Powered by</div>", unsafe_allow_html=True)
    for tech in [
        "🔗 LangGraph",
        "🧠 Groq · LLM",
        "🐘 PostgreSQL Checkpointing",
        "🔍 Tavily Search",
        "✈️ AviationStack MCP",
        "🌤️ Weather MCP",
    ]:
        st.markdown(f"<div class='sidebar-chip'>{tech}</div>", unsafe_allow_html=True)

    st.markdown("<div class='sidebar-title'>Agent Pipeline</div>", unsafe_allow_html=True)
    for step in [
        "① Supervisor + Guardrail",
        "② Flight Agent",
        "③ Hotel Agent",
        "④ Weather Agent",
        "⑤ Budget Agent",
        "⑥ Itinerary Agent",
        "⑦ Human Approval",
        "⑧ Final Response",
    ]:
        st.markdown(f"<div class='sidebar-chip'>{step}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.button(
        "🧹 Start a new conversation",
        use_container_width=True,
        on_click=start_new_conversation,
    )


# -------------------------------------------------------------------
# Hero
# -------------------------------------------------------------------
hero_html = textwrap.dedent(
    """
    <div class="hero-wrapper">
      <div class="hero-content">
        <div class="hero-badge">✦ Supervisor · Specialist Agents · Human-in-the-Loop</div>
        <div class="hero-title">✈️ TripPilot AI <span style="color:#ff6571;">Travel Planner</span></div>
        <div class="hero-sub">
          Your AI travel team researches flights, stays, weather and budget,
          builds an itinerary, and waits for your approval before preparing the final plan.
        </div>
      </div>
    </div>
    """
).strip()
st.markdown(hero_html, unsafe_allow_html=True)


# -------------------------------------------------------------------
# Destination image strip
# -------------------------------------------------------------------
DESTINATIONS = [
    ("🇯🇵 Tokyo", "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=450&q=75"),
    ("🇫🇷 Paris", "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=450&q=75"),
    ("🇹🇭 Bangkok", "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=450&q=75"),
    ("🇮🇹 Rome", "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=450&q=75"),
    ("🇦🇪 Dubai", "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=450&q=75"),
]
cols = st.columns(5)
for col, (name, image_url) in zip(cols, DESTINATIONS):
    with col:
        st.markdown(
            f"""
            <div style="border-radius:10px;overflow:hidden;position:relative;height:92px;">
              <img src="{image_url}" alt="{html.escape(name)}"
                   style="width:100%;height:100%;object-fit:cover;filter:brightness(.58);">
              <div style="position:absolute;bottom:8px;left:0;right:0;text-align:center;
                          color:#fff;font-size:.82rem;font-weight:700;">
                {html.escape(name)}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)


# -------------------------------------------------------------------
# Main trip request input
# -------------------------------------------------------------------
st.markdown("<div class='input-label'>🗺️ Describe your trip</div>", unsafe_allow_html=True)

QUICK_PROMPTS = [
    "Plan a 7-day Japan trip under ₹2 lakhs",
    "Plan a 5-day Paris trip",
    "Plan a Dubai weekend trip",
    "Plan a 10-day Bali backpacking trip",
]

quick_cols = st.columns(4)
for col, prompt in zip(quick_cols, QUICK_PROMPTS):
    with col:
        if st.button(prompt, key=f"quick_{QUICK_PROMPTS.index(prompt)}", use_container_width=True):
            st.session_state["trip_query"] = prompt

user_query = st.text_area(
    "Describe your trip",
    value=st.session_state.get("trip_query", ""),
    key="trip_query",
    placeholder=(
        "e.g. Plan a complete 7-day Japan trip including flights, hotels, "
        "weather and sightseeing under ₹2 lakhs. I am travelling from Kolkata."
    ),
    height=110,
    label_visibility="collapsed",
)

generate = st.button("🚀  Generate My Travel Plan", type="primary", use_container_width=True)


# -------------------------------------------------------------------
# Graph state and node labels
# -------------------------------------------------------------------
AGENT_META = {
    "supervisor": ("🧭", "Supervisor & Input Guardrail"),
    "flight_agent": ("✈️", "Flight Agent"),
    "hotel_agent": ("🏨", "Hotel Agent"),
    "weather_agent": ("🌤️", "Weather Agent"),
    "budget_agent": ("💰", "Budget Agent"),
    "itinerary_agent": ("🗓️", "Itinerary Agent"),
    "human_approval": ("🙋", "Human Approval"),
    "final_response": ("🧠", "Final Response Agent"),
}

DEFAULT_DISPLAY_STATE = {
    "selected_agents": [],
    "supervisor_reasoning": "",
    "trip_constraints": {},
    "flight_results": "",
    "hotel_results": "",
    "weather_results": "",
    "budget_results": "",
    "itinerary": "",
    "approval_request": "",
    "human_feedback": "",
    "approved": None,
    "final_response": "",
    "llm_calls": 0,
}


# -------------------------------------------------------------------
# Start a new graph run
# -------------------------------------------------------------------
if generate:
    if not user_query.strip():
        st.warning("Please describe your trip first.")
    else:
        config = {"configurable": {"thread_id": user_id.strip() or "user_raj"}}
        display_state = DEFAULT_DISPLAY_STATE.copy()
        st.session_state["display_state"] = display_state
        st.session_state.pop("pending_approval", None)
        st.session_state.pop("last_plan", None)

        initial_state = {
            "messages": [HumanMessage(content=user_query.strip())],
            "user_id": user_id.strip() or "user_raj",
            "user_query": user_query.strip(),
            "trip_constraints": {},
            "selected_agents": [],
            "supervisor_reasoning": "",
            "flight_results": "",
            "hotel_results": "",
            "weather_results": "",
            "budget_results": "",
            "itinerary": "",
            "approval_request": "",
            "human_feedback": "",
            "approved": False,
            "final_response": "",
            "llm_calls": 0,
        }

        render_section("🤖 Agent Pipeline — Live")
        try:
            with st.spinner("TripPilot AI is coordinating your travel agents..."):
                interrupt_data = run_graph(initial_state, config, display_state)

            st.session_state["display_state"] = display_state
            if interrupt_data is not None:
                st.session_state["pending_approval"] = {
                    "config": config,
                    "query": user_query.strip(),
                    "interrupt": interrupt_data,
                }
                st.success("Your draft itinerary is ready. Please review it below.")
            elif display_state.get("final_response"):
                filename, file_content = save_plan(user_query.strip(), user_id, display_state)
                st.session_state["last_plan"] = {
                    "filename": filename,
                    "content": file_content,
                    "display_state": display_state,
                }
                st.success("Your travel plan has been generated.")
            else:
                st.warning(
                    "The graph finished without a final response or approval pause. "
                    "Check the terminal for backend logs."
                )
        except Exception as exc:
            st.error(f"Project error: {exc}")
            st.exception(exc)


# -------------------------------------------------------------------
# Human-in-the-loop approval and resume
# -------------------------------------------------------------------
pending = st.session_state.get("pending_approval")
if pending:
    display_state = st.session_state.get("display_state", DEFAULT_DISPLAY_STATE.copy())

    render_section("🗓️ Review Your Draft Itinerary")
    draft = display_state.get("itinerary", "")
    if draft:
        st.markdown(
            f"<div class='final-card'>{html.escape(draft).replace(chr(10), '<br>')}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("The workflow paused for human review, but no draft text was returned.")

    approval_text = display_state.get("approval_request", "")
    if approval_text:
        with st.expander("Review request from the itinerary agent"):
            st.write(approval_text)

    with st.form("human_approval_form"):
        decision = st.radio(
            "Do you approve this itinerary?",
            options=["Approve itinerary", "Request changes"],
            horizontal=True,
        )
        feedback = st.text_area(
            "Feedback (optional for approval; explain requested changes if not approved)",
            placeholder="Tell the AI what you want changed...",
            height=100,
        )
        submitted = st.form_submit_button("Submit Review & Continue", type="primary", use_container_width=True)

    if submitted:
        resume_value = {
            "approved": decision == "Approve itinerary",
            "feedback": feedback.strip(),
        }
        try:
            with st.spinner("Preparing your final travel plan..."):
                for _chunk in app.stream(
                    Command(resume=resume_value),
                    config=pending["config"],
                    stream_mode="updates",
                ):
                    if isinstance(_chunk, dict):
                        for node_name, node_update in _chunk.items():
                            if node_name == "__interrupt__":
                                continue
                            apply_update(display_state, node_update)

            st.session_state["display_state"] = display_state
            st.session_state.pop("pending_approval", None)

            if display_state.get("final_response"):
                filename, file_content = save_plan(
                    pending["query"],
                    user_id,
                    display_state,
                )
                st.session_state["last_plan"] = {
                    "filename": filename,
                    "content": file_content,
                    "display_state": display_state,
                }
                st.success("Your final travel plan is ready.")
            else:
                st.warning("The graph resumed, but no final response was returned. Check the terminal logs.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not resume the approval workflow: {exc}")
            st.exception(exc)


# -------------------------------------------------------------------
# Results, metrics and download
# -------------------------------------------------------------------
last_plan = st.session_state.get("last_plan")
if last_plan:
    data = last_plan["display_state"]

    render_section("📊 Trip Planning Summary")
    llm_calls = data.get("llm_calls", 0)
    selected_count = len(data.get("selected_agents", []))
    metrics_html = f"""
    <div class="metric-row">
      <div class="metric-box"><div class="metric-val">{selected_count}</div>
        <div class="metric-lbl">Specialist Agents Selected</div></div>
      <div class="metric-box"><div class="metric-val">{llm_calls}</div>
        <div class="metric-lbl">LLM Calls</div></div>
      <div class="metric-box"><div class="metric-val">✓</div>
        <div class="metric-lbl">Workflow Completed</div></div>
    </div>
    """
    st.markdown(metrics_html, unsafe_allow_html=True)

    if data.get("supervisor_reasoning"):
        with st.expander("🧭 Supervisor's routing explanation"):
            st.write(data["supervisor_reasoning"])

    if data.get("trip_constraints"):
        with st.expander("🧳 Extracted Trip Details"):
            for key, value in data["trip_constraints"].items():
                label = key.replace("_", " ").title()
                if isinstance(value, list):
                    value = ", ".join(str(item) for item in value) or "Not specified"
                elif isinstance(value, dict):
                    value = "; ".join(
                        f"{nested_key.replace('_', ' ').title()}: {nested_value}"
                        for nested_key, nested_value in value.items()
                    )
                st.markdown(f"**{html.escape(label)}:** {html.escape(str(value or 'Not specified'))}")

    for key, title in [
        ("flight_results", "✈️ Flight Information"),
        ("hotel_results", "🏨 Hotel Information"),
        ("weather_results", "🌤️ Weather Information"),
        ("budget_results", "💰 Budget Assessment"),
        ("itinerary", "🗓️ Draft Itinerary"),
    ]:
        if data.get(key):
            with st.expander(title):
                st.markdown(data[key])

    render_section("🧠 Final Travel Plan")
    final_text = data.get("final_response", "")
    if final_text:
        st.markdown(
            f"<div class='final-card'>{html.escape(final_text).replace(chr(10), '<br>')}</div>",
            unsafe_allow_html=True,
        )

    dl_col, info_col = st.columns([1, 3])
    with dl_col:
        st.download_button(
            "⬇️ Download Plan",
            data=last_plan["content"],
            file_name=last_plan["filename"],
            mime="text/markdown",
            use_container_width=True,
        )
    with info_col:
        st.markdown(
            f"<div class='save-bar'>📁 Auto-saved → "
            f"<code>travel_plans/{html.escape(last_plan['filename'])}</code></div>",
            unsafe_allow_html=True,
        )
