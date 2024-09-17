from grabber.html_decoder import HtmlDecoder
from bs4 import BeautifulSoup
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
import csv


def extract_rooms(tags):
    pattern = r"(\d+ camere|\d+ apartament|\d+ garsonier)"
    for tag in tags:
        match = re.search(pattern, tag, re.IGNORECASE)
        if match:
            return int(match.group().split()[0])  # Return just the number
    return 0


def extract_square_footage(tags):
    pattern = r"\d+(\.\d+)?\s*m2"
    for tag in tags:
        match = re.search(pattern, tag, re.IGNORECASE)
        if match:
            return re.sub(r"[^\d.,]", "", match.group())
    return "0"


def extract_floor_no(tags):
    pattern = r"etaj.*?(\d+)"
    for tag in tags:
        match = re.search(pattern, tag, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 0


def extract_bathrooms(tags):
    pattern = r"(\d+)\s*(baie|băi)"
    for tag in tags:
        match = re.search(pattern, tag, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 0


def extract_bedrooms(tags):
    pattern = r"\d+\s*(dormitor|dormitoare)"
    for tag in tags:
        match = re.search(pattern, tag, re.IGNORECASE)
        if match:
            return int(re.split(r"\s+", match.group())[0])  # Return just the number
    return 0


def extract_price(tags):
    pattern = r"[\d\s,]+€(?:\s*\+\s*TVA)?"
    price_matches = []

    for tag in tags:
        matches = re.findall(pattern, tag, re.IGNORECASE)
        for match in matches:
            price_matches.append(normalize_price(match))

    # Return the maximum price or "N/A" if no matches
    if price_matches:
        return int(max(price_matches))
    return 0


def extract_price_per_mp(tags):
    pattern = r"[\d\s,]+€(?:\s*\+\s*TVA)?"
    price_matches = []

    for tag in tags:
        matches = re.findall(pattern, tag, re.IGNORECASE)
        for match in matches:
            price_matches.append(normalize_price(match))

    if price_matches:
        return int(min(price_matches))
    return 0


def normalize_price(price_str):
    # Remove currency symbols and non-numeric characters (except for decimal points)
    return float(re.sub(r"[^\d,]", "", price_str).replace(",", "."))


class Korter:
    def __init__(self) -> None:
        pass

    def process_listings(
        self,
        base_url: str = "https://korter.ro/vanzare-apartamente-bucure%C8%99ti",
        base_name: str = "Bucuresti",
    ):
        print(f"Using: {base_name} with {base_url} to pull listings...")

        first_page_html = requests.get(base_url)

        if first_page_html.status_code == 200:
            decoder = HtmlDecoder(first_page_html.text)
            content = decoder.get_html()
            soup = BeautifulSoup(content, "html.parser")

            # Extract page numbers to find the last page
            pages_container = soup.find_all(
                "a",
                class_="default-default-container-container-container-container-container-container-container-ul-li-link-class",
            )
            last_page = self.extract_listing_pages(pages_container)
            print(f"Found last page number: {last_page}")

            page_urls = [
                f"{base_url}?page={page_num}" for page_num in range(1, last_page + 1)
            ]
            all_apartments = []

            # for url in page_urls:
            #     result = self.fetch_and_process_page(url, all_apartments)
            #     all_apartments.append(result)

            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = {
                    executor.submit(
                        self.fetch_and_process_page, page_url, all_apartments
                    ): page_url
                    for page_url in page_urls
                }

                for future in as_completed(futures):
                    future.result()

            print(f"Fetched: {len(all_apartments)}")
            print("Will begin data dump...")

            csv_file = (
                "exported/"
                + base_name
                + "_all_appartments_"
                + str(int(time.time()))
                + ".csv"
            )

            self.save_apartments_to_csv(all_apartments, base_name)
        else:
            print(
                f"Failed to retrieve the first page. Status code: {first_page_html.status_code}"
            )

    def save_apartments_to_csv(self, all_apartments, prefix, output_dir="exported"):
        # Ensure the output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if all_apartments:
            # Generate a unique filename with a timestamp
            csv_file = os.path.join(
                output_dir, f"{prefix}_all_apartments_{int(time.time())}.csv"
            )

            headers = all_apartments[0].keys()

            # Write data to CSV file
            with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()

                for property_data in all_apartments:
                    if property_data:
                        row = {key: str(property_data.get(key, "")) for key in headers}
                        writer.writerow(row)

            print(f"Data collection complete and saved to {csv_file}")
        else:
            print("No apartments found")

    def fetch_and_process_page(self, page_url, page_apartments):
        print(f"Processing URL: {page_url}")
        page_html = requests.get(page_url)

        if page_html.status_code == 200:
            decoder = HtmlDecoder(page_html.text)
            content = decoder.get_html()
            soup = BeautifulSoup(content, "html.parser")

            listings_container = soup.find_all(
                "div",
                class_="default-default-container-container-container-container-container-container-container-container-class",
            )
            if not listings_container:
                print(f"Unable to process the listings container on {page_url}.")
                return []

            urls = []
            for listing in listings_container:
                self.extract_listing_urls(listing, urls)

            if urls:
                num_workers = len(urls)
                with ThreadPoolExecutor(4) as executor:
                    futures = [
                        executor.submit(self.extract_listing_metadata, url)
                        for url in urls
                    ]
                    for future in as_completed(futures):
                        result = future.result()
                        if result is not None:
                            page_apartments.append(result)

        else:
            print(
                f"Failed to retrieve {page_url}. Status code: {page_html.status_code}"
            )
        return page_apartments

    def clean_text(self, text):
        # Remove zero-width joiners and any extra whitespace
        cleaned_text = text.replace("\u200d", "").strip()
        return cleaned_text

    def extract_listing_metadata(self, url: str):
        print(f"Processing metadata for: {url}")
        metadata = {}
        html = requests.get("https://korter.ro" + url)
        if html.status_code == 200:
            decoder = HtmlDecoder(html.text)
            content = decoder.get_html()
            listing = BeautifulSoup(content, "html.parser")

            title_tag = listing.find(
                "h1",
                class_="default-default-container-container-container-container-container-container-container-default-class",
            )
            metadata["title"] = title_tag.get_text(strip=True) if title_tag else "N/A"

            tags = listing.find_all(
                "div",
                class_="default-default-container-container-container-container-container-container-container-container-container-container-class",
            )
            available_tags = []
            if tags:
                for tag in tags:
                    tag = tag.get_text(strip=True)
                    if tag:
                        available_tags.append(self.clean_text(tag))
                    # for child in tag.find_all(recursive=False):  # `recursive=False` to avoid deep traversal
                    #     # Extract text from each child element and append it
                    #     child = child.get_text(strip=True)
                    #     if child:
                    #         available_tags.append(child)

            metadata["complex"] = self.extract_complex_builder(metadata["title"])
            metadata["address"] = available_tags[0] if available_tags[0] else "N/A"
            metadata["price"] = 0
            metadata["price_per_mp"] = 0
            metadata["rooms"] = 0
            metadata["square_footage"] = 0
            metadata["floor_no"] = 0
            metadata["bathrooms"] = 0
            metadata["bedrooms"] = 0

            regex_patterns = {
                "price": r"[\d\s,]+€(?:\s*\+\s*TVA)?",
                "price_per_mp": r"\d{1,3}(?:\s*\d{3})*(?:,\d+)?\s*€\s*/\s*m2",
                "rooms": r"(\d+ camere|\d+ apartamnt|\d+ garsonier)",
                "square_footage": r"\d+(\.\d+)?\s*m2",
                "floor_no": r"etaj.*?(\d+)",
                "bathrooms": r"(\d+)\s*(baie|băi)",
                "bedrooms": r"\d+\s*(dormitor|dormitoare)",
            }

            for tag in available_tags:
                for key, pattern in regex_patterns.items():
                    match = re.search(pattern, tag, re.IGNORECASE)
                    if match:
                        metadata[key] = match.group()
                        break

            metadata["price"] = extract_price(available_tags)
            metadata["price_per_mp"] = extract_price_per_mp(available_tags)
            metadata["bathrooms"] = extract_bathrooms(available_tags)
            metadata["bedrooms"] = extract_bedrooms(available_tags)
            metadata["rooms"] = extract_rooms(available_tags)
            metadata["square_footage"] = extract_square_footage(available_tags)
            metadata["floor_no"] = extract_floor_no(available_tags)

        else:
            print(f"Unable to query: {url} - {html.status_code}")

        return metadata

    def extract_complex_builder(self, title):
        parts = title.split("–")
        if parts:
            complex_builder = parts[0].strip()
        else:
            complex_builder = "N/A"
        return complex_builder

    def extract_listing_pages(self, listing, page: int = 0):
        pages = []
        if listing:
            for item in listing:
                if "href" in item.attrs:
                    href = item["href"]
                    match = re.search(r"\?page=(\d+)", href)
                    if match:
                        page_number = int(match.group(1))
                        pages.append(page_number)

        max_page = max(pages, default=0)
        return max_page

    def extract_listing_urls(self, listing, urls: list = None):
        link_tag = listing.find_all(
            "a",
            class_="default-default-container-container-container-container-container-container-container-container-link-class",
        )
        if link_tag:
            for link in link_tag:
                if "href" in link.attrs:
                    urls.append(link["href"])

        return urls
