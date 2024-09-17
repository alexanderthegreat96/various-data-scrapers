from bs4 import BeautifulSoup
import requests
import logging
import json

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

def build_query_string(query: dict) -> str:
    if query:
        query_string = "&".join([f"{key}={value}" for key, value in query.items()])
        return f"?{query_string}"
    return ""

class SkiaOneScrapper:
    def __init__(self, locale: str = "ro") -> None:
        self.__main_url = "https://skia.one.ro"

        self.__filter_properties_url = (
            self.__main_url + "/" + locale + "/" + "proprietati"
        )

    def __fetch_property_data(self, request_url: str) -> dict:
        logging.info(f"Fetching property data for: {request_url}")

        metadata = {
            "floor": "N/A",
            "area": "N/A",
            "bedrooms": "N/A",
            "terrace": "N/A",
            "parking": "N/A",
            "price": "N/A",
            "price_with_vat": "N/A",
            "availability": "N/A",
            "project": "N/A",
            "phase": "N/A",
            "building_floors": "N/A",
            "building_type": "N/A",
            "energy_class": "N/A",
            "building_structure": "N/A",
            "building_status": "N/A",
            "completion_date": "N/A",
            "sector": "N/A",
            "neighborhood": "N/A",
        }

        response = requests.get(request_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            details_container = soup.find(
                "div", class_="row no-gutters property-details"
            )

            if details_container:
                details = details_container.find_all(
                    "div", class_="col-6 col-lg-4 col-xl-3"
                )

                for detail in details:
                    field_label = detail.find(
                        "div", class_="property-details-field"
                    ).text.strip()
                    field_value_tag = detail.find(
                        "div", class_="property-details-value"
                    )

                    field_value = (
                        field_value_tag.text.strip().replace("\xa0", " ")
                        if field_value_tag
                        else "N/A"
                    )
                    label_map = {
                        "Etaj:": "floor",
                        "Suprafață:": "area",
                        "Dormitoare:": "bedrooms",
                        "Terasă:": "terrace",
                        "Parcare:": "parking",
                        "Preț:": "price",
                        "Preț cu TVA:": "price_with_vat",
                        "Disponibilitate:": "availability",
                        "Proiect:": "project",
                        "Fază:": "phase",
                        "Etaje clădire:": "building_floors",
                        "Tip imobil:": "building_type",
                        "Clasă energetică:": "energy_class",
                        "Structură clădire:": "building_structure",
                        "Starea clădirii:": "building_status",
                        "Termen finalizare:": "completion_date",
                        "Sector:": "sector",
                        "Cartier:": "neighborhood",
                    }

                    field_key = label_map.get(field_label)
                    if field_key:
                        metadata[field_key] = field_value

        return metadata

    def grab_last_page(self, filters: dict) -> int:
        last_page = 0

        request_url = self.__filter_properties_url + build_query_string(filters)
        response = requests.get(request_url)

        if response.status_code == 200:
            logging.info("Grabbing last page number")

            soup = BeautifulSoup(response.content, "html.parser")
            pagination_nav = soup.find("nav", class_="pagination-container")

            if pagination_nav:
                data_paging = pagination_nav.get("data-paging")

                if data_paging:
                    paging_info = json.loads(data_paging)
                    last_page = paging_info.get("pages")

        return last_page

    def filtered_properties(self, filters: dict, page: int = 0) -> list:
        if not filters:
            filters = {}

        if page > 0:
            filters["page"] = page

        request_url = self.__filter_properties_url + build_query_string(filters)
        response = requests.get(request_url)

        if response.status_code == 200:
            logging.info(f"Grabbing properties for page: {page}")
            soup = BeautifulSoup(response.content, "html.parser")

            property_container = soup.find(
                "div", class_="row no-gutters my-3 properties-row"
            )
            if not property_container:
                logging.error("No properties found")
                return []

            property_column_container = property_container.find_all(
                "div", class_="property-col"
            )
            if not property_column_container:
                logging.error("No property col container found")

            property_list = []
            for col in property_container:
                property_card = col.find("div", class_="property-card")

                title_tag = property_card.find("h3", class_="property-card-title")
                title = title_tag.text.strip() if title_tag else "N/A"

                price_tag = property_card.find("div", class_="pricing-btn")
                price = (
                    price_tag.text.strip().replace("\xa0", " ") if price_tag else "N/A"
                )

                bedroom_tag = property_card.find("div", class_="bedroom-icon")
                bedrooms = bedroom_tag.text.strip() if bedroom_tag else "N/A"

                area_tag = property_card.find("div", class_="area-icon")
                area = area_tag.text.strip() if area_tag else "N/A"

                floor_tag = property_card.find("div", class_="floor-icon")
                floor = floor_tag.text.strip() if floor_tag else "N/A"

                link_tag = property_card.find("a", href=True)
                link = link_tag["href"] if link_tag else "N/A"

                logging.info(f"Processing: {title} with URL: {link}")

                property_list.append(
                    {
                        "title": title,
                        "price": price,
                        "bedrooms": bedrooms,
                        "area": area,
                        "floor": floor,
                        "link": link,
                        "details": self.__fetch_property_data(link),
                    }
                )

            return property_list
        else:
            logging.error(f"failed to retrieve properties: {response.status_code}")
            return []
