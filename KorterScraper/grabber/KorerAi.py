import requests
from g4f.client import Client
import json
from concurrent.futures import ThreadPoolExecutor, as_completed


def is_json(myjson: any) -> bool:
    """Check if a string is a valid JSON."""
    myjson = str(myjson)
    try:
        json.loads(myjson)
    except ValueError as e:
        return False
    return True


class Korter:
    def __init__(self, ai_model: str = "gpt-3.5-turbo") -> None:
        self.ai_model = ai_model
        self._listing_urls = [
            "https://korter.ro/vanzare-apartamente-bucure%C8%99ti",
            "https://korter.ro/vanzare-apartamente-cluj-napoca",
            "https://korter.ro/vanzare-apartamente-arad",
            "https://korter.ro/vanzare-apartamente-bac%C4%83u",
            "https://korter.ro/vanzare-apartamente-boto%C8%99ani",
            "https://korter.ro/vanzare-apartamente-bragadiru",
            "https://korter.ro/vanzare-apartamente-bra%C8%99ov",
            "https://korter.ro/vanzare-apartamente-chiajna",
            "https://korter.ro/vanzare-apartamente-chitila",
            "https://korter.ro/vanzare-apartamente-constan%C5%A3a",
            "https://korter.ro/vanzare-apartamente-craiova",
            "https://korter.ro/vanzare-apartamente-dobroe%C8%99ti",
            "https://korter.ro/vanzare-apartamente-ia%C8%99i",
            "https://korter.ro/vanzare-apartamente-mamaia",
            "https://korter.ro/vanzare-apartamente-mamaia-sat",
            "https://korter.ro/vanzare-apartamente-mangalia",
            "https://korter.ro/vanzare-apartamente-m%C4%83gurele",
            "https://korter.ro/vanzare-apartamente-mogo%C8%99oaia",
            "https://korter.ro/vanzare-apartamente-oradea",
            "https://korter.ro/vanzare-apartamente-otopeni",
            "https://korter.ro/vanzare-apartamente-pantelimon",
            "https://korter.ro/vanzare-apartamente-pite%C8%99ti",
            "https://korter.ro/vanzare-apartamente-ploie%C8%99ti",
            "https://korter.ro/vanzare-apartamente-pope%C8%99ti-leordeni",
            "https://korter.ro/vanzare-apartamente-sebe%C8%99",
            "https://korter.ro/vanzare-apartamente-sibiu",
            "https://korter.ro/vanzare-apartamente-sighi%C8%99oara",
            "https://korter.ro/vanzare-apartamente-slatina",
            "https://korter.ro/vanzare-apartamente-suceava",
            "https://korter.ro/vanzare-apartamente-targoviste",
            "https://korter.ro/vanzare-apartamente-targu-mures",
            "https://korter.ro/vanzare-apartamente-timi%C8%99oara",
            "https://korter.ro/vanzare-apartamente-tunari",
            "https://korter.ro/vanzare-apartamente-voluntari",
        ]

    def grab_listings(self):
        request_url = "https://r.jina.ai/" + self._listing_urls[0]
        content = requests.get(request_url)
        print(content.text)
        links: list = []
        if content.status_code == 200:
            prompt_message = (
                "Using this markdown: "
                + content.text
                + ", please assemble a JSON with all the links and return them to me. "
                "Please keep in mind, I need the URLs to the apartment listings themselves and not the other ones. "
                "When returning the JSON structure, include all links under the 'apartment_listings' key. Example: {apartment_listings: [link1, link2, link3]}"
                "DO NOT INCLUDE the JSON markdown, just the curly braces."
            )
            client = Client()
            response = client.chat.completions.create(
                model=self.ai_model,
                messages=[{"role": "user", "content": prompt_message}],
            )

            response_content = response.choices[0].message.content
            if is_json(response_content):
                found_appartment_links = json.loads(response_content)
                if "apartment_listings" in found_appartment_links:
                    for link in found_appartment_links["apartment_listings"]:
                        print(f"Extracted Link: {link}")
                        links.append(link)

        if links:
            metadata = []
            with ThreadPoolExecutor(max_workers=len(links)) as executor:
                future_to_link = {
                    executor.submit(self.get_listing_data, link): link for link in links
                }
                for future in as_completed(future_to_link):
                    try:
                        result = future.result()
                        metadata.append(result)
                    except Exception as e:
                        print(f"Error occurred: {e}")

            print(metadata)
        else:
            print("NO links found!")

    def get_listing_data(self, url):
        apartment_data = []
        apartment_data["link"] = url
        apartment_data["details"] = None

        grab_markdown = requests.get("https://r.jina.ai/" + url)

        prompt_message = (
            "I need you to extract apartment attributes from the markdown I will provide next. "
            "These attributes include important metadata about the apartment such as: "
            "price, square footage, area, number of rooms, floor, number of bathrooms, year built, "
            "and any other relevant information like parking availability or commission percentage. "
            "Once you've extracted the relevant information, I need you to format the output as a valid JSON string. "
            "Only return the JSON string—no extra text or explanations. "
            "Please follow this json structure everywhere: {'price': '87,800 €', 'square_footage': '56.29 m2', 'area': 'București', 'number_of_rooms': 2, 'floor': 'P, 1-10 etaje', 'year_built': '2021', 'developer': 'Brad Realty'}"
            "Of course, simply replace the values if found."
            "The markdown containing the listing data is this: " + grab_markdown.text
        )

        if grab_markdown.status_code == 200:
            client = Client()
            response = client.chat.completions.create(
                model=self.ai_model,
                messages=[{"role": "user", "content": prompt_message}],
            )

            response_content = response.choices[0].message.content

            if is_json(response_content):
                extracted_json = json.loads(response_content)
                print(
                    f"Found appartment metadata for link: {url} -> {str(extracted_json)}"
                )
                apartment_data["details"].append(extracted_json)

        return apartment_data
