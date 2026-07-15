import logging
import time
import argparse
import os
import re
import requests
from typing import Optional, List
from playwright.sync_api import sync_playwright, Page
from dataclasses import dataclass, asdict, field
import pandas as pd
import platform
import json

@dataclass
class Review:
    reviewer_name: str = ""
    rating: int = 0
    review_text: str = ""
    time_posted: str = ""
    reviewer_photo: str = ""

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
    monday: str = ""
    tuesday: str = ""
    wednesday: str = ""
    thursday: str = ""
    friday: str = ""
    saturday: str = ""
    sunday: str = ""
    price_range: str = ""
    plus_code: str = ""
    store_shopping: str = "No"
    in_store_pickup: str = "No"
    delivery: str = "No"
    dine_in: str = "No"
    introduction: str = ""
    latitude: str = ""
    longitude: str = ""
    owner_name: str = ""
    photo_urls: List[str] = field(default_factory=list)
    photo_count: int = 0
    reviews: List[Review] = field(default_factory=list)
    url: str = ""

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

def download_photos(photo_urls: List[str], business_name: str, output_dir: str = "photos"):
    """Download business photos to a local folder"""
    if not photo_urls:
        return

    # Clean business name for folder
    safe_name = re.sub(r'[^\w\s-]', '', business_name).strip().replace(' ', '_')[:50]
    photo_dir = os.path.join(output_dir, safe_name)
    os.makedirs(photo_dir, exist_ok=True)

    downloaded = 0
    for i, url in enumerate(photo_urls):
        try:
            # Fix URLs that start with // (missing scheme)
            if url.startswith('//'):
                url = 'https:' + url
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                ext = '.jpg'
                filepath = os.path.join(photo_dir, f"photo_{i+1}{ext}")
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                downloaded += 1
        except Exception as e:
            logging.warning(f"Failed to download photo {i+1}: {e}")

    logging.info(f"Downloaded {downloaded}/{len(photo_urls)} photos to {photo_dir}/")
    return photo_dir


