# import requests
# from fake_useragent import UserAgent
# import random
# from grabber.html_decoder import HtmlDecoder
# from bs4 import BeautifulSoup

# # Generate a random User-Agent using fake_useragent
# ua = UserAgent()

# headers = {
#     "User-Agent": ua.random,
#     "Accept-Language": "en-US,en;q=0.9",
#     "Accept-Encoding": "gzip, deflate, br",
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
#     "Connection": "keep-alive",
#     "Referer": "https://www.google.com",
#     "DNT": "1"
# }

# url = 'https://www.storia.ro/ro/rezultate/vanzare/apartament/bucuresti?limit=36&ownerTypeSingleSelect=ALL&by=BEST_MATCH&direction=DESC&viewType=listing'
# response = requests.get(url, headers=headers)

# if response.status_code == 200:
#     html = HtmlDecoder(response.text)
    
#     content = html.get_html(True, True)
#     # soup = BeautifulSoup(content, "html.parser")
#     # links = soup.find_all("a", class_="default-default-container-container-default-container-container-container-container-container-container-ul-li-default-section-container-link-class")
    
#     # found_urls = []
#     # if links:
#     #     for link in links:
#     #         if "href" in link.attrs:
#     #             found_urls.append(link["href"])

#     # if found_urls:
#     #     to_query = found_urls[0]
        