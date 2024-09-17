import requests
from bs4 import BeautifulSoup
import csv
import time
import os


class IvoryResidence:
    def __init__(self, url="https://www.ivoryresidence.ro"):
        self.url = url
        self.headers = {
            "authority": "www.ivoryresidence.ro",
            "method": "GET",
            "path": "/apartamente/",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "referer": "https://www.ivoryresidence.ro/",
            "sec-ch-ua": '"Chromium";v="127", "Not)A;Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        }

    def fetch_page(self, page_url=""):
        if "https://www.ivoryresidence.ro" in page_url:
            page_url = page_url.replace("https://www.ivoryresidence.ro", "")

        full_url = self.url + "/" + page_url
        try:
            response = requests.get(full_url, headers=self.headers)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            print(f"Error fetching the webpage {full_url}: {e}")
            return None

    def extract_links_for_apartments(self):
        html_content = self.fetch_page("apartamente")
        if html_content is None:
            return {"apps": [], "links": []}

        soup = BeautifulSoup(html_content, "html.parser")

        row_div = soup.find(
            "div", class_="row justify-content-center align-items-stretch"
        )
        if not row_div:
            print(
                "No <div> found with class 'row justify-content-center align-items-stretch'."
            )
            return {"apps": [], "links": []}

        border_divs = soup.find_all(
            "div",
            class_="border border-muted rounded d-flex align-items-center px-3 py-4 flex-column text-center justify-content-center w-100",
        )

        extracted_data = []
        for border_div in border_divs:
            text_secondary = border_div.find(
                "div", class_="text-secondary h5 font-weight-bold"
            )
            text_primary_italic = border_div.find(
                "div", class_="text-primary h5 m-0 font-weight-bold font-italic"
            )

            data = {
                "tip": text_secondary.get_text(strip=True) if text_secondary else None,
                "pret": text_primary_italic.get_text(strip=True)
                if text_primary_italic
                else None,
            }

            extracted_data.append(data)

        divs = soup.find_all("div", class_="archive-apartments")
        links = []
        for div in divs:
            a_tags = div.find_all("a", href=True)
            for a in a_tags:
                link = a["href"]
                links.append(link)

        return {"apps": extracted_data, "links": links}

    def extract_apartment_data(self, url=""):
        if not url:
            print("No URL provided for extracting apartment data.")
            return {}

        html_content = self.fetch_page(url)
        if html_content is None:
            return {}

        soup = BeautifulSoup(html_content, "html.parser")

        title_element = soup.find("h1", class_="title")
        if title_element:
            apartment_title = title_element.get_text(strip=True)
        else:
            print("No <h1> found with class 'title'.")
            return {}

        table = soup.find("table", class_="caracteristici-apartament")
        if not table:
            print("No table found with class 'caracteristici-apartament'.")
            return {}

        apartment_metadata = {}
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) == 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)
                apartment_metadata[key] = value

        additional_metadata = []
        additional_table = soup.find("div", class_="table-responsive text-muted").find(
            "table"
        )
        if additional_table:
            additional_rows = additional_table.find_all("tr")
            headers = [
                header.get_text(strip=True)
                for header in additional_rows[0].find_all("th")
            ]
            for row in additional_rows[1:]:
                cols = row.find_all("td")
                if len(cols) == len(headers):
                    row_data = {
                        headers[i]: cols[i].get_text(strip=True)
                        for i in range(len(headers))
                    }
                    additional_metadata.append(row_data)

        apartment_data = {
            "title": apartment_title,
            "data": apartment_metadata,
            "availability": additional_metadata,
        }

        return apartment_data

    def export_apartment_prices_to_csv(self, prices_data):
        timestamp = int(time.time())
        output_csv_file = f"prices_data_{timestamp}.csv"

        try:
            with open(output_csv_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=["tip", "pret"])
                writer.writeheader()
                writer.writerows(prices_data)
            print(f"Data exported successfully to {output_csv_file}")
        except IOError as e:
            print(f"Error writing CSV file {output_csv_file}: {e}")

    def export_apartment_data_to_csv(self, data):
        timestamp = int(time.time())
        output_csv_file = f"apartments_data_{timestamp}.csv"

        try:
            with open(output_csv_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)

                # Write the header row
                writer.writerow(
                    [
                        "Titlu",
                        "Living",
                        "Bucătărie",
                        "Dormitor matrimonial",
                        "Baie",
                        "Hol",
                        "Dormitor",
                        "Suprafață utilă",
                        "Balcon",
                        "Suprafață utilă totală",
                        "Suprafață construită",
                        "Bloc",
                        "Scara",
                        "Apt.",
                        "Etaj",
                        "Disponibilitate",
                    ]
                )

                for entry in data:
                    title = entry.get("title", "N/A")
                    data_fields = [
                        entry["data"].get(field, "N/A")
                        for field in [
                            "Living",
                            "Bucătărie",
                            "Dormitor matrimonial",
                            "Baie",
                            "Hol",
                            "Dormitor",
                            "Suprafață utilă",
                            "Balcon",
                            "Suprafață utilă totală",
                            "Suprafață construită",
                        ]
                    ]
                    for availability in entry.get("availability", []):
                        row = (
                            [title]
                            + data_fields
                            + [
                                availability.get("Bloc", "0"),
                                availability.get("Scara", "0"),
                                availability.get("Apt.", "0"),
                                availability.get("Etaj", "0"),
                                availability.get("Disponibilitate", "0"),
                            ]
                        )
                        writer.writerow(row)

            print(f"Data exported successfully to {output_csv_file}")
        except IOError as e:
            print(f"Error writing CSV file {output_csv_file}: {e}")


# Example usage
if __name__ == "__main__":
    print("IvoryResidence scraper booted. Please wait while I dump the data...")
    scraper = IvoryResidence()
    links = scraper.extract_links_for_apartments()
    if links:
        scraper.export_apartment_prices_to_csv(links["apps"])
        data = []
        for link in links["links"]:
            apartment_data = scraper.extract_apartment_data(link)
            if apartment_data:
                data.append(apartment_data)
        if data:
            scraper.export_apartment_data_to_csv(data)
