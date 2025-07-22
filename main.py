import os, json
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv
import httpx

# Load OPENWEATHER_API_KEY from .env
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing OPENWEATHER_API_KEY in .env")

app = FastAPI()

async def geocode(city: str) -> tuple[float, float]:
    """Convert a city name to (lat, lon) coordinates."""
    url = "http://api.openweathermap.org/geo/1.0/direct"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params={
            "q": city,
            "limit": 1,
            "appid": API_KEY
        })
        resp.raise_for_status()
        data = resp.json()
    if not data:
        raise ValueError(f"City '{city}' not found")
    return data[0]["lat"], data[0]["lon"]

async def mcp_stream(request: Request):
    """
    Accepts a JSON-RPC body:
      { id, method: "weather.xxx", params: { … } }
    Yields SSE “data: {...}” events, then a final { done: true }.
    """
    payload = await request.json()
    msg_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params", {})

    try:
        # --- 1) Current weather ---
        if method == "weather.current":
            city = params.get("city")
            if not city:
                raise ValueError("Missing param: city")
            url = "https://api.openweathermap.org/data/2.5/weather"
            async with httpx.AsyncClient() as client:
                res = await client.get(url, params={
                    "q": city,
                    "appid": API_KEY,
                    "units": "metric"
                })
                res.raise_for_status()
                result = res.json()

        # --- 2) 5‑day / 3‑hour forecast ---
        elif method == "weather.forecast":
            city = params.get("city")
            if not city:
                raise ValueError("Missing param: city")
            url = "https://api.openweathermap.org/data/2.5/forecast"
            async with httpx.AsyncClient() as client:
                res = await client.get(url, params={
                    "q": city,
                    "appid": API_KEY,
                    "units": "metric"
                })
                res.raise_for_status()
                result = res.json()

        # --- 3) One‑Call “everything” (current, minutely, hourly, daily) ---
        elif method == "weather.everything":
            if "city" in params:
                lat, lon = await geocode(params["city"])
            else:
                lat = params.get("lat")
                lon = params.get("lon")
                if lat is None or lon is None:
                    raise ValueError("Provide either city or lat & lon")
            url = "https://api.openweathermap.org/data/2.5/onecall"
            async with httpx.AsyncClient() as client:
                res = await client.get(url, params={
                    "lat": lat,
                    "lon": lon,
                    "appid": API_KEY,
                    "units": "metric"
                })
                res.raise_for_status()
                result = res.json()

        # --- 4) Historical (Time Machine up to 5 days back) ---
        elif method == "weather.historical":
            dt = params.get("dt")
            if not dt:
                raise ValueError("Missing param: dt (UNIX timestamp)")
            if "city" in params:
                lat, lon = await geocode(params["city"])
            else:
                lat = params.get("lat")
                lon = params.get("lon")
                if lat is None or lon is None:
                    raise ValueError("Provide either city or lat & lon")
            url = "https://api.openweathermap.org/data/2.5/onecall/timemachine"
            async with httpx.AsyncClient() as client:
                res = await client.get(url, params={
                    "lat": lat,
                    "lon": lon,
                    "dt": dt,
                    "appid": API_KEY,
                    "units": "metric"
                })
                res.raise_for_status()
                result = res.json()

        else:
            raise ValueError(f"Unknown method '{method}'")

        # ── Send the result as one SSE event ───────────────────────────────
        yield f"data: {json.dumps({'id': msg_id, 'result': result})}\n\n"
        # ── Then signal completion ──────────────────────────────────────────
        yield f"data: {json.dumps({'id': msg_id, 'done': True})}\n\n"

    except Exception as e:
        # On error, send an error event
        yield f"data: {json.dumps({'id': msg_id, 'error': str(e)})}\n\n"
        return

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    return EventSourceResponse(mcp_stream(request))
