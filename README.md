# LeadFlow — E-commerce Lead Gen Agent

A complete lead generation agent that finds, qualifies, and displays
e-commerce leads using Google Maps + Claude AI.

---

## Setup (5 minutes)

### 1. Install Python dependency
```
pip install requests
```

### 2. Get your API keys

**Claude API key** (for AI qualification):
- Go to https://console.anthropic.com
- Create an account → API Keys → Create Key
- Copy the key

**Google Places API key** (for finding businesses):
- Go to https://console.cloud.google.com
- Create a project → Enable "Places API" → Create Credentials → API Key
- Note: Google gives $200/month free credit — more than enough to start

### 3. Add your keys to agent.py
Open agent.py and replace these two lines near the top:
```python
ANTHROPIC_API_KEY = "your-api-key-here"
GOOGLE_API_KEY = "your-google-api-key"
```

### 4. Customize your search
Also in agent.py, edit these to match your target market:
```python
SEARCH_LOCATION = "New York, NY"   # Your target city
SEARCH_QUERIES = [...]              # Types of e-commerce stores to find
```

---

## Running the agent

```bash
python agent.py
```

This will:
1. Search Google Maps for e-commerce businesses
2. Get their website, phone, rating
3. Send each lead to Claude for AI qualification
4. Score them 1-10 and label as Hot / Warm / Cold
5. Generate a personalized outreach pitch for each
6. Save results to output/leads.json

---

## Viewing the dashboard

1. Open `dashboard.html` in your browser (just double-click it)
2. Click "Load leads.json file"
3. Navigate to `output/leads.json` and open it
4. Browse, filter, and copy outreach pitches

---

## Tips for finding first clients

1. Run the agent for a city, export the CSV (output/leads.csv)
2. Show the dashboard to a local marketing agency
3. Offer 50 free leads in exchange for feedback
4. Charge $300-800/month for ongoing lead delivery

---

## File structure

```
leadgen/
├── agent_free.py          ← Main agent (run this)
├── dashboard.html    ← Open in browser to view leads
├── requirements.txt  ← Python dependencies
├── README.md         ← This file
└── output/
    ├── leads.json    ← Generated after running agent
    └── leads.csv     ← Spreadsheet backup
```
