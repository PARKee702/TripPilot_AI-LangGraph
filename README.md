# ✈️ TripPilot AI --- Multi-Agent Travel Planner

TripPilot AI is an AI-powered travel planning application that
coordinates multiple specialist agents to research a trip, prepare a
practical itinerary, and present it for human approval before generating
the final travel plan.

Instead of relying on one large prompt, the application uses a
**Supervisor + Specialist Agents** workflow. The supervisor checks the
request and decides which agents are needed. The selected agents gather
travel information, assess the budget, and prepare an itinerary. The
user can then approve the draft or request changes.

The project is built with Python, Streamlit, LangGraph, Groq, and
MCP-based tools.

------------------------------------------------------------------------

## ✨ Features

-   **Supervisor and input guardrail** --- checks whether a request is
    suitable for travel planning and selects the relevant specialist
    agents.
-   **Flight research** --- uses AviationStack MCP data for airport and
    airline information, then generates flight guidance.
-   **Hotel research** --- uses Tavily Search to find accommodation
    information and useful areas to stay.
-   **Weather research** --- uses an OpenWeather-powered MCP server for
    current weather and forecast information.
-   **Budget assessment** --- evaluates the trip using the available
    flight, hotel, weather, and trip-constraint information.
-   **Day-by-day itinerary** --- combines the research into a practical
    draft plan.
-   **Human-in-the-loop approval** --- lets the user approve the
    itinerary or request changes before the final response.
-   **Final travel plan** --- produces a user-friendly Markdown response
    rather than displaying raw JSON.
-   **Downloadable plan** --- saves a Markdown copy under
    `travel_plans/` and provides it for download.
-   **Conversation checkpointing** --- uses PostgreSQL checkpointing
    when `DATABASE_URL` is configured, with a new thread ID for each new
    conversation.

> Travel information and prices are guidance based on the data returned
> by connected services. The application does not make or confirm
> bookings.

------------------------------------------------------------------------

## 🧠 How the workflow works

``` text
User enters a travel request
          |
          v
Supervisor + Input Guardrail
          |
          |-- Request rejected --> Show rejection message and stop
          |
          v
Select relevant specialist agents
          |
          +------> Flight Agent (when selected)
          |
          +------> Hotel Agent (when selected)
          |
          +------> Weather Agent (when selected)
          |
          +------> Budget Agent (when selected)
          |
          v
Itinerary Agent
          |
          v
Human Approval
          |
          |-- Request changes --> Final response incorporates feedback
          |
          |-- Approve ---------> Final response
          |
          v
Final Travel Plan
          |
          v
Save / Download Markdown
```

### Agent responsibilities

  -----------------------------------------------------------------------
  Component                           Responsibility
  ----------------------------------- -----------------------------------
  Supervisor                          Validates the request, extracts
                                      trip constraints, and chooses
                                      specialist agents.

  Flight Agent                        Retrieves airport and airline
                                      information through AviationStack
                                      MCP and creates flight guidance.

  Hotel Agent                         Searches for hotel and
                                      accommodation information through
                                      Tavily.

  Weather Agent                       Retrieves current weather and
                                      forecast information through the
                                      Weather MCP server.

  Budget Agent                        Assesses affordability, estimated
                                      cost categories, risks, and saving
                                      suggestions.

  Itinerary Agent                     Combines the available research
                                      into a draft itinerary.

  Human Approval                      Pauses the graph and waits for the
                                      user's approval or feedback.

  Final Response Agent                Produces the final user-facing
                                      travel plan.
  -----------------------------------------------------------------------

The supervisor's structured output is used internally for routing.
User-facing travel content is intended to be displayed as readable
Markdown.

------------------------------------------------------------------------

## 🛠️ Tech stack

  -----------------------------------------------------------------------
  Technology                          Usage
  ----------------------------------- -----------------------------------
  Python                              Main application and agent logic

  Streamlit                           Web interface

  LangGraph                           Agent orchestration, conditional
                                      routing, and human-in-the-loop
                                      workflow

  LangChain                           Chat model integration and message
                                      handling

  Groq                                LLM inference

  `openai/gpt-oss-120b`               Configured Groq model in the
                                      current setup

  Model Context Protocol (MCP)        Connects the application to
                                      external tools

  AviationStack MCP                   Airport and airline information

  Tavily Search                       Web search for accommodation
                                      research

  OpenWeather MCP server              Current weather and forecast

  PostgreSQL + LangGraph Postgres     Persistent graph checkpoints when
  Checkpointer                        configured
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 📁 Project structure

The main application folder is organized approximately as follows:

``` text
Multi_agent_system_part_3/
│
├── .venv/                    # Python virtual environment
├── .env                      # API keys and environment configuration
├── agents.py                 # Supervisor and specialist agent functions
├── config.py                 # Environment variables and Groq model setup
├── frontend.py               # Streamlit user interface
├── graph.py                  # LangGraph workflow and routing
├── mcp_client.py             # MCP client connections and tool wrappers
├── state.py                  # Shared TravelState definition
├── weather_mcp_server.py     # Weather MCP server
├── requirements.txt          # Python dependencies
├── README.md
│
└── travel_plans/             # Generated Markdown travel plans
```

The AviationStack MCP server is installed separately, alongside the main
application folder:

``` text
travel1/
│
├── Multi_agent_system_part_3/
│
└── aviationstack-mcp/
```

