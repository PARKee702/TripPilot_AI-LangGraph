# ✈️ TripPilot AI — Multi-Agent Travel Planner

TripPilot AI is an AI-powered travel planning application built with Python, Streamlit, LangGraph, and Groq. It uses a multi-agent workflow to retrieve flight information, discover hotels, generate personalized itineraries, and deliver a consolidated travel plan.

## Features

- **Flight Search:** Retrieves flight-related information through an integrated search tool.
- **Hotel Discovery:** Searches for relevant accommodation information using Tavily.
- **AI-Powered Itinerary:** Generates travel itineraries using a Groq-powered language model.
- **Multi-Agent Workflow:** Coordinates four specialized agents using LangGraph.
- **Consolidated Travel Plan:** Combines flight results, hotel information, and itinerary recommendations into a final response.
- **Persistent State:** Uses PostgreSQL and LangGraph checkpointing to maintain graph state.
- **Interactive UI:** A customized Streamlit interface with a red-and-white design.
- **Travel Plan Export:** Provides travel-plan saving and downloading functionality through the frontend.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | User interface |
| LangGraph | Multi-agent workflow orchestration |
| LangChain | LLM integration and message handling |
| Groq | Language model inference |
| Tavily | Web search and hotel discovery |
| PostgreSQL | Persistent state storage |
| Psycopg | PostgreSQL connectivity |
| python-dotenv | Environment variable management |

## Multi-Agent Workflow

TripPilot AI processes each travel request through four sequential agents.

```text
       User Travel Request
                |
                v
          Flight Agent
                |
                v
           Hotel Agent
                |
                v
         Itinerary Agent
                |
                v
      Final Response Agent
                |
                v
       Complete Travel Plan
```

### Agent Responsibilities

**1. Flight Agent**

Retrieves flight-related information using the configured flight-search tool.

**2. Hotel Agent**

Searches for accommodation information relevant to the user's travel request using Tavily.

**3. Itinerary Agent**

Uses the travel request, flight results, and hotel information to generate a travel itinerary with the Groq language model.

**4. Final Response Agent**

Combines the gathered flight information, hotel results, and generated itinerary into a final travel response.

LangGraph manages the agent execution sequence, while PostgreSQL checkpointing supports persistent state through a configurable thread ID.

## Project Structure

```text
TripPilot-AI/
├── tools/
│   ├── flight_tool.py
│   └── tavily_tool.py
├── main.py
├── frontend_trippilot_red_white.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

- `main.py` — Defines the agents, LangGraph workflow, LLM integration, and PostgreSQL checkpointer.
- `frontend_trippilot_red_white.py` — Implements the Streamlit user interface.
- `tools/flight_tool.py` — Handles flight-search functionality.
- `tools/tavily_tool.py` — Provides Tavily search functionality.
- `requirements.txt` — Lists the project's Python dependencies.
- `.env` — Stores environment variables and API credentials.

## Configuration

The application requires the following configuration:

- Groq API key for language model access.
- Tavily API key for web search.
- PostgreSQL connection URL for persistent graph state.

Credentials should be stored in environment variables and kept out of version control.

## Future Improvements

- Advanced flight and hotel comparison.
- Budget-based travel recommendations.
- More personalized itinerary customization.
- Enhanced error handling and search validation.
- Improved agent execution monitoring.
- Additional travel-plan export formats.

---

**TripPilot AI — Plan smarter. Travel better.** ✈️
