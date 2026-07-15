import logging
import time
import argparse
from typing import Optional
from playwright.sync_api import sync_playwright, Page
from dataclasses import dataclass, asdict
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
    opening_status: str = ""
    hours_today: str = ""
    full_hours: str = ""
    price_range: str = ""
    plus_code: str = ""
    store_shopping: str = "No"
    in_store_pickup: str = "No"
    delivery: str = "No"
    dine_in: str = "No"
    introduction: str = ""
    latitude: str = ""
    longitude: str = ""
    url: str = ""

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

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
            time.sleep(5)

            # Handle GDPR/consent popup
            if 'consent.google.com' in page.url:
                try:
                    page.locator('form button').first.click()
                    time.sleep(3)
                except:
                    pass

            # Wait for business name to load
            try:
                page.wait_for_selector('.DUwDvf', timeout=15000)
            except:
                pass

            time.sleep(3)

            # ===== BUSINESS NAME =====
            try:
                name_loc = page.locator('.DUwDvf')
                if name_loc.count() > 0:
                    business.name = name_loc.first.inner_text().strip()
            except:
                pass

            # ===== CATEGORY / PLACE TYPE =====
            try:
                cat_loc = page.locator('button.DkEaL')
                if cat_loc.count() > 0:
                    business.place_type = cat_loc.first.inner_text().strip()
            except:
                pass

            # ===== RATING =====
            try:
                rating_loc = page.locator('.F7nice span[aria-hidden="true"]')
                if rating_loc.count() > 0:
                    text = rating_loc.first.inner_text().strip()
                    business.rating = float(text.replace(',', '.'))
            except:
                pass

            # ===== REVIEWS COUNT =====
            try:
                reviews_loc = page.locator('.F7nice span[aria-label]')
                if reviews_loc.count() > 0:
                    text = reviews_loc.first.get_attribute('aria-label')
                    if text:
                        num = text.replace(',', '').replace('.', '')
                        import re
                        match = re.search(r'(\d+)', num)
                        if match:
                            business.reviews_count = int(match.group(1))
            except:
                pass

            # ===== ALL INFO ITEMS (address, phone, website, hours, plus code) =====
            # These are in the info section with data-item-id attributes
            try:
                # Address
                addr_loc = page.locator('button[data-item-id="address"]')
                if addr_loc.count() > 0:
                    business.address = addr_loc.first.get_attribute('aria-label') or ""
                    business.address = business.address.replace("Address: ", "").strip()
            except:
                pass

            try:
                # Phone
                phone_loc = page.locator('button[data-item-id*="phone:tel:"]')
                if phone_loc.count() > 0:
                    business.phone_number = phone_loc.first.get_attribute('aria-label') or ""
                    business.phone_number = business.phone_number.replace("Phone: ", "").strip()
            except:
                pass

            try:
                # Website
                web_loc = page.locator('a[data-item-id="authority"]')
                if web_loc.count() > 0:
                    business.website = web_loc.first.get_attribute('aria-label') or ""
                    business.website = business.website.replace("Website: ", "").strip()
                    if not business.website:
                        business.website = web_loc.first.get_attribute('href') or ""
                business.has_website = "Yes" if business.website else "No"
            except:
                pass

            try:
                # Plus Code
                plus_loc = page.locator('button[data-item-id="oloc"]')
                if plus_loc.count() > 0:
                    business.plus_code = plus_loc.first.get_attribute('aria-label') or ""
                    business.plus_code = business.plus_code.replace("Plus code: ", "").strip()
            except:
                pass

            # ===== OPENING HOURS =====
            try:
                hours_loc = page.locator('button[data-item-id*="oh"]')
                if hours_loc.count() > 0:
                    hours_label = hours_loc.first.get_attribute('aria-label') or ""
                    business.full_hours = hours_label.replace("Hours", "").strip()

                    # Get the visible text for status
                    hours_text_loc = hours_loc.first.locator('.fontBodyMedium')
                    if hours_text_loc.count() > 0:
                        visible_text = hours_text_loc.first.inner_text().strip()
                        parts = visible_text.split('⋅')
                        if len(parts) >= 2:
                            business.opening_status = parts[0].strip()
                            business.hours_today = parts[1].strip().replace("\u202f", "")
                        else:
                            business.opening_status = visible_text.replace("\u202f", "")
            except:
                pass

            # ===== PRICE RANGE =====
            try:
                price_loc = page.locator('span[aria-label*="Price"]')
                if price_loc.count() > 0:
                    business.price_range = price_loc.first.get_attribute('aria-label') or ""
            except:
                pass

            # ===== SERVICE OPTIONS =====
            try:
                services = page.locator('.LTs0Rc')
                for i in range(services.count()):
                    text = services.nth(i).inner_text().lower()
                    if 'dine' in text or 'dine-in' in text:
                        business.dine_in = "Yes"
                    if 'delivery' in text:
                        business.delivery = "Yes"
                    if 'pickup' in text or 'pick-up' in text:
                        business.in_store_pickup = "Yes"
                    if 'shop' in text or 'in-store' in text:
                        business.store_shopping = "Yes"
            except:
                pass

            # ===== INTRODUCTION / ABOUT =====
            try:
                intro_loc = page.locator('.WeS02d.fontBodyMedium .PYvSYb')
                if intro_loc.count() > 0:
                    business.introduction = intro_loc.first.inner_text().strip()
            except:
                pass

            # ===== LATITUDE & LONGITUDE (from URL) =====
            try:
                current_url = page.url
                import re
                coords = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
                if coords:
                    business.latitude = coords.group(1)
                    business.longitude = coords.group(2)
            except:
                pass

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
            time.sleep(2)
        except Exception as e:
            logging.warning(f"Failed to scrape {url}: {e}")

    save_to_csv(businesses, output_path, append)
    return businesses


