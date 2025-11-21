# Weather Alerts API - Stitch Integration Guide

This document explains how the `api_server.py` FastAPI application works and how to use it with Stitch or any frontend application.

## Overview

The API server (`api_server.py`) is a simple REST API that reads CSV files from the `data/` folder and serves them as endpoints. This allows frontend applications like Stitch to access the weather alert data without directly reading CSV files.

## How It Works

### Architecture

```
┌─────────────┐         ┌──────────────┐         ┌──────────┐
│   Frontend  │ ──────> │  FastAPI     │ ──────> │ CSV Files│
│   (Stitch)  │ <────── │  Server      │ <────── │ (data/)  │
└─────────────┘         └──────────────┘         └──────────┘
```

1. **Frontend requests** data via HTTP GET requests
2. **FastAPI server** receives the request
3. **CSV reader function** reads the appropriate CSV file
4. **Data is converted** from CSV rows to JSON objects
5. **JSON response** is sent back to the frontend

### Key Components

#### 1. FastAPI Application Setup

```python
app = FastAPI(title="Weather Alerts API", version="1.0.0")
```

This creates the main FastAPI application instance. FastAPI automatically:
- Generates OpenAPI documentation at `/docs`
- Validates request/response data
- Handles JSON serialization

#### 2. CORS Middleware

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Why CORS is needed:** Browsers block cross-origin requests by default. Since Stitch runs in a browser and the API runs on a different port, CORS middleware allows the browser to make requests to our API.

**What each setting does:**
- `allow_origins=["*"]` - Allows requests from any domain
- `allow_credentials=True` - Allows cookies/auth headers
- `allow_methods=["*"]` - Allows all HTTP methods (GET, POST, etc.)
- `allow_headers=["*"]` - Allows any request headers

#### 3. CSV Reading Function

```python
def read_csv_file(filename: str) -> List[Dict]:
    """Safely read a CSV file and return list of dictionaries."""
```

**How it works:**

1. **File Path Construction:**
   ```python
   filepath = DATA_DIR / filename
   ```
   - Combines the `data/` directory with the filename
   - Uses `Path` from `pathlib` for safe path handling

2. **File Existence Check:**
   ```python
   if not filepath.exists():
       raise HTTPException(status_code=404, ...)
   ```
   - Checks if the CSV file exists
   - Returns 404 error if file is missing

3. **CSV Reading:**
   ```python
   with open(filepath, 'r', encoding='utf-8', newline='') as f:
       reader = csv.DictReader(f)
       return list(reader)
   ```
   - Opens file with UTF-8 encoding (supports international characters)
   - Uses `csv.DictReader` which automatically:
     - Reads the first row as column names (headers)
     - Converts each subsequent row into a dictionary
     - Keys = column names, Values = cell values

4. **Error Handling:**
   - Catches any exceptions during file reading
   - Returns HTTP 500 error with descriptive message

**Example CSV to JSON conversion:**

**Input CSV (`data/locations.csv`):**
```csv
building_code,owner_emails,longitude,latitude
BREST001,"jprijean@gmail.com",-4.4861,48.3904
BREST002,"jprijean@gmail.com",-4.4890,48.3950
```

**Output JSON:**
```json
[
  {
    "building_code": "BREST001",
    "owner_emails": "jprijean@gmail.com",
    "longitude": "-4.4861",
    "latitude": "48.3904"
  },
  {
    "building_code": "BREST002",
    "owner_emails": "jprijean@gmail.com",
    "longitude": "-4.4890",
    "latitude": "48.3950"
  }
]
```

#### 4. Endpoint Creation

Endpoints are created using **decorators** in FastAPI. Here's how they work:

```python
@app.get("/locations")
def get_locations():
    """Return all locations from data/locations.csv."""
    return read_csv_file("locations.csv")
```

**Breaking it down:**

- `@app.get("/locations")` - This is a **decorator** that:
  - Registers the function as an HTTP GET endpoint
  - Maps the URL path `/locations` to this function
  - FastAPI automatically handles the HTTP request/response

- `def get_locations():` - This function:
  - Runs when someone visits `/locations`
  - Calls `read_csv_file()` to get the data
  - Returns the data (FastAPI automatically converts it to JSON)

**All three endpoints work the same way:**

| Endpoint | CSV File | Function |
|----------|----------|----------|
| `/locations` | `data/locations.csv` | `get_locations()` |
| `/results` | `data/results.csv` | `get_results()` |
| `/interventions` | `data/interventions.csv` | `get_interventions()` |

## How to Use

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `fastapi` - The web framework
- `uvicorn` - The ASGI server that runs FastAPI
- `python-dotenv` - For loading environment variables (already included)

### 2. Configure API Settings (Optional)

You can optionally configure the API host and port in your `.env` file:

```env
# Optional - API Server Configuration
API_HOST=127.0.0.1
API_PORT=8000
```

**Default values:**
- `API_HOST` defaults to `127.0.0.1` (localhost only)
- `API_PORT` defaults to `8000`

**Why configure these?**
- Change `API_HOST` to `0.0.0.0` if you want to allow access from other devices on your network
- Change `API_PORT` if port 8000 is already in use

### 3. Start the Server

```bash
python api_server.py
```

You should see output like:
```
INFO:     Started server process
INFO:     Started server process [127.0.0.1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 3. Access the Endpoints

#### Root Endpoint (API Info)
```bash
http://localhost:8000/
```
Returns:
```json
{
  "name": "Weather Alerts API",
  "version": "1.0.0",
  "endpoints": ["/locations", "/results", "/interventions"]
}
```

#### Get All Locations
```bash
http://localhost:8000/locations
```

#### Get All Results
```bash
http://localhost:8000/results
```

#### Get All Interventions
```bash
http://localhost:8000/interventions
```

### 4. Using with Stitch or Frontend

#### JavaScript/Fetch Example

```javascript
// Fetch locations
fetch('http://localhost:8000/locations')
  .then(response => response.json())
  .then(data => {
    console.log(data);
    // data is an array of location objects
  })
  .catch(error => console.error('Error:', error));
