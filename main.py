import logging
from typing import List, Optional
from playwright.sync_api import sync_playwright, Page
from dataclasses import dataclass, asdict
import pandas as pd
import argparse
import platform
import time
import os

@dataclass
class Place:
    name: str = ""
    address: str = ""
    website: str = ""
    has_website: str = "Yes"
    phone_number: str = ""
    reviews_count: Optional[int] = None
    reviews_average: Optional[float] = None
    store_shopping: str = "No"
    in_store_pickup: str = "No"
    store_delivery: str = "No"
    place_type: str = ""
    opens_at: str = ""
    introduction: str = ""

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

def extract_text(page: Page, xpath: str) -> str:
    try:
        if page.locator(xpath).count() > 0:
            return page.locator(xpath).inner_text()
    except Exception as e:
        logging.warning(f"Failed to extract text for xpath {xpath}: {e}")
    return ""

def extract_place(page: Page) -> Place:
    # XPaths
    name_xpath = '//div[@class="TIHn2 "]//h1[@class="DUwDvf lfPIob"]'
    address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
    website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
    phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
    reviews_count_xpath = '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span//span//span[@aria-label]'
    reviews_average_xpath = '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span[@aria-hidden]'
    info1 = '//div[@class="LTs0Rc"][1]'
    info2 = '//div[@class="LTs0Rc"][2]'
    info3 = '//div[@class="LTs0Rc"][3]'
    opens_at_xpath = '//button[contains(@data-item-id, "oh")]//div[contains(@class, "fontBodyMedium")]'
    opens_at_xpath2 = '//div[@class="MkV9"]//span[@class="ZDu9vd"]//span[2]'
    place_type_xpath = '//div[@class="LBgpqf"]//button[@class="DkEaL "]'
    intro_xpath = '//div[@class="WeS02d fontBodyMedium"]//div[@class="PYvSYb "]'

    place = Place()
    place.name = extract_text(page, name_xpath)
    place.address = extract_text(page, address_xpath)
    place.website = extract_text(page, website_xpath)
    place.has_website = "Yes" if place.website else "No"
    place.phone_number = extract_text(page, phone_number_xpath)
    place.place_type = extract_text(page, place_type_xpath)
    place.introduction = extract_text(page, intro_xpath) or "None Found"

    # Reviews Count
    reviews_count_raw = extract_text(page, reviews_count_xpath)
    if reviews_count_raw:
        try:
            temp = reviews_count_raw.replace('\xa0', '').replace('(','').replace(')','').replace(',','')
            place.reviews_count = int(temp)
        except Exception as e:
            logging.warning(f"Failed to parse reviews count: {e}")
    # Reviews Average
    reviews_avg_raw = extract_text(page, reviews_average_xpath)
    if reviews_avg_raw:
        try:
            temp = reviews_avg_raw.replace(' ','').replace(',','.')
            place.reviews_average = float(temp)
        except Exception as e:
            logging.warning(f"Failed to parse reviews average: {e}")
    # Store Info
    for idx, info_xpath in enumerate([info1, info2, info3]):
        info_raw = extract_text(page, info_xpath)
        if info_raw:
            temp = info_raw.split('·')
            if len(temp) > 1:
                check = temp[1].replace("\n", "").lower()
                if 'shop' in check:
                    place.store_shopping = "Yes"
                if 'pickup' in check:
                    place.in_store_pickup = "Yes"
                if 'delivery' in check:
                    place.store_delivery = "Yes"
    # Opens At
    opens_at_raw = extract_text(page, opens_at_xpath)
    if opens_at_raw:
        opens = opens_at_raw.split('⋅')
        if len(opens) > 1:
            place.opens_at = opens[1].replace("\u202f","")
        else:
            place.opens_at = opens_at_raw.replace("\u202f","")
    else:
        opens_at2_raw = extract_text(page, opens_at_xpath2)
        if opens_at2_raw:
            opens = opens_at2_raw.split('⋅')
            if len(opens) > 1:
                place.opens_at = opens[1].replace("\u202f","")
            else:
                place.opens_at = opens_at2_raw.replace("\u202f","")
    return place

