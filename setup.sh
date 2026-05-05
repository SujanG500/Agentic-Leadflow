#!/bin/bash
# LeadFlow Free Setup Script
# Run this once to install everything

echo ""
echo "======================================"
echo "  LeadFlow — Installing dependencies"
echo "======================================"
echo ""

# Install Python packages
pip install requests playwright

# Install Playwright's browser (Chromium — free)
python -m playwright install chromium

echo ""
echo "======================================"
echo "  Done! Now:"
echo "  1. Open agent_free.py"
echo "  2. Paste your Groq API key (console.groq.com)"
echo "  3. Set your SEARCH_QUERY and SEARCH_CITY"
echo "  4. Run: python agent_free.py"
echo "======================================"
echo ""
