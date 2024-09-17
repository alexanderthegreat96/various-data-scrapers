import requests
from fake_useragent import UserAgent
import random
from grabber.html_decoder import HtmlDecoder
from bs4 import BeautifulSoup
import re
import math
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time

def extract_last_page_from_list(tags):
    total_ads = 0
    ads_per_page = 0

    # Iterate through each tag to find the necessary information
    for tag in tags:
        # Extract the total number of ads
        total_ads_pattern = r"din\s*(\d+)"
        match_total_ads = re.search(total_ads_pattern, tag)
        
        if match_total_ads:
            total_ads = int(match_total_ads.group(1))
        
        # Extract the number of ads per page (the range, 1-36)
        ads_per_page_pattern = r"(\d+)-(\d+)"
        match_ads_per_page = re.search(ads_per_page_pattern, tag)
        
        if match_ads_per_page:
            ads_per_page = int(match_ads_per_page.group(2))  # The second number is the per-page count

    # If both values were found, calculate the last page number
    if total_ads > 0 and ads_per_page > 0:
        last_page = math.ceil(total_ads / ads_per_page)
        return last_page
    
    return 0  # If no match, return 0

def extract_price(tag_list):
    price_pattern = r"[\d\s]+€"
    prices = []
    
    for tag in tag_list:
        match = re.search(price_pattern, tag)
        if match:
            # Clean the price, remove non-numeric characters except for space
            price = re.sub(r'[^\d]', '', match.group())
            prices.append(int(price))
    
    # Return min and max if we find multiple prices
    if prices:
        return max(prices)
    
    return 0, 0

def extract_price_per_sqm(tag_list):
    price_per_sqm_pattern = r"\d{1,3}(?:\s*\d{3})*\s*€/m²"
    prices_per_sqm = []
    
    for tag in tag_list:
        match = re.search(price_per_sqm_pattern, tag)
        if match:
            price_per_sqm = re.sub(r'[^\d]', '', match.group())
            prices_per_sqm.append(int(price_per_sqm))

    if prices_per_sqm:
        return min(prices_per_sqm)
    
    return 0, 0

