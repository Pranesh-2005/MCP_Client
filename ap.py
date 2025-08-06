from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
import os
from dotenv import load_dotenv
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastMCP server for Weather, GitHub, and Indian Rail tools (SSE)
mcp = FastMCP("weather-github-rail")

# Constants
NWS_API_BASE = "https://api.weather.gov"
GITHUB_API_BASE = "https://api.github.com"
USER_AGENT = "weather-github-app/1.0"
INDIAN_RAIL_API_KEY = os.getenv("INDIAN_RAIL_API_KEY")
INDIAN_RAIL_BASE_URL = "https://indianrailapi.com/api/v2"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# --- HTTP helpers ---

async def make_nws_request(url: str) -> dict[str, Any] | None:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"NWS API error: {e}")
            return None

async def make_github_request(url: str) -> dict[str, Any] | None:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github.v3+json"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return None

async def fetch_data(url: str) -> dict:
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Fetch data error: {e}")
        return {"error": str(e)}

# --- Weather Tools ---

def format_alert(feature: dict) -> str:
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state."""
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)
    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."
    if not data["features"]:
        return "No active alerts for this state."
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location."""
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)
    if not points_data:
        return "Unable to fetch forecast data for this location."
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)
    if not forecast_data:
        return "Unable to fetch detailed forecast."
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)
    return "\n---\n".join(forecasts)

# --- GitHub Read-Only Tools ---

@mcp.tool()
async def get_github_user(username: str) -> str:
    """Get public GitHub user information."""
    url = f"{GITHUB_API_BASE}/users/{username}"
    data = await make_github_request(url)
    if not data:
        return f"Unable to fetch user information for {username}"
    return f"""
Username: {data.get('login', 'N/A')}
Name: {data.get('name', 'N/A')}
Bio: {data.get('bio', 'No bio available')}
Public Repos: {data.get('public_repos', 0)}
Followers: {data.get('followers', 0)}
Following: {data.get('following', 0)}
Location: {data.get('location', 'N/A')}
Company: {data.get('company', 'N/A')}
Blog: {data.get('blog', 'N/A')}
Created: {data.get('created_at', 'N/A')}
"""

@mcp.tool()
async def get_github_repos(username: str, limit: int = 10) -> str:
    """Get public GitHub repositories for a user."""
    limit = min(limit, 50)
    url = f"{GITHUB_API_BASE}/users/{username}/repos?sort=updated&per_page={limit}"
    data = await make_github_request(url)
    if not data:
        return f"Unable to fetch repositories for {username}"
    repos = []
    for repo in data:
        repo_info = f"""
Name: {repo.get('name', 'N/A')}
Description: {repo.get('description', 'No description')}
Language: {repo.get('language', 'N/A')}
Stars: {repo.get('stargazers_count', 0)}
Forks: {repo.get('forks_count', 0)}
Updated: {repo.get('updated_at', 'N/A')}
URL: {repo.get('html_url', 'N/A')}
"""
        repos.append(repo_info)
    return "\n---\n".join(repos)

@mcp.tool()
async def get_github_repo_info(owner: str, repo: str) -> str:
    """Get detailed information about a public GitHub repository."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    data = await make_github_request(url)
    if not data:
        return f"Unable to fetch repository information for {owner}/{repo}"
    return f"""
Repository: {data.get('full_name', 'N/A')}
Description: {data.get('description', 'No description')}
Language: {data.get('language', 'N/A')}
Stars: {data.get('stargazers_count', 0)}
Forks: {data.get('forks_count', 0)}
Watchers: {data.get('watchers_count', 0)}
Open Issues: {data.get('open_issues_count', 0)}
Size: {data.get('size', 0)} KB
Default Branch: {data.get('default_branch', 'N/A')}
Created: {data.get('created_at', 'N/A')}
Updated: {data.get('updated_at', 'N/A')}
License: {data.get('license', {}).get('name', 'N/A') if data.get('license') else 'N/A'}
URL: {data.get('html_url', 'N/A')}
Clone URL: {data.get('clone_url', 'N/A')}
"""

@mcp.tool()
async def search_github_repos(query: str, limit: int = 10) -> str:
    """Search public GitHub repositories."""
    limit = min(limit, 30)
    url = f"{GITHUB_API_BASE}/search/repositories?q={query}&sort=stars&order=desc&per_page={limit}"
    data = await make_github_request(url)
    if not data or 'items' not in data:
        return f"Unable to search repositories for query: {query}"
    repos = []
    for repo in data['items']:
        repo_info = f"""
