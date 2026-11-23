
import os
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient

from config import (
    AVIATION_STACK_API_KEY,
    OPENWEATHER_API_KEY,
    TAVILY_API_KEY,
)

# ------------------------
# Project Paths
# ------------------------

PROJECT_DIR = Path(__file__).resolve().parent
TRAVEL1_DIR = PROJECT_DIR.parent

AVIATIONSTACK_DIR = TRAVEL1_DIR / "aviationstack-mcp"
AVIATIONSTACK_PYTHON = (
    AVIATIONSTACK_DIR / ".venv" / "Scripts" / "python.exe"
)

WEATHER_SERVER = PROJECT_DIR / "weather_mcp_server.py"

# ------------------------
# Validate MCP Server Paths
# ------------------------

if not AVIATIONSTACK_PYTHON.exists():
    raise FileNotFoundError(
        f"AviationStack Python executable not found: {AVIATIONSTACK_PYTHON}"
    )

if not WEATHER_SERVER.exists():
    raise FileNotFoundError(
        f"Weather MCP server not found: {WEATHER_SERVER}"
    )

# ------------------------
# Create MCP Client
# ------------------------

client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}",
        },

        "aviationstack": {
            "transport": "stdio",
            "command": str(AVIATIONSTACK_PYTHON),
            "args": [
                "-m",
                "aviationstack_mcp",
                "mcp",
                "run",
            ],
            "env": {
                **os.environ,
                "AVIATION_STACK_API_KEY": AVIATION_STACK_API_KEY or "",
            },
        },

        "weather": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [
                str(WEATHER_SERVER),
            ],
            "env": {
                **os.environ,
                "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY or "",
            },
        },
    }
)

# ------------------------
# Cache Tools
# ------------------------

_tools_cache = None


async def get_tools():
    global _tools_cache

    if _tools_cache is None:
        try:
            _tools_cache = await client.get_tools()

        except Exception as e:
            print("\n========== FULL ERROR ==========")
            print(type(e))
            print(repr(e))

            if hasattr(e, "exceptions"):
                print("\nSUB EXCEPTIONS:")

                for i, sub in enumerate(e.exceptions):
                    print(f"\n--- Exception {i + 1} ---")
                    print(type(sub))
                    print(repr(sub))

            raise

    return _tools_cache


async def call_tool(tool_name: str, args: dict = None):
    tools = await get_tools()

    tool = next(
        (tool for tool in tools if tool.name == tool_name),
        None,
    )

    if tool is None:
        raise ValueError(f"Tool '{tool_name}' not found")

    return await tool.ainvoke(args or {})


# ------------------------
# Tavily MCP Tools
# ------------------------

async def tavily_search(query: str):
    return await call_tool(
        "tavily_search",
        {"query": query},
    )


# ------------------------
# AviationStack MCP Tools
# ------------------------

async def list_airports(search: str = "", limit: int = 10):
    return await call_tool(
        "list_airports",
        {"search": search, "limit": limit, "offset": 0},
    )


async def list_airlines(search: str = "", limit: int = 10):
    return await call_tool(
        "list_airlines",
        {"search": search, "limit": limit, "offset": 0},
    )


# ------------------------
# Weather MCP Tools
# ------------------------

async def current_weather(city: str):
    return await call_tool(
        "get_current_weather",
        {"city": city},
    )


async def forecast(city: str):
    return await call_tool(
        "get_forecast",
        {"city": city},
    )