class Storia:
    def __init__(self, main_url : str = None) -> None:
        self.main_url = main_url
        self.root_url = "https://storia.ro"
    
    def make_legit_request(self, url : str = None) -> requests:
        ua = UserAgent()
        headers = {
            "User-Agent": ua.random,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
            "Referer": "https://www.google.com",
            "DNT": "1"
        }
        return requests.get(url, headers=headers)
    
    def decode_html(self, html : str = None, beautify : bool = False, dump : bool = True):
        decode = HtmlDecoder(html)
        return decode.get_html(beautify, dump)
        
    def fetch_listing_metadata(self, url : str = None, appartments : list = None):
        print(f"Using {url} to grab metadata...")
        
        response = self.make_legit_request(url)
        if response.status_code == 200:
            
            print(f"Processing metadata for {url}...")
            
            content = self.decode_html(response.text)
            soup = BeautifulSoup(content, "html.parser")
            
            metadata : dict = {}
            metadata['title'] = "No tile found"
            metadata['developer'] = "Owner - N/A"
            metadata['url'] = url
            metadata['price'] = '0'
            metadata['price_per_square_m'] = '0'
            metadata['square_footage'] = "0"
            metadata['rooms'] = "0"
            metadata['address'] = "Not found"
            
            title = soup.find("h1", class_="default-default-container-container-default-container-container-container-container-default-class")
            metadata['title'] = title.text if title else "No title found."
            
            sq_rooms_list = []
            sq_rooms = soup.find_all("div", class_="default-default-container-container-default-container-container-container-container-class")
            if sq_rooms:
                for room in sq_rooms:
                    square_area = room.find_all("button", class_="default-default-container-container-default-container-container-container-container-default-class")
                    if square_area:
                        for sq in square_area:
                            sq_text = sq.get_text(strip=True)
                            if sq_text:
                                sq_rooms_list.append(sq_text)
            if sq_rooms_list:
                metadata['square_footage'] = sq_rooms_list[1] if sq_rooms_list[1] else "0.0 m²"
                metadata['rooms'] = sq_rooms_list[2] if sq_rooms_list[2] else "0"
                
            address = "Not found"    
            div_address = soup.find_all("div", class_="default-default-container-container-default-container-container-container-container-container-class")
            if div_address:
                for div in div_address:
                    address_link = div.find("a", class_= "default-default-container-container-default-container-container-container-container-container-link-class")
                    if address_link:
                        address = address_link.get_text(strip=True)
            
            metadata['address'] = address
            
            price_list = []
            
            prices_container = soup.find_all("div", class_="default-default-container-container-default-container-container-container-container-container-class")
            if prices_container:
                for price in prices_container:
                    first_price_container = price.find_all("div", class_="default-default-container-container-default-container-container-container-container-container-container-class")   
                    if first_price_container:
                        for fp in first_price_container:
                            fp_text = fp.get_text(strip=True)
                            if fp_text:
                                price_list.append(fp_text)
            
            metadata['price'] = extract_price(price_list)
            metadata['price_per_square_m'] = extract_price_per_sqm(price_list)
            
            developer_container = soup.find("strong", class_="default-default-container-container-default-container-container-container-container-container-default-container-container-span-default-class")
            if developer_container:
                metadata['developer'] = developer_container.get_text(strip=True)
            
            appartments.append(metadata)
        else:
            print(f"Unable to parse listing: {response.status_code}. Aborting.")
    
    def fetch_listings(self):
            response = self.make_legit_request(self.main_url)

            if response.status_code == 200:
                content = self.decode_html(response.text)
                soup = BeautifulSoup(content, "html.parser")
                
                pages_list = []
                pages_container = soup.find_all('div', class_="default-default-container-container-default-container-container-container-container-container-container-container-container-container-container-container-container-class")
                if pages_container:
                    for page in pages_container:
                        pages_list.append(page.get_text(strip=True))
                
                last_page = 10
                if pages_list:
                    last_page = extract_last_page_from_list(pages_list)
  
                links = soup.find_all("a", class_="default-default-container-container-default-container-container-container-container-container-container-ul-li-default-section-container-link-class")
    
                found_urls = []
                if links:
                    for link in links:
                        if "href" in link.attrs:
                            found_urls.append(link["href"])
                            
                # implement the usage of pages
                # if the page is larger than 1
                # otherwise do not include the &page in the reuquest

                appartments = []
                if found_urls:
                    # print(f"Found {len(found_urls)}, processing metadata...")
                    # # only using the first one for testing
                    
                    # #to_query = self.root_url + found_urls[0]
                    # for url in found_urls:
                    #     self.fetch_listing_metadata(self.root_url + url, appartments)
                    # Process all listing URLs in parallel
                    with ThreadPoolExecutor(max_workers=6) as executor:
                        futures = [
                            executor.submit(self.fetch_listing_metadata, self.root_url + url, appartments)
                            for url in found_urls
                        ]
                        for future in as_completed(futures):
                            future.result()

                else:
                    print(f"Unable to fetch listing urls for: {self.main_url}")
                    

                # if last_page > 1:
                #     for page_num in range(2, 5):
                #         print(f"Processing page {page_num}...")
                #         paginated_url = f"{self.main_url}&page={page_num}"
                #         self.fetch_listings_for_page(paginated_url, appartments)
                if last_page > 1:
                    with ThreadPoolExecutor(max_workers=4) as executor:
                        page_futures = []
                        for page_num in range(2, last_page + 1):
                            print(f"Processing page {page_num} in parallel...")
                            paginated_url = f"{self.main_url}&page={page_num}"
                            page_futures.append(executor.submit(self.fetch_listings_for_page, paginated_url, appartments))

                        # Wait for all pages to finish processing
                        for future in as_completed(page_futures):
                            future.result()  # Ensure completion and handle potential errors

                            

                if len(appartments):
                    self.save_apartments_to_csv(appartments, "storia-dd")        
                    
                print(f"Data parsing complete. Processed: {len(appartments)}")
            else:
                print(f"Unable to process request: {response.status_code}")
    
    def fetch_listings_for_page(self, request_url: str, appartments : list):
        response = self.make_legit_request(request_url)
        
        if response.status_code == 200:
            content = self.decode_html(response.text)
            soup = BeautifulSoup(content, "html.parser")
            
            links = soup.find_all("a", class_="default-default-container-container-default-container-container-container-container-container-container-ul-li-default-section-container-link-class")
            
            found_urls = []
            if links:
                for link in links:
                    if "href" in link.attrs:
                        found_urls.append(link["href"])
            
            if found_urls:
                # for url in found_urls:
                #     to_query = self.root_url + url
                #     self.fetch_listing_metadata(to_query, appartments)
                with ThreadPoolExecutor(max_workers=6) as executor:
                        futures = [
                            executor.submit(self.fetch_listing_metadata, self.root_url + url, appartments)
                            for url in found_urls
                        ]
                        for future in as_completed(futures):
                            future.result()
            else:
                print(f"No listing URLs found on page: {request_url}")
        else:
            print(f"Failed to fetch page: {request_url}, status code: {response.status_code}")

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