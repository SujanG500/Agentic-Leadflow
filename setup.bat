@echo off
echo.
echo ======================================
echo   LeadFlow — Installing dependencies
echo ======================================
echo.

pip install requests playwright
python -m playwright install chromium

echo.
echo ======================================
echo   Done! Now:
echo   1. Open agent_free.py in Notepad
echo   2. Paste your Groq API key
echo   3. Set SEARCH_QUERY and SEARCH_CITY
echo   4. Run: python agent_free.py
echo ======================================
echo.
pause