Your actual local folder names may differ. Keep the AviationStack MCP
folder where the path configuration in `mcp_client.py` expects it, or
update that configuration to match your setup.

------------------------------------------------------------------------

## ⚙️ Setup

### 1. Clone or download the project

Open a terminal in the project folder.

### 2. Create and activate a virtual environment

On Windows:

``` cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

``` cmd
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Install the AviationStack MCP server separately

From the parent folder that will contain both project folders:

``` cmd
git clone https://github.com/Pradumnasaraf/aviationstack-mcp.git
cd aviationstack-mcp
uv sync
```

The MCP server uses its own environment. The main application's MCP
client is configured to launch it using that environment's Python
executable.

If you already cloned and installed this server, do not clone it again.

### 5. Configure environment variables

Create a `.env` file in the main project folder. Add your own API
credentials:

``` env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

TAVILY_API_KEY=your_tavily_api_key
AVIATION_STACK_API_KEY=your_aviationstack_api_key
OPENWEATHER_API_KEY=your_openweather_api_key

DATABASE_URL=your_postgresql_connection_string
```

Use the variable names expected by `config.py`. If PostgreSQL is not
configured, leave `DATABASE_URL` unset or empty if the application
supports running without it.

**Important:** Never commit your real `.env` file or expose API keys in
screenshots, logs, or public repositories. Add `.env` to `.gitignore`.

------------------------------------------------------------------------

## ▶️ Run the application

From the main project directory, with the virtual environment activated:

``` cmd
streamlit run frontend.py
```

Streamlit will print a local URL, normally:

``` text
http://localhost:8501
```

Open that address in your browser.

The weather and AviationStack MCP processes are started through the MCP
client configuration in the application. Make sure their folders,
dependencies, and API keys are correctly configured before starting a
trip.

------------------------------------------------------------------------

## 🧳 Using TripPilot AI

1.  Enter a travel request, including details such as origin,
    destination, duration, budget, and preferences.
2.  Select **Generate My Travel Plan**.
3.  The supervisor checks the request and chooses the required agents.
4.  Follow the agent activity as the selected agents gather information
    and prepare the itinerary.
5.  Review the draft itinerary.
6.  Choose **Approve itinerary** or **Request changes** and provide
    feedback.
7.  Review the final travel plan.
8.  Download the Markdown plan if you want to keep a copy.

Use **Start a new conversation** to clear the current UI results and
begin with a fresh LangGraph thread ID. This does not delete previous
PostgreSQL checkpoints or previously saved Markdown plans.

------------------------------------------------------------------------

## 🔐 Environment variables

  -----------------------------------------------------------------------
  Variable                            Purpose
  ----------------------------------- -----------------------------------
  `GROQ_API_KEY`                      Authenticates requests to Groq.

  `GROQ_MODEL`                        Selects the Groq model. The current
                                      configuration defaults to
                                      `openai/gpt-oss-120b`.

  `TAVILY_API_KEY`                    Enables Tavily search.

  `AVIATION_STACK_API_KEY`            Enables AviationStack API access
                                      through its MCP server.

  `OPENWEATHER_API_KEY`               Enables weather data access.

  `DATABASE_URL`                      PostgreSQL connection string used
                                      for LangGraph checkpointing when
                                      configured.
  -----------------------------------------------------------------------

Do not share the values of these variables.

------------------------------------------------------------------------

## 🧪 Current implementation notes

-   The Supervisor uses structured JSON internally because the graph
    needs machine-readable routing decisions. This is separate from the
    user-facing travel response.
-   Specialist agents and the final response are instructed to return
    readable text/Markdown. The application also includes output
    handling for responses that arrive as JSON.
-   Prompt inputs are shortened in selected agents to reduce the chance
    of exceeding Groq token-per-minute limits.
-   Flight, hotel, and weather results depend on the data returned by
    their connected services.
-   Search results and model-generated estimates should be checked
    before making real travel or payment decisions.
-   PostgreSQL checkpointing is enabled only when a valid `DATABASE_URL`
    is provided.

------------------------------------------------------------------------

## 🛣️ Possible future improvements

-   Add stronger validation and retry handling for malformed model
    responses.
-   Improve source links and citations in flight, hotel, and destination
    research.
-   Add clearer cost breakdowns and currency handling.
-   Add export options such as PDF.
-   Add automated tests for supervisor routing, agent execution,
    approval, and graph resumption.
-   Improve handling of unavailable APIs, rate limits, and incomplete
    MCP results.
-   Add booking-provider integrations only when supported by reliable
    availability and booking APIs.

------------------------------------------------------------------------

## ⚠️ Disclaimer

TripPilot AI is a travel research and planning assistant. It provides
suggestions and estimates based on model output and connected data
sources. It does not guarantee accuracy, live availability, fares, hotel
rates, weather conditions, or reservations. Always verify important
details with the relevant airline, hotel, service provider, or official
source before booking.

------------------------------------------------------------------------

## 👨‍💻 About the project

TripPilot AI is a hands-on multi-agent application developed through
iterative experimentation, integration, debugging, and customization.
Its current implementation brings together a Streamlit interface,
LangGraph orchestration, Groq-powered agents, MCP tool connections,
human approval, and downloadable travel plans.

The README describes the current workflow and configuration. Update it
as the implementation evolves.