```

#### Using in Stitch

1. **Start the API server** (keep it running)

2. **In Stitch**, make HTTP requests to:
   - `http://localhost:8000/locations`
   - `http://localhost:8000/results`
   - `http://localhost:8000/interventions`

3. **Handle the JSON response** - Each endpoint returns an array of objects

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Visit these URLs in your browser to see:
- All available endpoints
- Request/response formats
- Interactive API testing interface

## Data Structure

### Locations Endpoint (`/locations`)

Returns data from `data/locations.csv`:

```json
[
  {
    "building_code": "BREST001",
    "owner_emails": "jprijean@gmail.com",
    "longitude": "-4.4861",
    "latitude": "48.3904"
  }
]
```

**Columns:**
- `building_code` - Unique identifier for the building
- `owner_emails` - Comma-separated list of owner email addresses
- `longitude` - Longitude coordinate
- `latitude` - Latitude coordinate

### Results Endpoint (`/results`)

Returns data from `data/results.csv`:

```json
[
  {
    "building_code": "BREST001",
    "timestamp": "2025-11-02T12:00:00",
    "windspeed_val": "8.63",
    "precipitation_val": "0.68",
    "intervention_id": "no-alert",
    "severity": "low"
  }
]
```

**Columns:**
- `building_code` - Building identifier
- `timestamp` - When the weather check was performed (ISO format)
- `windspeed_val` - Wind speed value
- `precipitation_val` - Precipitation amount
- `intervention_id` - ID of the intervention triggered (or "no-alert")
- `severity` - Severity level of the alert

### Interventions Endpoint (`/interventions`)

Returns data from `data/interventions.csv`:

```json
[
  {
    "id": "high_wind_alert",
    "title": "Vent Fort Détecté",
    "description": "Des vents forts ont été détectés..."
  }
]
```

**Columns:**
- `id` - Unique intervention identifier
- `title` - Short title of the intervention
- `description` - Detailed description of the intervention

## Error Handling

The API handles errors gracefully:

### 404 - File Not Found
```json
{
  "detail": "File locations.csv not found"
}
```
Occurs when the CSV file doesn't exist in the `data/` folder.

### 500 - Server Error
```json
{
  "detail": "Error reading results.csv: [error message]"
}
```
Occurs when there's a problem reading the file (permissions, corruption, etc.).

## Troubleshooting

### Server Won't Start

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Port Already in Use

**Problem:** `Address already in use`

**Solution:** Another process is using port 8000. Either:
- Stop the other process
- Change the port in `api_server.py`:
  ```python
  uvicorn.run(app, host="127.0.0.1", port=8001)  # Use different port
  ```

### CORS Errors in Browser

**Problem:** Browser shows CORS error even with middleware enabled

**Solution:** 
- Make sure the CORS middleware is configured (it is in the code)
- Check that the server is actually running
- Verify the URL is correct (http://localhost:8000, not https://)

### Empty Response

**Problem:** Endpoint returns `[]` (empty array)

**Solution:** 
- Check that the CSV file exists in the `data/` folder
- Verify the CSV file has data rows (not just headers)
- Check file permissions

### CSV Not Updating

**Problem:** Changes to CSV files don't appear in API responses

**Solution:** 
- The API reads files on each request (no caching)
- Refresh your browser or make a new request
- Verify the CSV file was saved correctly

## Code Structure Summary

```
api_server.py
│
├── Imports & Setup
│   ├── FastAPI framework
│   ├── CORS middleware
│   └── CSV & file utilities
│
├── Configuration
│   ├── FastAPI app instance
│   ├── CORS middleware setup
│   └── DATA_DIR path
│
├── Helper Function
│   └── read_csv_file() - Safe CSV reader
│       ├── File existence check
│       ├── CSV parsing
│       └── Error handling
│
└── Endpoints (3 total)
    ├── GET / - Root/API info
    ├── GET /locations - Locations data
    ├── GET /results - Results data
    └── GET /interventions - Interventions data
```

## Key Concepts Explained

### What is FastAPI?

FastAPI is a modern Python web framework that:
- Makes it easy to create REST APIs
- Automatically generates API documentation
- Validates data types
- Is fast and efficient

### What is a Decorator?

The `@app.get()` syntax is a **decorator**. It's Python syntax that:

```python
@app.get("/locations")
def get_locations():
    ...
```

Is equivalent to:
```python
def get_locations():
    ...
get_locations = app.get("/locations")(get_locations)
```

The decorator "wraps" the function and tells FastAPI:
- What URL path to use (`/locations`)
- What HTTP method to accept (`GET`)
- What function to call when someone visits that URL

### What is CORS?

**CORS** (Cross-Origin Resource Sharing) is a browser security feature that prevents websites from making requests to different domains/ports. Our middleware tells the browser: "It's OK, allow requests to this API."

## Next Steps

- **Add pagination** if datasets get large
- **Add filtering** (e.g., filter results by building_code)
- **Add authentication** if you need to secure the API
- **Add caching** if CSV files are read frequently
- **Add rate limiting** to prevent abuse

## Summary

The `api_server.py` file is a simple, straightforward API that:
1. Uses FastAPI to create HTTP endpoints
2. Reads CSV files from the `data/` folder
3. Converts CSV rows to JSON objects
4. Returns JSON to the frontend
5. Handles errors gracefully
6. Supports CORS for browser access

Each endpoint follows the same pattern: define route → read CSV → return JSON.