def scrape_places(search_for: str, total: int) -> List[Place]:
    setup_logging()
    places: List[Place] = []
    with sync_playwright() as p:
        if platform.system() == "Windows":
            browser_path = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            browser = p.chromium.launch(executable_path=browser_path, headless=False)
        else:
            browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto("https://www.google.com/maps/@32.9817464,70.1930781,3.67z?", timeout=60000)
            page.wait_for_timeout(1000)
            page.locator("//form[contains(@jsaction,'searchboxFormSubmit')]//input[@name='q']").fill(search_for)
            page.keyboard.press("Enter")
            page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]')
            page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')
            previously_counted = 0
            while True:
                page.mouse.wheel(0, 10000)
                page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]')
                found = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
                logging.info(f"Currently Found: {found}")
                if found >= total:
                    break
                if found == previously_counted:
                    logging.info("Arrived at all available")
                    break
                previously_counted = found
            listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:total]
            listings = [listing.locator("xpath=..") for listing in listings]
            logging.info(f"Total Found: {len(listings)}")
            for idx, listing in enumerate(listings):
                try:
                    listing.click()
                    page.wait_for_selector('//div[@class="TIHn2 "]//h1[@class="DUwDvf lfPIob"]', timeout=10000)
                    time.sleep(1.5)  # Give time for details to load
                    place = extract_place(page)
                    if place.name:
                        places.append(place)
                        status = "NO WEBSITE" if place.has_website == "No" else "has website"
                        logging.info(f"[{idx+1}/{len(listings)}] {place.name} - {status}")
                    else:
                        logging.warning(f"No name found for listing {idx+1}, skipping.")
                except Exception as e:
                    logging.warning(f"Failed to extract listing {idx+1}: {e}")
        finally:
            browser.close()
    return places

def save_places_to_csv(places: List[Place], output_path: str = "result.csv", append: bool = False, no_website_only: bool = False):
    df = pd.DataFrame([asdict(place) for place in places])
    if not df.empty:
        # Filter to only businesses without websites if requested
        if no_website_only:
            df = df[df['has_website'] == 'No']
            logging.info(f"Filtered to {len(df)} businesses WITHOUT a website")

        if df.empty:
            logging.warning("No businesses found matching your filter criteria.")
            return

        # Remove columns where all values are the same (useless data)
        for column in df.columns:
            if df[column].nunique() == 1 and column not in ['has_website']:
                df.drop(column, axis=1, inplace=True)

        file_exists = os.path.isfile(output_path)
        mode = "a" if append else "w"
        header = not (append and file_exists)
        df.to_csv(output_path, index=False, mode=mode, header=header)
        logging.info(f"Saved {len(df)} places to {output_path} (append={append})")

        # Print summary
        total_places = len(places)
        no_website_count = sum(1 for p in places if p.has_website == "No")
        has_website_count = total_places - no_website_count
        print("\n" + "="*60)
        print(f"  SCRAPING COMPLETE")
        print(f"="*60)
        print(f"  Total businesses scraped: {total_places}")
        print(f"  With website:             {has_website_count}")
        print(f"  WITHOUT website (LEADS):  {no_website_count}")
        print(f"  Output file:              {output_path}")
        print(f"="*60 + "\n")
    else:
        logging.warning("No data to save. DataFrame is empty.")

def main():
    parser = argparse.ArgumentParser(description="Google Maps Scraper - Find businesses without websites")
    parser.add_argument("-s", "--search", type=str, help="Search query for Google Maps (e.g. 'plumbers in Austin TX')")
    parser.add_argument("-t", "--total", type=int, help="Total number of results to scrape (default: 20)")
    parser.add_argument("-o", "--output", type=str, default="result.csv", help="Output CSV file path (default: result.csv)")
    parser.add_argument("--append", action="store_true", help="Append results to the output file instead of overwriting")
    parser.add_argument("--no-website", action="store_true", help="Only save businesses that do NOT have a website")
    parser.add_argument("--leads-only", action="store_true", help="Same as --no-website (only save leads without websites)")
    args = parser.parse_args()

    search_for = args.search or "turkish stores in toronto Canada"
    total = args.total or 20
    output_path = args.output
    append = args.append
    no_website_only = args.no_website or args.leads_only

    print("\n" + "="*60)
    print(f"  GOOGLE MAPS LEAD SCRAPER")
    print(f"="*60)
    print(f"  Search: {search_for}")
    print(f"  Target results: {total}")
    print(f"  Output: {output_path}")
    print(f"  Filter: {'Only businesses WITHOUT websites' if no_website_only else 'All businesses'}")
    print(f"="*60 + "\n")

    places = scrape_places(search_for, total)
    save_places_to_csv(places, output_path, append=append, no_website_only=no_website_only)

if __name__ == "__main__":
    main()
