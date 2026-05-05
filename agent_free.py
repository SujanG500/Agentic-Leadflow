import json
import time
import csv
import os
import re
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# What to search on Google Maps
SEARCH_QUERY = "restaurants"   # change to whatever niche
SEARCH_CITY  = "Kathmandu"               # change to your target city

# How many leads to scrape (keep under 30 to be safe)
MAX_LEADS = 20
# ============================================================


def scrape_google_maps(query, city, max_results):
    """Scrape Google Maps listings using Playwright (free, no API key)."""

    full_query = f"{query} {city}"
    url = f"https://www.google.com/maps/search/{full_query.replace(' ', '+')}"

    leads = []

    print(f"\n  Opening Google Maps for: '{full_query}'")
    print("  (A browser window will open — don't close it)\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel='msedge')
        context = browser.new_context(locale="en-US")
        page = browser.new_page()
        page.set_default_timeout(60000)
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)

        # Scroll the results panel to load more listings
        print("  Scrolling to load listings...")
        try:
            results_panel = page.locator('div[role="feed"]').first
            for _ in range(6):
                results_panel.evaluate("el => el.scrollTop += 600")
                time.sleep(1.2)
        except:
            pass

        # Grab all listing links
        listing_links = page.locator('a[href*="/maps/place/"]').all()
        hrefs = []
        seen = set()
        for link in listing_links:
            href = link.get_attribute("href")
            if href and href not in seen and "/maps/place/" in href:
                seen.add(href)
                hrefs.append(href)

        hrefs = hrefs[:max_results]
        print(f"  Found {len(hrefs)} listings — extracting details...\n")

        for i, href in enumerate(hrefs):
            try:
                print(f"  [{i+1}/{len(hrefs)}] Visiting listing...")
                page.goto(href, wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)

                # Business name
                name = ""
                try:
                    name = page.locator('h1').first.inner_text(timeout=3000).strip()
                except:
                    pass

                # Rating
                rating = ""
                try:
                    rating_el = page.locator('div[jsaction*="pane.rating"]').first
                    rating_text = rating_el.inner_text(timeout=2000)
                    match = re.search(r'(\d\.\d)', rating_text)
                    if match:
                        rating = match.group(1)
                except:
                    pass

                # Address
                address = ""
                try:
                    addr_el = page.locator('button[data-item-id="address"]').first
                    address = addr_el.inner_text(timeout=2000).strip()
                except:
                    pass

                # Website
                website = ""
                try:
                    web_el = page.locator('a[data-item-id="authority"]').first
                    website = web_el.get_attribute("href", timeout=2000) or ""
                except:
                    pass

                # Phone
                phone = ""
                try:
                    phone_el = page.locator('button[data-item-id*="phone"]').first
                    phone = phone_el.inner_text(timeout=2000).strip()
                except:
                    pass

                # Review count
                reviews = ""
                try:
                    rev_el = page.locator('span[aria-label*="reviews"]').first
                    rev_text = rev_el.get_attribute("aria-label", timeout=2000) or ""
                    match = re.search(r'([\d,]+)', rev_text)
                    if match:
                        reviews = match.group(1).replace(",", "")
                except:
                    pass

                if name:
                    leads.append({
                        "name": name,
                        "address": address,
                        "phone": phone,
                        "website": website,
                        "rating": rating or "N/A",
                        "total_ratings": reviews or "0",
                        "maps_url": href,
                    })
                    print(f"     ✓ {name}")

            except Exception as e:
                print(f"     ✗ Skipped: {e}")
                continue

        browser.close()

    print(f"\n  Scraped {len(leads)} leads successfully")
    return leads


