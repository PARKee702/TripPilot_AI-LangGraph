import asyncio
import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt

from config import get_llm
from mcp_client import (
    current_weather,
    forecast,
    list_airlines,
    list_airports,
    tavily_search,
)
from state import TravelState


llm = get_llm()


def _llm_text(system: str, prompt: str) -> str:
    """Send a system instruction and user prompt to the configured chat model."""
    response = llm.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(content=prompt),
        ]
    )
    return response.content


def _compact_text(value: Any, max_chars: int = 1500) -> str:
    """Limit the size of upstream data before including it in an LLM prompt."""
    if value is None:
        return "Not available"

    text = str(value).strip()
    if not text:
        return "Not available"

    if len(text) > max_chars:
        text = text[:max_chars] + "\n[Additional content omitted]"
    return text


def _ensure_markdown_output(value: Any) -> str:
    """Convert accidental JSON output into readable Markdown for the UI."""
    if not isinstance(value, str):
        value = str(value)

    text = value.strip()
    if not text:
        return "No response was generated."

    # Only attempt JSON parsing when the whole response looks like JSON.
    if text.startswith("{") or text.startswith("["):
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return text

        def render(item: Any, heading: str = "") -> list[str]:
            lines = []
            if heading:
                lines.append(f"**{heading}:**")

            if isinstance(item, dict):
                for key, nested in item.items():
                    label = str(key).replace("_", " ").strip().title()
                    lines.extend(render(nested, label))
            elif isinstance(item, list):
                for entry in item:
                    if isinstance(entry, (dict, list)):
                        lines.append("-")
                        lines.extend(render(entry))
                    else:
                        lines.append(f"- {entry}")
            elif item is None or item == "":
                lines.append("Not specified")
            else:
                lines.append(str(item))

            return lines

        return "\n\n".join(render(parsed))

    return text


def _json_from_llm(text: str) -> dict:
    """Extract a JSON object from an LLM response."""
    print("\n========== RAW LLM RESPONSE ==========")
    print(text)
    print("======================================\n")

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"The model did not return a JSON object: {text}")

    json_text = text[start : end + 1]
    print("\n========== EXTRACTED JSON ==========")
    print(json_text)
    print("====================================\n")
    return json.loads(json_text)