def save_to_csv(businesses, output_path: str = "businesses.csv", append: bool = False):
    if not businesses:
        logging.warning("No data to save.")
        return

    df = pd.DataFrame([asdict(b) for b in businesses])

    if not df.empty:
        import os
        file_exists = os.path.isfile(output_path)
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
        print(f"="*60)

        # Print all details for each business
        for _, row in df.iterrows():
            print(f"\n  {'='*56}")
            print(f"  {row['name']}")
            print(f"  {'='*56}")
            print(f"  Category:     {row['place_type']}")
            print(f"  Address:      {row['address']}")
            print(f"  Phone:        {row['phone_number']}")
            print(f"  Website:      {row['website'] if row['website'] else 'NONE - POTENTIAL LEAD!'}")
            print(f"  Rating:       {row['rating']}/5 ({row['reviews_count']} reviews)")
            print(f"  Status:       {row['opening_status']}")
            print(f"  Hours Today:  {row['hours_today']}")
            print(f"  Full Hours:   {row['full_hours']}")
            print(f"  Plus Code:    {row['plus_code']}")
            print(f"  Dine-in:      {row['dine_in']}")
            print(f"  Delivery:     {row['delivery']}")
            print(f"  Pickup:       {row['in_store_pickup']}")
            print(f"  Shopping:     {row['store_shopping']}")
            print(f"  About:        {row['introduction']}")
            print(f"  Coordinates:  {row['latitude']}, {row['longitude']}")
            print(f"  URL:          {row['url']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Google Maps Business Scraper - Get FULL details from URL(s)")
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
        print(f"  URL: {args.url[:55]}...")
        print(f"  Output: {args.output}")
        print(f"="*60 + "\n")

        business = scrape_business_from_url(args.url)
        save_to_csv([business], args.output, args.append)

        if args.json:
            print("\nJSON Output:")
            print(json.dumps(asdict(business), indent=2, ensure_ascii=False))

    elif args.file:
        with open(args.file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
        print(f"  URLs file: {args.file}")
        print(f"  Total URLs: {len(urls)}")
        print(f"  Output: {args.output}")
        print(f"="*60 + "\n")

        scrape_multiple_urls(urls, args.output, args.append)


if __name__ == "__main__":
    main()
