import logging
import time
import argparse
from typing import List, Optional
from playwright.sync_api import sync_playwright, Page
from dataclasses import dataclass, asdict
import pandas as pd
import platform

@dataclass
class Review:
    reviewer_name: str = ""
    rating: int = 0
    review_text: str = ""
    time_posted: str = ""
    business_name: str = ""

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

def scrape_reviews(url: str, total: int = 50) -> List[Review]:
    """Scrape reviews from a Google Maps business URL"""
    setup_logging()
    reviews: List[Review] = []

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
            time.sleep(3)

            # Handle GDPR/consent popup
            if 'consent.google.com' in page.url:
                try:
                    page.locator('form button').first.click()
                    time.sleep(2)
                except:
                    pass

            # Get business name
            business_name = ""
            try:
                name_el = page.locator('//h1[@class="DUwDvf lfPIob"]').first
                if name_el.count() > 0:
                    business_name = name_el.inner_text()
            except:
                pass

            # Click the Reviews tab to open all reviews
            try:
                reviews_tab = page.locator('button[role="tab"]:has-text("Reviews")')
                if reviews_tab.count() > 0:
                    reviews_tab.first.click()
                    time.sleep(2)
                    logging.info("Clicked Reviews tab")
                else:
                    # Try alternative: click review count
                    review_link = page.locator('//button[contains(@aria-label, "review")]')
                    if review_link.count() > 0:
                        review_link.first.click()
                        time.sleep(2)
                        logging.info("Clicked review link")
            except Exception as e:
                logging.warning(f"Could not click reviews tab: {e}")

            # Scroll to load more reviews
            scrolls_needed = (total // 10) + 2
            logging.info(f"Scrolling {scrolls_needed} times to load ~{total} reviews...")

            for i in range(scrolls_needed):
                try:
                    # Find the scrollable reviews container
                    page.evaluate("""
                        () => {
                            const scrollable = document.querySelector('div.m6QErb.DxyBCb.kA9KIf.dS8AEf');
                            if (scrollable) {
                                scrollable.scrollTop = scrollable.scrollHeight;
                            }
                        }
                    """)
                except:
                    try:
                        # Fallback scroll method
                        page.evaluate("""
                            () => {
                                const scrollable = document.querySelector('.m6QErb.DxyBCb');
                                if (scrollable) {
                                    scrollable.scrollTop = scrollable.scrollHeight;
                                }
                            }
                        """)
                    except:
                        pass
                time.sleep(2)

            # Expand all "More" buttons to see full review text
            try:
                more_buttons = page.locator('button.w8nwRe.kyuRq')
                count = more_buttons.count()
                logging.info(f"Found {count} 'More' buttons to expand")
                for i in range(count):
                    try:
                        more_buttons.nth(i).click()
                        time.sleep(0.3)
                    except:
                        pass
            except:
                pass

            # Extract reviews
            review_elements = page.locator('div.jftiEf.fontBodyMedium')
            found_count = review_elements.count()
            logging.info(f"Found {found_count} reviews on page")

            extract_count = min(found_count, total)
            for i in range(extract_count):
                try:
                    review_el = review_elements.nth(i)
                    review = Review()
                    review.business_name = business_name

                    # Reviewer name
                    try:
                        name_el = review_el.locator('div.d4r55').first
                        if name_el.count() > 0:
                            review.reviewer_name = name_el.inner_text()
                    except:
                        pass

                    # Rating (stars)
                    try:
                        stars_el = review_el.locator('span.kvMYJc')
                        if stars_el.count() > 0:
                            aria_label = stars_el.first.get_attribute('aria-label')
                            if aria_label:
                                # "5 stars" or "4 stars" etc
                                review.rating = int(aria_label.split(' ')[0])
                    except:
                        pass

                    # Review text
                    try:
                        text_el = review_el.locator('span.wiI7pd')
                        if text_el.count() > 0:
                            review.review_text = text_el.first.inner_text()
                    except:
                        pass

                    # Time posted
                    try:
                        time_el = review_el.locator('span.rsqaWe')
                        if time_el.count() > 0:
                            review.time_posted = time_el.first.inner_text()
                    except:
                        pass

                    if review.reviewer_name:
                        reviews.append(review)

                except Exception as e:
                    logging.warning(f"Failed to extract review {i+1}: {e}")
                    continue

        finally:
            browser.close()

    return reviews


def save_reviews_to_csv(reviews: List[Review], output_path: str = "reviews.csv", append: bool = False):
    df = pd.DataFrame([asdict(r) for r in reviews])
    if not df.empty:
        file_exists = pd.io.common.file_exists(output_path)
        mode = "a" if append else "w"
        header = not (append and file_exists)
        df.to_csv(output_path, index=False, mode=mode, header=header)

        # Summary
        avg_rating = df['rating'].mean()
        print("\n" + "="*60)
        print(f"  REVIEW SCRAPING COMPLETE")
        print(f"="*60)
        print(f"  Business: {reviews[0].business_name if reviews else 'Unknown'}")
        print(f"  Total reviews scraped: {len(df)}")
        print(f"  Average rating: {avg_rating:.1f}/5")
        print(f"  5-star: {len(df[df['rating']==5])}")
        print(f"  4-star: {len(df[df['rating']==4])}")
        print(f"  3-star: {len(df[df['rating']==3])}")
        print(f"  2-star: {len(df[df['rating']==2])}")
        print(f"  1-star: {len(df[df['rating']==1])}")
        print(f"  Output file: {output_path}")
        print(f"="*60 + "\n")
    else:
        logging.warning("No reviews found.")


def save_reviews_to_excel(reviews: List[Review], output_path: str = "reviews.xlsx"):
    df = pd.DataFrame([asdict(r) for r in reviews])
    if not df.empty:
        df.to_excel(output_path, index=False)
        logging.info(f"Saved {len(df)} reviews to {output_path}")
    else:
        logging.warning("No reviews found.")


def main():
    parser = argparse.ArgumentParser(description="Google Maps Review Scraper - Scrape reviews from any business")
    parser.add_argument("-u", "--url", type=str, required=True,
                        help="Google Maps URL of the business (e.g. 'https://www.google.com/maps/place/...')")
    parser.add_argument("-t", "--total", type=int, default=50,
                        help="Total number of reviews to scrape (default: 50)")
    parser.add_argument("-o", "--output", type=str, default="reviews.csv",
                        help="Output file path (default: reviews.csv)")
    parser.add_argument("--excel", action="store_true",
                        help="Save as Excel (.xlsx) instead of CSV")
    parser.add_argument("--append", action="store_true",
                        help="Append results to existing file")
    args = parser.parse_args()

    print("\n" + "="*60)
    print(f"  GOOGLE MAPS REVIEW SCRAPER")
    print(f"="*60)
    print(f"  URL: {args.url[:60]}...")
    print(f"  Target reviews: {args.total}")
    print(f"  Output: {args.output}")
    print(f"="*60 + "\n")

    reviews = scrape_reviews(args.url, args.total)

    if args.excel:
        output = args.output.replace('.csv', '.xlsx') if args.output.endswith('.csv') else args.output
        save_reviews_to_excel(reviews, output)
    else:
        save_reviews_to_csv(reviews, args.output, append=args.append)


if __name__ == "__main__":
    main()
