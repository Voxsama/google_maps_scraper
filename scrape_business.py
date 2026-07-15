import logging
import time
import argparse
from typing import Optional
from playwright.sync_api import sync_playwright, Page
from dataclasses import dataclass, asdict, fields
import pandas as pd
import platform
import json

@dataclass
class BusinessDetails:
    name: str = ""
    address: str = ""
    phone_number: str = ""
    website: str = ""
    has_website: str = "No"
    place_type: str = ""
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    opens_at: str = ""
    hours: str = ""
    price_range: str = ""
    plus_code: str = ""
    store_shopping: str = "No"
    in_store_pickup: str = "No"
    delivery: str = "No"
    dine_in: str = "No"
    introduction: str = ""
    url: str = ""

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

def extract_text(page: Page, xpath: str) -> str:
    try:
        loc = page.locator(xpath)
        if loc.count() > 0:
            return loc.first.inner_text().strip()
    except:
        pass
    return ""

def extract_attribute(page: Page, xpath: str, attr: str) -> str:
    try:
        loc = page.locator(xpath)
        if loc.count() > 0:
            val = loc.first.get_attribute(attr)
            return val.strip() if val else ""
    except:
        pass
    return ""

def scrape_business_from_url(url: str) -> BusinessDetails:
    """Scrape all details from a single Google Maps business URL"""
    setup_logging()
    business = BusinessDetails()
    business.url = url

    with sync_playwright() as p:
        if platform.system() == "Windows":
            browser_path = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            browser = p.chromium.launch(executable_path=browser_path, headless=False)
        else:
            browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        try:
            logging.info(f"Opening: {url}")
            page.goto(url, timeout=60000)
            time.sleep(4)

            # Handle GDPR/consent popup
            if 'consent.google.com' in page.url:
                try:
                    page.locator('form button').first.click()
                    time.sleep(2)
                except:
                    pass

            # Wait for business name to load
            try:
                page.wait_for_selector('//h1[@class="DUwDvf lfPIob"]', timeout=15000)
            except:
                try:
                    page.wait_for_selector('.DUwDvf', timeout=10000)
                except:
                    pass

            time.sleep(2)

            # Business Name
            business.name = extract_text(page, '//h1[@class="DUwDvf lfPIob"]')
            if not business.name:
                business.name = extract_text(page, '.DUwDvf')

            # Address
            business.address = extract_text(page, '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]')

            # Phone
            business.phone_number = extract_text(page, '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]')

            # Website
            business.website = extract_text(page, '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]')
            if not business.website:
                # Try getting href
                href = extract_attribute(page, '//a[@data-item-id="authority"]', 'href')
                if href:
                    business.website = href
            business.has_website = "Yes" if business.website else "No"

            # Category/Place Type
            business.place_type = extract_text(page, '//div[@class="LBgpqf"]//button[@class="DkEaL "]')

            # Rating
            rating_text = extract_text(page, '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span[@aria-hidden]')
            if rating_text:
                try:
                    business.rating = float(rating_text.replace(',', '.').strip())
                except:
                    pass

            # Reviews Count
            reviews_text = extract_text(page, '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span//span//span[@aria-label]')
            if reviews_text:
                try:
                    temp = reviews_text.replace('\xa0', '').replace('(', '').replace(')', '').replace(',', '')
                    business.reviews_count = int(temp)
                except:
                    pass

            # Opening Hours
            opens_at_text = extract_text(page, '//button[contains(@data-item-id, "oh")]//div[contains(@class, "fontBodyMedium")]')
            if opens_at_text:
                parts = opens_at_text.split('⋅')
                if len(parts) > 1:
                    business.opens_at = parts[0].strip()
                    business.hours = parts[1].strip().replace("\u202f", "")
                else:
                    business.opens_at = opens_at_text.replace("\u202f", "")

            # Price Range
            business.price_range = extract_text(page, '//span[contains(@aria-label, "Price")]')

            # Plus Code
            business.plus_code = extract_text(page, '//button[@data-item-id="oloc"]//div[contains(@class, "fontBodyMedium")]')

            # Service options (dine-in, delivery, pickup, etc.)
            try:
                service_options = page.locator('//div[@class="LTs0Rc"]')
                count = service_options.count()
                for i in range(count):
                    text = service_options.nth(i).inner_text().lower()
                    if 'dine' in text:
                        business.dine_in = "Yes"
                    if 'delivery' in text:
                        business.delivery = "Yes"
                    if 'pickup' in text:
                        business.in_store_pickup = "Yes"
                    if 'shop' in text:
                        business.store_shopping = "Yes"
            except:
                pass

            # Introduction/About
            business.introduction = extract_text(page, '//div[@class="WeS02d fontBodyMedium"]//div[@class="PYvSYb "]')

            logging.info(f"Successfully scraped: {business.name}")

        finally:
            browser.close()

    return business