def qualify_with_groq(business, api_key):
    """Use Groq's free API to qualify a lead."""

    prompt = f"""You are a lead qualification expert. Analyze this restaurants business listing and qualify it as a sales lead.

Business: {business['name']}
Address: {business['address']}
Phone: {business['phone'] or 'not found'}
Website: {business['website'] or 'not found'}
Rating: {business['rating']} ({business['total_ratings']} reviews)

Respond with ONLY a raw JSON object, no markdown, no explanation:
{{
  "score": <1-10>,
  "tier": "<Hot|Warm|Cold>",
  "reason": "<one sentence assessment>",
  "pain_point": "<most likely business problem they face>",
  "pitch": "<one sentence personalized cold outreach opener>"
}}

Hot (8-10): strong online presence, active reviews, clear e-commerce signals
Warm (5-7): some online presence but unclear digital maturity
Cold (1-4): mainly offline, very few reviews, weak signals"""

    response = None
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 250,
                "temperature": 0.3,
            },
            timeout=30
        )

        raw = response.json()

        # Print full response if no choices key — reveals the real error
        if "choices" not in raw:
            print(f"     Groq said: {json.dumps(raw)}")
            raise Exception("No choices returned")

        text = raw["choices"][0]["message"]["content"].strip()

        # Strip markdown fences if present
        if "```" in text:
            text = re.sub(r"```[a-z]*\n?", "", text).strip()

        return json.loads(text)

    except Exception as e:
        if response is not None:
            print(f"     Groq response: {response.text[:300]}")
        print(f"     AI error: {e}")
        return {
            "score": 5,
            "tier": "Warm",
            "reason": "Auto-qualification failed — review manually",
            "pain_point": "Unknown",
            "pitch": f"Hi, I came across {business['name']} and wanted to reach out."
        }


def run():
    print("\n" + "="*52)
    print("  LEADFLOW — Free Edition (Groq + Playwright)")
    print("="*52)
    print(f"  Query : {SEARCH_QUERY}")
    print(f"  City  : {SEARCH_CITY}")
    print(f"  Limit : {MAX_LEADS} leads")
    print("="*52)

    # Quick API key check
    if GROQ_API_KEY == "your-groq-api-key-here":
        print("\n  ERROR: You need to paste your Groq API key!")
        print("  Get it free at console.groq.com")
        print("  Then replace 'your-groq-api-key-here' at the top of this file.\n")
        return

    # Test Groq key before scraping
    print("\n  Testing Groq API key...")
    test = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5},
        timeout=15
    )
    test_data = test.json()
    if "choices" not in test_data:
        print(f"\n  Groq API key error: {json.dumps(test_data)}")
        print("  Fix your API key then try again.\n")
        return
    print("  Groq API key is working!\n")

    # Step 1: Scrape
    leads = scrape_google_maps(SEARCH_QUERY, SEARCH_CITY, MAX_LEADS)

    if not leads:
        print("\n  No leads found. Try a different query or city.")
        return

    # Step 2: Qualify with Groq
    print(f"\n  Qualifying {len(leads)} leads with AI...\n")
    qualified = []

    for i, lead in enumerate(leads):
        print(f"  [{i+1}/{len(leads)}] Qualifying: {lead['name']}")
        q = qualify_with_groq(lead, GROQ_API_KEY)
        qualified.append({**lead, **q, "searched_at": datetime.now().strftime("%Y-%m-%d %H:%M")})
        time.sleep(0.3)

    # Sort best first
    qualified.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Step 3: Save
    os.makedirs("output", exist_ok=True)

    with open("output/leads.json", "w") as f:
        json.dump(qualified, f, indent=2)

    fields = ["name", "address", "phone", "website", "rating",
              "score", "tier", "reason", "pain_point", "pitch", "searched_at"]
    with open("output/leads.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(qualified)

    # Summary
    hot  = sum(1 for l in qualified if l.get("tier") == "Hot")
    warm = sum(1 for l in qualified if l.get("tier") == "Warm")
    cold = sum(1 for l in qualified if l.get("tier") == "Cold")

    print(f"\n{'='*52}")
    print(f"  DONE!  {len(qualified)} leads saved")
    print(f"  Hot: {hot}   Warm: {warm}   Cold: {cold}")
    print(f"  -> output/leads.json")
    print(f"  -> output/leads.csv")
    print(f"\n  Open dashboard.html in your browser to view")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    run()