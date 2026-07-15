import { chromium, type Page } from "playwright";

export interface ScrapedLead {
  business_name: string;
  address: string;
  phone: string;
  category: string;
  rating: number | null;
  review_count: number | null;
  website: string;
  has_website: number;
}

function randomDelay(min: number, max: number): Promise<void> {
  const ms = Math.floor(Math.random() * (max - min + 1)) + min;
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function trySelector(
  page: Page,
  selectors: string[]
): Promise<string | null> {
  for (const selector of selectors) {
    try {
      const element = await page.$(selector);
      if (element) {
        const text = await element.textContent();
        if (text && text.trim()) {
          return text.trim();
        }
      }
    } catch {
      // Selector not found, try next
    }
  }
  return null;
}

async function tryGetAttribute(
  page: Page,
  selectors: string[],
  attribute: string
): Promise<string | null> {
  for (const selector of selectors) {
    try {
      const element = await page.$(selector);
      if (element) {
        const value = await element.getAttribute(attribute);
        if (value && value.trim()) {
          return value.trim();
        }
      }
    } catch {
      // Selector not found, try next
    }
  }
  return null;
}

export async function scrapeGoogleMaps(
  query: string
): Promise<ScrapedLead[]> {
  const results: ScrapedLead[] = [];

  const browser = await chromium.launch({
    headless: true,
    args: [
      "--disable-blink-features=AutomationControlled",
      "--disable-features=IsolateOrigins,site-per-process",
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
    ],
  });

  try {
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      userAgent:
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    });

    const page = await context.newPage();

    // Navigate to Google Maps with the search query
    const url = `https://www.google.com/maps/search/${encodeURIComponent(query)}`;
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
    // Wait a bit for dynamic content to load
    await randomDelay(3000, 5000);

    // Handle cookie consent popup (non-fatal)
    try {
      const consentSelectors = [
        '[aria-label="Accept all"]',
        'button:has-text("Accept all")',
        'form[action*="consent"] button',
        ".VfPpkd-LgbsSe",
      ];
      for (const selector of consentSelectors) {
        try {
          const button = await page.$(selector);
          if (button) {
            await button.click();
            await randomDelay(1000, 2000);
            break;
          }
        } catch {
          // Try next selector
        }
      }
    } catch {
      // Consent popup not found or already dismissed
    }

    // Wait for results to load
    try {
      await page.waitForSelector('[role="feed"], .Nv2PK, .m6QErb', {
        timeout: 15000,
      });
    } catch {
      // Results may have loaded with a different structure
    }

    // Scroll the results panel to load more results
    const feedSelector = '[role="feed"]';
    for (let i = 0; i < 4; i++) {
      try {
        await page.evaluate((selector) => {
          const feed = document.querySelector(selector);
          if (feed) {
            feed.scrollTop = feed.scrollHeight;
          }
        }, feedSelector);
      } catch {
        // Scroll failed, continue
      }
      await randomDelay(1000, 3000);
    }

    // Collect all result items
    const resultSelectors = [
      '[role="feed"] > div > div > a',
      ".Nv2PK a",
      ".hfpxzc",
    ];

    const resultElements: string[] = [];
    for (const selector of resultSelectors) {
      try {
        const elements = await page.$$(selector);
        if (elements.length > 0) {
          // Store aria-labels or hrefs to re-find them after clicking
          for (const el of elements) {
            const label = await el.getAttribute("aria-label");
            if (label) {
              resultElements.push(label);
            }
          }
          break;
        }
      } catch {
        // Try next selector
      }
    }

    // Limit to 20 results
    const maxResults = Math.min(resultElements.length, 20);

    for (let i = 0; i < maxResults; i++) {
      try {
        // Re-find the element by aria-label using Playwright's getByRole
        // which safely handles special characters (], \, quotes, etc.)
        const ariaLabel = resultElements[i];
        const element = page.getByRole("link", { name: ariaLabel, exact: true }).first();

        if ((await element.count()) === 0) continue;

        // Click the result to open its detail panel
        await element.click();
        await randomDelay(500, 2000);

        // Extract business details from the detail panel
        const businessName = await trySelector(page, [
          ".DUwDvf",
          "h1.DUwDvf",
          '[data-attrid="title"]',
          "h1",
        ]);

        const address = await trySelector(page, [
          ".rogA2c .Io6YTe",
          'button[data-item-id="address"]',
          '[data-item-id="address"]',
        ]);

        // Phone - try selectors and look for phone pattern
        let phone = await trySelector(page, [
          'button[data-item-id^="phone"]',
          '[data-item-id^="phone"]',
        ]);
        if (!phone) {
          // Try to find phone in generic info elements
          const infoElements = await page.$$(".rogA2c .Io6YTe");
          for (const el of infoElements) {
            const text = await el.textContent();
            if (text && /[\d\s\-\(\)\+]{7,}/.test(text)) {
              phone = text.trim();
              break;
            }
          }
        }

        const category = await trySelector(page, [
          "button.DkEaL",
          ".DkEaL",
          '[jsaction*="category"]',
        ]);

        // Rating
        const ratingText = await trySelector(page, [
          '.F7nice span[aria-hidden="true"]',
          ".MW4etd",
        ]);
        const rating = ratingText ? parseFloat(ratingText) || null : null;

        // Review count
        let reviewCount: number | null = null;
        const reviewText = await trySelector(page, [
          '.F7nice span[aria-label*="review"]',
          ".UY7F9",
        ]);
        if (reviewText) {
          const match = reviewText.match(/[\d,]+/);
          if (match) {
            reviewCount = parseInt(match[0].replace(/,/g, ""), 10) || null;
          }
        }

        // Website
        let website =
          (await tryGetAttribute(
            page,
            [
              'a[data-item-id="authority"]',
              'a[aria-label*="website"]',
            ],
            "href"
          )) || "";

        // Fallback: find a link that is not a Google link
        if (!website) {
          try {
            const links = await page.$$('a[href^="http"]:not([href*="google"])');
            for (const link of links) {
              const href = await link.getAttribute("href");
              if (
                href &&
                !href.includes("google.com") &&
                !href.includes("googleapis.com")
              ) {
                website = href;
                break;
              }
            }
          } catch {
            // No website found
          }
        }

        const hasWebsite = website ? 1 : 0;

        results.push({
          business_name: businessName || "",
          address: address || "",
          phone: phone || "",
          category: category || "",
          rating,
          review_count: reviewCount,
          website: website || "",
          has_website: hasWebsite,
        });

        // Random delay before next business
        await randomDelay(500, 1500);
      } catch {
        // Skip this result and continue with next
        continue;
      }
    }
  } finally {
    await browser.close();
  }

  return results;
}