Name: {repo.get('full_name', 'N/A')}
Description: {repo.get('description', 'No description')}
Language: {repo.get('language', 'N/A')}
Stars: {repo.get('stargazers_count', 0)}
Forks: {repo.get('forks_count', 0)}
URL: {repo.get('html_url', 'N/A')}
"""
        repos.append(repo_info)
    return "\n---\n".join(repos)

@mcp.tool()
async def get_github_issues(owner: str, repo: str, state: str = "open", limit: int = 10) -> str:
    """Get public issues for a GitHub repository."""
    limit = min(limit, 30)
    if state not in ["open", "closed", "all"]:
        state = "open"
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues?state={state}&per_page={limit}"
    data = await make_github_request(url)
    if not data:
        return f"Unable to fetch issues for {owner}/{repo}"
    issues = []
    for issue in data:
        labels = ", ".join([label['name'] for label in issue.get('labels', [])])
        issue_info = f"""
#{issue.get('number', 'N/A')}: {issue.get('title', 'No title')}
State: {issue.get('state', 'N/A')}
Author: {issue.get('user', {}).get('login', 'N/A')}
Labels: {labels if labels else 'None'}
Created: {issue.get('created_at', 'N/A')}
URL: {issue.get('html_url', 'N/A')}
"""
        issues.append(issue_info)
    return "\n---\n".join(issues)

@mcp.tool()
async def get_github_commits(owner: str, repo: str, limit: int = 10) -> str:
    """Get recent commits for a public GitHub repository."""
    limit = min(limit, 20)
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits?per_page={limit}"
    data = await make_github_request(url)
    if not data:
        return f"Unable to fetch commits for {owner}/{repo}"
    commits = []
    for commit in data:
        commit_info = f"""
