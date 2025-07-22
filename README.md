# weather-mcp-python

A FastAPI-based Model Context Protocol (MCP) server for OpenWeatherMap’s free API. Provides a single SSE endpoint to retrieve:

* **Current weather**
* **5-day / 3-hour forecast**
* **One‑Call data** (current, minutely, hourly, daily)
* **Historical weather** (up to 5 days ago)

---

## Features

* **Single `/mcp` endpoint**: JSON-RPC–style requests over Server-Sent Events (SSE).
* **Async I/O**: Built with FastAPI and httpx for high concurrency.
* **Geocoding**: Automatically resolves city names to coordinates.
* **Extensible**: Add new methods (e.g., air pollution) by following the existing pattern.

---

## Prerequisites

* **Python 3.8+**
* **pip** package manager
* An **OpenWeatherMap** account (free tier) with an API key: [https://openweathermap.org/api](https://openweathermap.org/api)

---

## Installation

1. **Clone the repository**

   ```bash
   git clone <repo-url> weather-mcp-backend
   cd weather-mcp-backend
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # macOS/Linux
   .\.venv\Scripts\activate    # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

Create a `.env` file in the project root:

```ini
OPENWEATHER_API_KEY=your_openweathermap_api_key_here
```

This environment variable is loaded by `python-dotenv` at runtime.

---

## Project Structure

```
weather-mcp-backend/
├── .env                  # API key configuration
├── Dockerfile            # Containerization
├── docker-compose.yml    # Optional compose setup
├── main.py               # Application entrypoint
├── README.md             # This documentation
├── requirements.txt      # Python dependencies
└── .dockerignore         # Files to ignore in Docker builds
```

---

## Usage

### Running Locally

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

* **Endpoint**: `http://localhost:8000/mcp`
* **Content-Type**: `text/event-stream`

### Supported MCP Methods

| Method               | Description                                 | Params                                                           |
| -------------------- | ------------------------------------------- | ---------------------------------------------------------------- |
| `weather.current`    | Current weather by city name                | `{ city: string }`                                               |
| `weather.forecast`   | 5-day / 3-hour forecast by city name        | `{ city: string }`                                               |
| `weather.everything` | One‑Call (current, minutely, hourly, daily) | `{ city: string }` **or** `{ lat, lon }`                         |
| `weather.historical` | Historical data (up to 5 days ago)          | `{ city: string, dt: UNIX timestamp }` **or** `{ lat, lon, dt }` |

### Example Request

```json
{
  "id": "1",
  "method": "weather.current",
  "params": { "city": "Karachi" }
}
```

### JavaScript Client Example

```js
const payload = {
  id:     "1",
  method: "weather.current",
  params: { city: "Karachi" }
};

const es = new EventSource("/mcp", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload)
});

es.onmessage = e => {
  const msg = JSON.parse(e.data);
  if (
```
