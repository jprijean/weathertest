# How to Restart the API Server

## Important: The server MUST be restarted after code changes!

The `/weather-alerts` endpoint was added to the code, but the server is still running the old version.

## Steps to Restart:

1. **Find the terminal/command prompt where the API server is running**
   - Look for a window showing "Uvicorn running on http://127.0.0.1:8000"
   - Or "INFO:     Uvicorn running on..."

2. **Stop the server:**
   - Press `Ctrl+C` in that terminal
   - Wait until it says "Shutting down" or the prompt returns

3. **Restart the server:**
   ```powershell
   cd C:\Users\jprijean\Documents\openprojectweather_global\amazon_weather_alerts
   .\venv\Scripts\Activate.ps1
   python api.py
   ```

   OR if using uvicorn directly:
   ```powershell
   cd C:\Users\jprijean\Documents\openprojectweather_global\amazon_weather_alerts
   .\venv\Scripts\Activate.ps1
   uvicorn api:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Verify it's working:**
   - Open http://localhost:8000/docs in your browser
   - You should see `/weather-alerts` in the list of endpoints
   - Or test: http://localhost:8000/weather-alerts (should return `[]`)

5. **Refresh your frontend page** and try adding an alert again

## Using --reload flag (Recommended)

If you use `uvicorn api:app --reload`, the server will automatically restart when you change the code. This is helpful during development.

## Troubleshooting

If the endpoint still doesn't work after restarting:

1. Check that you're in the correct directory (`amazon_weather_alerts`)
2. Make sure you're using the virtual environment (`.venv\Scripts\Activate.ps1`)
3. Clear Python cache: Delete the `__pycache__` folder if it exists
4. Check for any error messages when starting the server
5. Verify the file `api.py` has the weather-alerts endpoints (lines 559-768)