SHA: {commit.get('sha', 'N/A')[:8]}
Message: {commit.get('commit', {}).get('message', 'No message')[:100]}{'...' if len(commit.get('commit', {}).get('message', '')) > 100 else ''}
Author: {commit.get('commit', {}).get('author', {}).get('name', 'N/A')}
Date: {commit.get('commit', {}).get('author', {}).get('date', 'N/A')}
URL: {commit.get('html_url', 'N/A')}
"""
        commits.append(commit_info)
    return "\n---\n".join(commits)

# --- Indian Rail Tools ---

@mcp.tool()
async def station_name_to_code(station_name: str) -> str:
    """Convert a station name to its code using Indian Rail API."""
    if not INDIAN_RAIL_API_KEY:
        return "Indian Rail API key not configured"
    
    station_name = station_name.upper()
    url = f"{INDIAN_RAIL_BASE_URL}/StationNameToCode/apikey/{INDIAN_RAIL_API_KEY}/StationName/{station_name}"
    data = await fetch_data(url)
    
    if "error" in data:
        return f"Error fetching station code: {data['error']}"
    
    if data.get('ResponseCode') == 200 and data.get('Station'):
        stations = data['Station']
        if isinstance(stations, list) and stations:
            result = "Station codes found:\n"
            for station in stations[:5]:
                result += f"Name: {station.get('StationName', 'N/A')}\n"
                result += f"Code: {station.get('StationCode', 'N/A')}\n"
                result += f"State: {station.get('StateName', 'N/A')}\n---\n"
            return result
        else:
            return f"No stations found for '{station_name}'"
    else:
        return f"No stations found for '{station_name}'"

@mcp.tool()
async def get_train_schedule_indian_rail(train_number: str) -> str:
    """Get the schedule of a train by its number using Indian Rail API."""
    if not INDIAN_RAIL_API_KEY:
        return "Indian Rail API key not configured"
    
    url = f"{INDIAN_RAIL_BASE_URL}/TrainSchedule/apikey/{INDIAN_RAIL_API_KEY}/TrainNumber/{train_number}"
    data = await fetch_data(url)
    
    if "error" in data:
        return f"Error fetching train schedule: {data['error']}"
    
    if data.get('ResponseCode') == 200 and data.get('Route'):
        train_info = f"Train {train_number} Schedule:\n"
        train_info += f"Train Name: {data.get('TrainName', 'N/A')}\n"
        train_info += f"Train Number: {data.get('TrainNumber', 'N/A')}\n\n"
        
        route = data['Route']
        if isinstance(route, list):
            train_info += "Schedule:\n"
            for station in route[:10]:
                train_info += f"Station: {station.get('StationName', 'N/A')} ({station.get('StationCode', 'N/A')})\n"
                train_info += f"Arrival: {station.get('ArrivalTime', 'N/A')} | Departure: {station.get('DepartureTime', 'N/A')}\n"
                train_info += f"Distance: {station.get('DistanceFromSource', 'N/A')} km\n---\n"
        return train_info
    else:
        return f"No schedule found for train {train_number}"

@mcp.tool()
async def get_all_trains_on_station(station_code: str) -> str:
    """Get all trains arriving at or departing from a station using Indian Rail API."""
    if not INDIAN_RAIL_API_KEY:
        return "Indian Rail API key not configured"
    
    station_code = station_code.upper()
    url = f"{INDIAN_RAIL_BASE_URL}/AllTrainOnStation/apikey/{INDIAN_RAIL_API_KEY}/StationCode/{station_code}"
    data = await fetch_data(url)
    
    if "error" in data:
        return f"Error fetching trains for station: {data['error']}"
    
    if data.get('ResponseCode') == 200 and data.get('Trains'):
        trains = data['Trains']
        if trains:
            result = f"Trains at station {station_code}:\n"
            for train in trains[:15]:
                result += f"Train: {train.get('TrainName', 'N/A')} ({train.get('TrainNumber', 'N/A')})\n"
                result += f"Arrival: {train.get('ArrivalTime', 'N/A')} | Departure: {train.get('DepartureTime', 'N/A')}\n"
                result += f"Source: {train.get('SourceStationName', 'N/A')} | Destination: {train.get('DestinationStationName', 'N/A')}\n---\n"
            return result
        else:
            return f"No trains found for station {station_code}"
    else:
        return f"No trains found for station {station_code}"

# --- Starlette App ---

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")
    
    async def handle_sse(request: Request):
        try:
            logger.info("SSE connection initiated")
            async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,
            ) as (read_stream, write_stream):
                logger.info("SSE connection established, starting MCP server")
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )
        except Exception as e:
            logger.error(f"Error in SSE handler: {e}")
            raise
    
    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

if __name__ == "__main__":
    # Get the MCP server instance
    mcp_server = mcp._mcp_server
    
    import argparse
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    args = parser.parse_args()
    
    print("Available tools:")
    print("Weather tools: get_alerts, get_forecast")
    print("GitHub tools (read-only): get_github_user, get_github_repos, get_github_repo_info, get_github_issues, search_github_repos, get_github_commits")
    print("Indian Rail tools: station_name_to_code, get_train_schedule_indian_rail, get_all_trains_on_station")
    
    if not GITHUB_TOKEN:
        print("Note: No GITHUB_TOKEN set. Using public API with lower rate limits.")
    else:
        print("Note: GITHUB_TOKEN found. Using authenticated API with higher rate limits.")
    
    if not INDIAN_RAIL_API_KEY:
        print("Note: INDIAN_RAIL_API_KEY not set. Indian Rail tools will not work.")
    else:
        print("Note: INDIAN_RAIL_API_KEY found. Indian Rail tools are available.")
    
    # Create the Starlette app
    starlette_app = create_starlette_app(mcp_server, debug=True)
    
    # Run the server
    try:
        uvicorn.run(starlette_app, host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise