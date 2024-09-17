from grabber.SkiaOneScraper import SkiaOneScrapper
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import time

filters = {}


def fetch_page_data(scraper, filters, page):
    return scraper.filtered_properties(filters, page)


def run_scraper():
    scraper = SkiaOneScrapper()
    all_properties = []
    max_workers = 16

    last_page = scraper.grab_last_page(filters)
    max_page = last_page if last_page else 10

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(fetch_page_data, scraper, filters, page)
            for page in range(0, max_page)
        ]
        for future in as_completed(futures):
            try:
                all_properties.extend(future.result())
            except Exception as e:
                print(f"Error fetching data: {e}")

    csv_file = "exported/all_properties_" + str(int(time.time())) + ".csv"

 
    headers = ["title", "link"] + list(all_properties[0]["details"].keys())
    
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()

        for property_data in all_properties:
            row = {"title": property_data["title"], "link": property_data["link"]}

            row.update(property_data["details"])
            row = {key: row.get(key, "") for key in headers}

            writer.writerow(row)

    print(f"Data collection complete and saved to {csv_file}")


run_scraper()