def supervisor_agent(state: TravelState):
    query = state["user_query"]

    # Input guardrail
    guardrail_prompt = f"""
Determine whether the following request is a valid travel planning request.
Return only JSON in this format:
{{
    "allowed": true,
    "reason": ""
}}

User request:
{query}
"""

    guardrail_raw = _llm_text(
        "You are an input validation guardrail. Return strict JSON only.",
        guardrail_prompt,
    )
    guardrail_result = _json_from_llm(guardrail_raw)

    print("\n========== GUARDRAIL PARSED RESPONSE ==========")
    print(json.dumps(guardrail_result, indent=2))
    print("================================================\n")

    if not guardrail_result.get("allowed", False):
        reason = guardrail_result.get(
            "reason", "Request rejected by input guardrail."
        )
        return {
            "selected_agents": [],
            "trip_constraints": {},
            "supervisor_reasoning": reason,
            "final_response": reason,
            "messages": [AIMessage(content=f"Guardrail blocked request: {reason}")],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }

    prompt = f"""
You are the supervisor of a real-world multi-agent travel planning system.
Decide which specialist agents are needed for this user request.

Available agents:
- flight_agent: flights, airports, airlines, routes, or airfare guidance
- hotel_agent: hotels, stays, neighborhoods, or accommodation
- weather_agent: weather, climate, season, packing, or forecast
- budget_agent: budget, affordability, cost, or price constraints
- itinerary_agent: almost always needed to produce the travel plan

Return only JSON with this schema:
{{
  "selected_agents": ["flight_agent", "hotel_agent", "weather_agent", "budget_agent", "itinerary_agent"],
  "trip_constraints": {{
    "destination": "",
    "origin": "",
    "duration": "",
    "budget": "",
    "travel_style": "",
    "special_preferences": []
  }},
  "reasoning": ""
}}

User request:
{query}
"""

    raw = _llm_text(
        "You route work to specialist agents. Return strict JSON only.",
        prompt,
    )
    parsed = _json_from_llm(raw)

    print("\n========== PARSED JSON ==========")
    print(json.dumps(parsed, indent=2))
    print("=================================\n")

    return {
        "selected_agents": parsed["selected_agents"],
        "trip_constraints": parsed["trip_constraints"],
        "supervisor_reasoning": parsed["reasoning"],
        "messages": [AIMessage(content="Supervisor created the agent plan.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def flight_agent(state: TravelState):
    query = state["user_query"]
    constraints = state["trip_constraints"]
    destination = constraints["destination"]

    print("\n========== FLIGHT AGENT INPUT ==========")
    print("Query:", query)
    print("Constraints:", constraints)
    print("========================================\n")

    airports = asyncio.run(list_airports(destination, limit=10))
    airlines = asyncio.run(list_airlines("", limit=10))

    print("\n========== AIRPORT MCP DATA ==========")
    print(airports)
    print("======================================\n")
    print("\n========== AIRLINE MCP DATA ==========")
    print(airlines)
    print("======================================\n")

    prompt = f"""
Create flight guidance for this trip.

User request:
{_compact_text(query, 800)}

Trip constraints:
{_compact_text(constraints, 500)}

Airport MCP data:
{_compact_text(airports, 2500)}

Airline MCP data:
{_compact_text(airlines, 2500)}

Include likely departure/arrival airports, relevant airlines,
estimated duration, fare range, peak season warning, and booking advice.
Do not claim a flight or fare is confirmed unless the data confirms it.
"""

    result = _llm_text(
        "You are a flight planning specialist. Return readable Markdown, never JSON.",
        prompt + "\nReturn the answer as normal Markdown with headings and bullets. Do not return JSON."
    )
    result = _ensure_markdown_output(result)

    print("\n========== FLIGHT AGENT OUTPUT ==========")
    print(result)
    print("=========================================\n")

    return {
        "flight_results": result,
        "messages": [AIMessage(content="Flight agent completed.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def hotel_agent(state: TravelState):
    query = f"Best hotels and areas to stay for: {state['user_query']}"

    print("\n========== HOTEL AGENT INPUT ==========")
    print(query)
    print("=======================================\n")

    result = asyncio.run(tavily_search(query))
    readable_result = _ensure_markdown_output(result)

    print("\n========== HOTEL SEARCH RESULT ==========")
    print(readable_result)
    print("=========================================\n")

    return {
        "hotel_results": readable_result,
        "messages": [AIMessage(content="Hotel agent completed.")],
    }


def weather_agent(state: TravelState):
    constraints = state["trip_constraints"]
    city = constraints["destination"]

    print("\n========== WEATHER AGENT INPUT ==========")
    print("City:", city)
    print("=========================================\n")

    weather_data = asyncio.run(current_weather(city))
    forecast_data = asyncio.run(forecast(city))

    print("\n========== CURRENT WEATHER ==========")
    print(weather_data)
    print("=====================================\n")
    print("\n========== WEATHER FORECAST ==========")
    print(forecast_data)
    print("======================================\n")

    result = f"""
Current weather:
{weather_data}

Forecast:
{forecast_data}
"""

    print("\n========== WEATHER AGENT OUTPUT ==========")
    print(result)
    print("==========================================\n")

    return {
        "weather_results": _ensure_markdown_output(result),
        "messages": [AIMessage(content="Weather agent completed.")],
    }


def budget_agent(state: TravelState):
    print("\n========== BUDGET AGENT INPUT ==========")

    user_query = _compact_text(state.get("user_query", ""), 800)
    constraints = _compact_text(state.get("trip_constraints", {}), 500)
    flight_results = _compact_text(state.get("flight_results", ""), 1500)
    hotel_results = _compact_text(state.get("hotel_results", ""), 1500)
    weather_results = _compact_text(state.get("weather_results", ""), 1000)

    print("Trip Constraints:", constraints)
    print("Flight Results:", flight_results)
    print("Hotel Results:", hotel_results)
    print("Weather Results:", weather_results)
    print("=========================================\n")

    prompt = f"""
Analyze whether this trip plan is realistic for the user's budget.

User request:
{user_query}

Trip constraints:
{constraints}

Flight information:
{flight_results}

Hotel information:
{hotel_results}

Weather information:
{weather_results}

Return a concise budget assessment covering:
1. Estimated cost categories.
2. Major financial risks.
3. Money-saving suggestions.
4. Whether the trip is feasible within the budget.

Do not invent exact prices when reliable prices are unavailable.
Clearly distinguish estimates from confirmed prices.
Keep the response concise.
"""

    result = _llm_text(
        "You are a practical travel budget analyst. Analyze only supplied information. Return readable Markdown, never JSON.",
        prompt + "\nReturn normal Markdown with short headings and bullets. Do not return JSON.",
    )
    result = _ensure_markdown_output(result)

    print("\n========== BUDGET AGENT OUTPUT ==========")
    print(result)
    print("=========================================\n")

    return {
        "budget_results": result,
        "messages": [AIMessage(content="Budget agent completed.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def itinerary_agent(state: TravelState):
    print("\n========== ITINERARY AGENT INPUT ==========")

    user_query = _compact_text(state.get("user_query", ""), 800)
    constraints = _compact_text(state.get("trip_constraints", {}), 500)
    flight_results = _compact_text(state.get("flight_results", ""), 1200)
    hotel_results = _compact_text(state.get("hotel_results", ""), 1200)
    weather_results = _compact_text(state.get("weather_results", ""), 800)
    budget_results = _compact_text(state.get("budget_results", ""), 1000)

    print("Trip Constraints:", constraints)
    print("Flight Results:", flight_results)
    print("Hotel Results:", hotel_results)
    print("Weather Results:", weather_results)
    print("Budget Results:", budget_results)
    print("============================================\n")

    prompt = f"""
Create a practical draft travel itinerary.

User request:
{user_query}

Trip constraints:
{constraints}

Flight information:
{flight_results}

Hotel information:
{hotel_results}

Weather information:
{weather_results}

Budget assessment:
{budget_results}

Requirements:
1. Organize the trip day by day when trip duration is available.
2. Include practical activities and travel suggestions.
3. Consider weather and budget constraints.
4. Include accommodation and flight guidance where available.
5. Do not invent confirmed bookings or prices.
6. Clearly mention missing information.

Make the itinerary structured, practical, concise, and ready for human review.
"""

    result = _llm_text(
        "You are an expert travel itinerary planner. Use supplied research carefully, avoid unsupported claims, and return readable Markdown, never JSON.",
        prompt + "\nReturn a readable Markdown itinerary with headings and bullets. Do not return JSON.",
    )
    result = _ensure_markdown_output(result)

    print("\n========== ITINERARY OUTPUT ==========")
    print(result)
    print("======================================\n")

    approval_request = f"""
Please review this draft travel plan.

{_compact_text(result, 5000)}

Reply with approval or feedback.
"""

    return {
        "itinerary": result,
        "approval_request": approval_request,
        "messages": [AIMessage(content="Draft itinerary created for human review.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def human_approval_agent(state: TravelState):
    feedback = interrupt(
        {
            "question": "Do you approve this itinerary?",
            "draft_itinerary": state.get("itinerary", ""),
            "approval_request": state.get("approval_request", ""),
            "expected_response": {
                "approved": True,
                "feedback": "Optional feedback for revision",
            },
        }
    )

    approved = feedback["approved"]
    human_feedback = feedback.get("feedback", "")

    return {
        "approved": approved,
        "human_feedback": human_feedback,
        "messages": [AIMessage(content="Human approval step completed.")],
    }


def final_response_agent(state: TravelState):
    print("\n========== FINAL AGENT INPUT ==========")
    print("Approved:", state.get("approved"))
    print("Feedback:", state.get("human_feedback"))
    print("=======================================\n")

    # Keep the final model request bounded as well.
    itinerary = _compact_text(state.get("itinerary", ""), 2500)
    budget_results = _compact_text(state.get("budget_results", ""), 800)

    if state.get("approved"):
        prompt = f"""
The human approved this draft itinerary.
Produce the final polished travel plan. Preserve important details and do not invent bookings or prices.

Draft itinerary:
{itinerary}

Budget notes:
{budget_results}
"""
    else:
        user_query = _compact_text(state.get("user_query", ""), 800)
        human_feedback = _compact_text(state.get("human_feedback", ""), 800)
        prompt = f"""
The human did not approve the draft. Revise it using the feedback.

Original user request:
{user_query}

Draft itinerary:
{itinerary}

Human feedback:
{human_feedback}

Budget notes:
{budget_results}

Clearly address the feedback. Do not invent bookings or prices.
"""

    result = _llm_text(
        """You are TripPilot AI, a professional travel planning assistant.
Return ONLY a polished, user-friendly Markdown travel plan.
Never return JSON, XML, Python dictionaries, or a code block.
Use clear headings, bullet points, and numbered day-by-day sections.
Be practical, concise, and honest about estimates and missing information.
Never invent confirmed bookings, live availability, or exact prices.""",
        prompt + "\nIMPORTANT: The final answer must be natural-language Markdown, not JSON.",
    )
    result = _ensure_markdown_output(result)

    print("\n========== FINAL RESPONSE ==========")
    print(result)
    print("====================================\n")

    return {
        "final_response": result,
        "messages": [AIMessage(content=result)],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }
