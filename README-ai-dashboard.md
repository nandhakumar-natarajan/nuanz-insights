AI Dashboard — deployment notes

What changed

- Replaced the rotating cube multi-screen widget with a sequential "lettercard" carousel containing two cards:
  1) "Hello John" — shows portfolio sentiment
  2) "AI says" — shows the most important news item for the portfolio
- Removed the "Market Movers" widget and the "AI Insights Feed" section from the page markup
- Added lightweight JS that auto-rotates the two cards and attempts to fetch data from API endpoints if available:
  - /api/portfolio/sentiment -> { summary, score }
  - /api/portfolio/top-news -> { headline, link? }
  - /api/portfolio/snapshot -> { overallScore, suggestion }

Files to deploy

- ai-dashboard.html  (this file)

Preview locally

Open `ai-dashboard.html` directly in a browser, or run a local static server from the Insights folder:

```powershell
# from C:\Users\USER\Insights
python -m http.server 8000
# then open http://localhost:8000/ai-dashboard.html in your browser
```

Deployment checklist (recommended)

1) Backup the current remote file on the server.
   - Example (Linux server with SSH):
     ssh user@host "cp /var/www/html/ai-dashboard.html /var/www/html/ai-dashboard.html.bak.$(date +%Y%m%d%H%M%S)"

2) Upload the new `ai-dashboard.html`.
   - Using scp from PowerShell (OpenSSH client required):
     scp -P 22 .\ai-dashboard.html user@host:/var/www/html/ai-dashboard.html

3) Verify using curl or a browser:
   curl -sS https://your-site/ai-dashboard.html | head -n 40

4) If the site is served behind a CDN, purge the CDN cache for this file.

5) If the page requires the API endpoints, ensure your backend routes are available and returning the expected JSON shape.

Notes about wiring to backend

- The frontend attempts to fetch these endpoints with fetch() and will silently keep placeholders if they are unreachable. To populate the cards, implement these endpoints (example contract below):

GET /api/portfolio/sentiment
Response: 200
{
  "summary": "Mostly Positive",
  "score": "+12%"
}

GET /api/portfolio/top-news
Response: 200
{
  "headline": "HDFC Bank Q3 results beat estimates, stock rallies",
  "link": "https://news.site/article"
}

GET /api/portfolio/snapshot
Response: 200
{
  "overallScore": "78%",
  "suggestion": "Consider rebalancing toward defensive sectors"
}

If you want, I can add small mock endpoints to your FastAPI app so the page shows live values immediately after deployment.

Rollback plan

- If something goes wrong, restore the backup created in step (1):
  ssh user@host "mv /var/www/html/ai-dashboard.html.bak.<timestamp> /var/www/html/ai-dashboard.html"

Questions / next actions

- Do you want me to add mock FastAPI endpoints to the `app/` package so the page has live data immediately? (I can implement quick mocks under `/api/portfolio/*`.)
- Do you want me to produce a minified version of the HTML and a ZIP package for easy upload?
- If you want, provide server access details (or run the provided `deploy_ai_dashboard.ps1` locally) and I can perform the upload for you.
