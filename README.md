# LeadScraper - Google Maps Business Scraper

Find local businesses on Google Maps that **don't have a website** — perfect for offering your web development services.

## Features

- Search Google Maps with any query (e.g. "plumbers in Austin TX")
- Headless browser scraping with anti-detection measures
- Automatically identifies businesses without websites
- SQLite database for storing leads locally
- Export leads to CSV
- Dashboard with stats overview
- Dark theme professional UI
- Table and card view modes

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Install Playwright browsers (IMPORTANT!)

```bash
npx playwright install chromium
```

> If you get permission errors on Linux, run:
> ```bash
> npx playwright install --with-deps chromium
> ```

### 3. Run the app

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## How to Use

1. Go to the **Search** page
2. Enter a query like "restaurants in Dallas TX" or "dentists in Miami FL"
3. Click **Search** — the scraper will open Google Maps in a headless browser and extract business details
4. View results on the **Results** page — businesses without websites are highlighted
5. Toggle the **"No Website Only"** filter to see just your opportunities
6. Click **Export CSV** to download your leads

## Pages

| Page | URL | Description |
|------|-----|-------------|
| Search | `/search` | Enter queries to scrape Google Maps |
| Results | `/results` | View all scraped leads (table/card view, filters, CSV export) |
| Dashboard | `/dashboard` | Stats overview and recent searches |

## Tech Stack

- **Next.js 14** (App Router) with TypeScript
- **Tailwind CSS** for styling (dark theme)
- **Playwright** for headless browser scraping
- **better-sqlite3** for local database storage

## Troubleshooting

### "Executable doesn't exist" error
Run `npx playwright install chromium` to download the browser.

### "No results found"
- Google may be blocking the request. Wait a few minutes and try again.
- Use specific queries with location (e.g. "plumbers in Austin TX" not just "plumbers")
- Google Maps HTML changes frequently — selectors may need updating.

### Scraping is slow
This is normal. The scraper adds random delays between actions to avoid detection. Each search takes 30-90 seconds depending on how many results are found.

## License

MIT