def scrape_business_from_url(url: str, scrape_reviews: bool = True, max_reviews: int = 20, download_pics: bool = True, max_photos: int = 10) -> BusinessDetails:
    """Scrape ALL details from a single Google Maps business URL"""
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
                        match = re.search(r'(\d+)', num)
                        if match:
                            business.reviews_count = int(match.group(1))
            except:
                pass

            # ===== ADDRESS =====
            try:
                addr_loc = page.locator('button[data-item-id="address"]')
                if addr_loc.count() > 0:
                    label = addr_loc.first.get_attribute('aria-label') or ""
                    business.address = label.replace("Address: ", "").strip()
            except:
                pass

            # ===== PHONE =====
            try:
                phone_loc = page.locator('button[data-item-id*="phone:tel:"]')
                if phone_loc.count() > 0:
                    label = phone_loc.first.get_attribute('aria-label') or ""
                    business.phone_number = label.replace("Phone: ", "").strip()
            except:
                pass

            # ===== WEBSITE =====
            try:
                web_loc = page.locator('a[data-item-id="authority"]')
                if web_loc.count() > 0:
                    label = web_loc.first.get_attribute('aria-label') or ""
                    business.website = label.replace("Website: ", "").strip()
                    if not business.website:
                        business.website = web_loc.first.get_attribute('href') or ""
                business.has_website = "Yes" if business.website else "No"
            except:
                pass

            # ===== PLUS CODE =====
            try:
                plus_loc = page.locator('button[data-item-id="oloc"]')
                if plus_loc.count() > 0:
                    label = plus_loc.first.get_attribute('aria-label') or ""
                    business.plus_code = label.replace("Plus code: ", "").strip()
            except:
                pass

            # ===== OPENING HOURS =====
            try:
                hours_loc = page.locator('button[data-item-id*="oh"]')
                if hours_loc.count() > 0:
                    # Get the full hours from aria-label
                    hours_label = hours_loc.first.get_attribute('aria-label') or ""
                    
                    # Parse individual days from the aria-label
                    days_map = {
                        'monday': 'monday', 'tuesday': 'tuesday', 
                        'wednesday': 'wednesday', 'thursday': 'thursday',
                        'friday': 'friday', 'saturday': 'saturday', 'sunday': 'sunday'
                    }
                    hours_lower = hours_label.lower()
                    for day_key, attr_name in days_map.items():
                        pattern = rf'{day_key}[,:]?\s*([^;.]+?)(?:(?:,\s*(?:tuesday|wednesday|thursday|friday|saturday|sunday|monday))|[;.]|$)'
                        match = re.search(pattern, hours_lower)
                        if match:
                            setattr(business, attr_name, match.group(1).strip().replace('\u202f', ''))

                    # Get visible opening status
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

            # Try expanding hours table for better data
            try:
                hours_btn = page.locator('button[data-item-id*="oh"]')
                if hours_btn.count() > 0:
                    hours_btn.first.click()
                    time.sleep(1)
                    # Try to read the hours table
                    table_rows = page.locator('.y0skZc table tr, .t39EBf tr, .OqCZI tr')
                    if table_rows.count() > 0:
                        for i in range(table_rows.count()):
                            row_text = table_rows.nth(i).inner_text().strip()
                            row_lower = row_text.lower()
                            for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                                if day in row_lower:
                                    hours_val = row_text.split('\t')[-1] if '\t' in row_text else row_text.split('  ')[-1]
                                    setattr(business, day, hours_val.strip())
                    # Close the popup by pressing Escape
                    page.keyboard.press('Escape')
                    time.sleep(0.5)
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
                    if 'dine' in text:
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

            # ===== OWNER =====
            try:
                owner_loc = page.locator('.bfdHYd span')
                if owner_loc.count() > 0:
                    business.owner_name = owner_loc.first.inner_text().strip()
            except:
                pass

            # ===== COORDINATES (from URL) =====
            try:
                current_url = page.url
                coords = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
                if coords:
                    business.latitude = coords.group(1)
                    business.longitude = coords.group(2)
            except:
                pass

            # ===== PHOTOS =====
            try:
                # Click on the photos/images section
                photo_tab = page.locator('button[aria-label*="Photo"], button[aria-label*="photo"], button.aoRNLd')
                if photo_tab.count() > 0:
                    photo_tab.first.click()
                    time.sleep(3)
                else:
                    # Try clicking the main image
                    main_img = page.locator('.ZKbJif, .p-ogBf, .aoRNLd')
                    if main_img.count() > 0:
                        main_img.first.click()
                        time.sleep(3)

                # Collect photo URLs
                photo_elements = page.locator('a[data-photo-index] img, .U39Pmb img, div[style*="background-image"]')
                if photo_elements.count() > 0:
                    for i in range(min(photo_elements.count(), max_photos)):
                        try:
                            src = photo_elements.nth(i).get_attribute('src')
                            if src and 'googleusercontent' in src:
                                # Get higher res version
                                src = re.sub(r'=w\d+-h\d+', '=w800-h600', src)
                                business.photo_urls.append(src)
                        except:
                            pass

                # Also try background-image style
                if not business.photo_urls:
                    bg_elements = page.locator('[style*="background-image"]')
                    for i in range(min(bg_elements.count(), max_photos)):
                        try:
                            style = bg_elements.nth(i).get_attribute('style')
                            if style:
                                url_match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                                if url_match and 'googleusercontent' in url_match.group(1):
                                    photo_url = url_match.group(1)
                                    photo_url = re.sub(r'=w\d+-h\d+', '=w800-h600', photo_url)
                                    business.photo_urls.append(photo_url)
                        except:
                            pass

                business.photo_count = len(business.photo_urls)
                logging.info(f"Found {business.photo_count} photos")

                # Go back to main info
                page.go_back()
                time.sleep(2)
            except Exception as e:
                logging.warning(f"Photo extraction: {e}")

            # ===== REVIEWS =====
            if scrape_reviews:
                try:
                    # Click Reviews tab
                    reviews_tab = page.locator('button[role="tab"]:has-text("Reviews"), button[role="tab"]:has-text("reviews")')
                    if reviews_tab.count() > 0:
                        reviews_tab.first.click()
                        time.sleep(3)
                    else:
                        # Try clicking review count
                        rev_link = page.locator('.F7nice')
                        if rev_link.count() > 0:
                            rev_link.first.click()
                            time.sleep(3)

                    # Scroll to load reviews
                    scrolls = (max_reviews // 10) + 2
                    for _ in range(scrolls):
                        try:
                            page.evaluate("""
                                () => {
                                    const el = document.querySelector('.m6QErb.DxyBCb.kA9KIf.dS8AEf') || 
                                               document.querySelector('.m6QErb.DxyBCb');
                                    if (el) el.scrollTop = el.scrollHeight;
                                }
                            """)
                        except:
                            pass
                        time.sleep(1.5)

                    # Expand "More" buttons
                    try:
                        more_buttons = page.locator('button.w8nwRe.kyuRq')
                        for i in range(more_buttons.count()):
                            try:
                                more_buttons.nth(i).click()
                                time.sleep(0.2)
                            except:
                                pass
                    except:
                        pass

                    # Extract reviews
                    review_elements = page.locator('div.jftiEf.fontBodyMedium')
                    extract_count = min(review_elements.count(), max_reviews)
                    logging.info(f"Extracting {extract_count} reviews...")

                    for i in range(extract_count):
                        try:
                            rev_el = review_elements.nth(i)
                            review = Review()

                            # Name
                            try:
                                name_el = rev_el.locator('div.d4r55')
                                if name_el.count() > 0:
                                    review.reviewer_name = name_el.first.inner_text().strip()
                            except:
                                pass

                            # Rating
                            try:
                                stars_el = rev_el.locator('span.kvMYJc')
                                if stars_el.count() > 0:
                                    aria = stars_el.first.get_attribute('aria-label')
                                    if aria:
                                        review.rating = int(aria.split(' ')[0])
                            except:
                                pass

                            # Text
                            try:
                                text_el = rev_el.locator('span.wiI7pd')
                                if text_el.count() > 0:
                                    review.review_text = text_el.first.inner_text().strip()
                            except:
                                pass

                            # Time
                            try:
                                time_el = rev_el.locator('span.rsqaWe')
                                if time_el.count() > 0:
                                    review.time_posted = time_el.first.inner_text().strip()
                            except:
                                pass

                            # Reviewer photo
                            try:
                                img_el = rev_el.locator('img.NBa7we')
                                if img_el.count() > 0:
                                    review.reviewer_photo = img_el.first.get_attribute('src') or ""
                            except:
                                pass

                            if review.reviewer_name:
                                business.reviews.append(review)
                        except:
                            continue

                    logging.info(f"Extracted {len(business.reviews)} reviews")
                except Exception as e:
                    logging.warning(f"Review extraction: {e}")

            logging.info(f"Successfully scraped: {business.name}")

        finally:
            browser.close()

    # Download photos if requested
    if download_pics and business.photo_urls:
        download_photos(business.photo_urls, business.name)

    return business


def save_output(business: BusinessDetails, output_path: str, append: bool = False, as_json: bool = False):
    """Save business details to file"""
    # Prepare data dict (flatten reviews and photos for CSV)
    data = asdict(business)
    
    # For JSON output
    if as_json:
        json_path = output_path.replace('.csv', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved JSON to {json_path}")

    # For CSV - flatten the data (remove nested lists)
    csv_data = {}
    for k, v in data.items():
        if k == 'photo_urls':
            # Fix URLs and join
            fixed_urls = []
            for u in v:
                if u.startswith('//'):
                    u = 'https:' + u
                fixed_urls.append(u)
            csv_data['photo_urls'] = ' | '.join(fixed_urls) if fixed_urls else ""
        elif k == 'reviews':
            # Skip - reviews go to separate file
            continue
        elif isinstance(v, list):
            csv_data[k] = str(v)
        else:
            csv_data[k] = v
    
    # Add review summary
    if data['reviews']:
        csv_data['total_reviews_scraped'] = len(data['reviews'])
        # Add first few reviews as columns
        for i, rev in enumerate(data['reviews'][:5]):
            csv_data[f'review_{i+1}_name'] = rev['reviewer_name']
            csv_data[f'review_{i+1}_rating'] = rev['rating']
            csv_data[f'review_{i+1}_text'] = rev['review_text'][:200] if rev['review_text'] else ""
            csv_data[f'review_{i+1}_time'] = rev['time_posted']

    try:
        df = pd.DataFrame([csv_data])
        file_exists = os.path.isfile(output_path)
        mode = "a" if append else "w"
        header = not (append and file_exists)
        df.to_csv(output_path, index=False, mode=mode, header=header, encoding='utf-8-sig')
        logging.info(f"Saved business details to {output_path}")
    except Exception as e:
        logging.warning(f"CSV save error: {e}. Saving as JSON instead.")
        fallback_path = output_path.replace('.csv', '.json')
        with open(fallback_path, 'w', encoding='utf-8') as f:
            json.dump(csv_data, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved to {fallback_path} instead")

    # Also save all reviews to separate CSV
    if data['reviews']:
        try:
            reviews_path = output_path.replace('.csv', '_reviews.csv')
            rev_data = []
            for rev in data['reviews']:
                rev_row = {
                    'business_name': business.name,
                    'reviewer_name': rev['reviewer_name'],
                    'rating': rev['rating'],
                    'review_text': rev['review_text'],
                    'time_posted': rev['time_posted'],
                    'reviewer_photo': rev['reviewer_photo']
                }
                rev_data.append(rev_row)
            rev_df = pd.DataFrame(rev_data)
            file_exists = os.path.isfile(reviews_path)
            mode = "a" if append else "w"
            header = not (append and file_exists)
            rev_df.to_csv(reviews_path, index=False, mode=mode, header=header, encoding='utf-8-sig')
            logging.info(f"Saved {len(rev_data)} reviews to {reviews_path}")
        except Exception as e:
            logging.warning(f"Review CSV save error: {e}")


def print_details(business: BusinessDetails):
    """Print all business details in a formatted way"""
    print("\n" + "="*60)
    print(f"  {business.name}")
    print(f"="*60)
    print(f"  Category:       {business.place_type}")
    print(f"  Address:        {business.address}")
    print(f"  Phone:          {business.phone_number}")
    print(f"  Website:        {business.website if business.website else 'NONE - POTENTIAL LEAD!'}")
    print(f"  Has Website:    {business.has_website}")
    print(f"  Rating:         {business.rating}/5 ({business.reviews_count} reviews)")
    print(f"  Price Range:    {business.price_range}")
    print(f"  Status:         {business.opening_status}")
    print(f"  Hours Today:    {business.hours_today}")
    print(f"  Monday:         {business.monday}")
    print(f"  Tuesday:        {business.tuesday}")
    print(f"  Wednesday:      {business.wednesday}")
    print(f"  Thursday:       {business.thursday}")
    print(f"  Friday:         {business.friday}")
    print(f"  Saturday:       {business.saturday}")
    print(f"  Sunday:         {business.sunday}")
    print(f"  Plus Code:      {business.plus_code}")
    print(f"  Dine-in:        {business.dine_in}")
    print(f"  Delivery:       {business.delivery}")
    print(f"  Pickup:         {business.in_store_pickup}")
    print(f"  Shopping:       {business.store_shopping}")
    print(f"  About:          {business.introduction}")
    print(f"  Owner:          {business.owner_name}")
    print(f"  Coordinates:    {business.latitude}, {business.longitude}")
    print(f"  Photos:         {business.photo_count} downloaded")
    print(f"  URL:            {business.url}")
    
    if business.reviews:
        print(f"\n  --- REVIEWS ({len(business.reviews)}) ---")
        for i, rev in enumerate(business.reviews[:10]):  # Show first 10 in terminal
            stars = "★" * rev.rating + "☆" * (5 - rev.rating)
            print(f"\n  [{i+1}] {rev.reviewer_name} | {stars} | {rev.time_posted}")
            if rev.review_text:
                text = rev.review_text[:150] + "..." if len(rev.review_text) > 150 else rev.review_text
                print(f"      \"{text}\"")
        if len(business.reviews) > 10:
            print(f"\n  ... and {len(business.reviews) - 10} more reviews (saved to CSV)")

    print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Google Maps Business Scraper - Get EVERYTHING from a business URL")
    parser.add_argument("-u", "--url", type=str, help="Single Google Maps business URL")
    parser.add_argument("-f", "--file", type=str, help="Text file with Google Maps URLs (one per line)")
    parser.add_argument("-o", "--output", type=str, default="businesses.csv", help="Output CSV file (default: businesses.csv)")
    parser.add_argument("-r", "--reviews", type=int, default=20, help="Number of reviews to scrape (default: 20, 0 to skip)")
    parser.add_argument("-p", "--photos", type=int, default=10, help="Number of photos to download (default: 10, 0 to skip)")
    parser.add_argument("--no-reviews", action="store_true", help="Skip review scraping")
    parser.add_argument("--no-photos", action="store_true", help="Skip photo downloading")
    parser.add_argument("--json", action="store_true", help="Also save output as JSON (full data)")
    parser.add_argument("--append", action="store_true", help="Append to existing file")
    args = parser.parse_args()

    if not args.url and not args.file:
        parser.error("You must provide either -u (single URL) or -f (file with URLs)")

    do_reviews = not args.no_reviews and args.reviews > 0
    do_photos = not args.no_photos and args.photos > 0

    print("\n" + "="*60)
    print(f"  GOOGLE MAPS FULL BUSINESS SCRAPER")
    print(f"="*60)

    if args.url:
        print(f"  URL:      {args.url[:50]}...")
        print(f"  Reviews:  {'Yes (' + str(args.reviews) + ')' if do_reviews else 'No'}")
        print(f"  Photos:   {'Yes (' + str(args.photos) + ')' if do_photos else 'No'}")
        print(f"  Output:   {args.output}")
        print(f"="*60 + "\n")

        business = scrape_business_from_url(
            args.url,
            scrape_reviews=do_reviews,
            max_reviews=args.reviews,
            download_pics=do_photos,
            max_photos=args.photos
        )
        save_output(business, args.output, args.append, args.json)
        print_details(business)

    elif args.file:
        with open(args.file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
        
        print(f"  File:     {args.file}")
        print(f"  URLs:     {len(urls)}")
        print(f"  Reviews:  {'Yes (' + str(args.reviews) + ')' if do_reviews else 'No'}")
        print(f"  Photos:   {'Yes (' + str(args.photos) + ')' if do_photos else 'No'}")
        print(f"  Output:   {args.output}")
        print(f"="*60 + "\n")

        for i, url in enumerate(urls):
            print(f"\n[{i+1}/{len(urls)}] Scraping: {url[:60]}...")
            try:
                business = scrape_business_from_url(
                    url,
                    scrape_reviews=do_reviews,
                    max_reviews=args.reviews,
                    download_pics=do_photos,
                    max_photos=args.photos
                )
                append = args.append or (i > 0)
                save_output(business, args.output, append, args.json)
                print_details(business)
                time.sleep(2)
            except Exception as e:
                logging.warning(f"Failed: {e}")

    print("\nDone! Check your output files.")


if __name__ == "__main__":
    main()