def scrape_multiple_urls(urls: list, output_path: str = "businesses.csv", append: bool = False):
    """Scrape details from multiple Google Maps URLs"""
    businesses = []
    for i, url in enumerate(urls):
        print(f"\n[{i+1}/{len(urls)}] Scraping: {url[:60]}...")
        try:
            biz = scrape_business_from_url(url)
            businesses.append(biz)
            time.sleep(2)  # Delay between scrapes
        except Exception as e:
            logging.warning(f"Failed to scrape {url}: {e}")

    save_to_csv(businesses, output_path, append)
    return businesses


def save_to_csv(businesses, output_path: str = "businesses.csv", append: bool = False):
    if not businesses:
        logging.warning("No data to save.")
        return

    if isinstance(businesses[0], BusinessDetails):
        df = pd.DataFrame([asdict(b) for b in businesses])
    else:
        df = pd.DataFrame(businesses)

    if not df.empty:
        file_exists = pd.io.common.file_exists(output_path)
        mode = "a" if append else "w"
        header = not (append and file_exists)
        df.to_csv(output_path, index=False, mode=mode, header=header)

        no_website = len(df[df['has_website'] == 'No'])
        has_website = len(df[df['has_website'] == 'Yes'])

        print("\n" + "="*60)
        print(f"  SCRAPING COMPLETE")
        print(f"="*60)
        print(f"  Total businesses scraped: {len(df)}")
        print(f"  With website:             {has_website}")
        print(f"  WITHOUT website (LEADS):  {no_website}")
        print(f"  Output file:              {output_path}")
        print(f"="*60 + "\n")

        # Print details
        for _, row in df.iterrows():
            status = "NO WEBSITE" if row['has_website'] == 'No' else "has website"
            print(f"  {row['name']} | {row['phone_number']} | {status}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Google Maps Business Scraper - Get full details from URL(s)")
    parser.add_argument("-u", "--url", type=str, help="Single Google Maps business URL")
    parser.add_argument("-f", "--file", type=str, help="Text file with Google Maps URLs (one per line)")
    parser.add_argument("-o", "--output", type=str, default="businesses.csv", help="Output CSV file (default: businesses.csv)")
    parser.add_argument("--append", action="store_true", help="Append to existing file")
    parser.add_argument("--json", action="store_true", help="Also print output as JSON")
    args = parser.parse_args()

    if not args.url and not args.file:
        parser.error("You must provide either -u (single URL) or -f (file with URLs)")

    print("\n" + "="*60)
    print(f"  GOOGLE MAPS BUSINESS DETAIL SCRAPER")
    print(f"="*60)

    if args.url:
        # Single URL
        print(f"  URL: {args.url[:55]}...")
        print(f"  Output: {args.output}")
        print(f"="*60 + "\n")

        business = scrape_business_from_url(args.url)
        save_to_csv([business], args.output, args.append)

        if args.json:
            print("\nJSON Output:")
            print(json.dumps(asdict(business), indent=2))

    elif args.file:
        # Multiple URLs from file
        with open(args.file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
        print(f"  URLs file: {args.file}")
        print(f"  Total URLs: {len(urls)}")
        print(f"  Output: {args.output}")
        print(f"="*60 + "\n")

        scrape_multiple_urls(urls, args.output, args.append)


if __name__ == "__main__":
    main()
