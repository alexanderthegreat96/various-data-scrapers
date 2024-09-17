from grabber.Korter import Korter
from concurrent.futures import ThreadPoolExecutor, as_completed

korter = Korter()

urls = {
    "bucurești": "https://korter.ro/vanzare-apartamente-bucure%C8%99ti",
    "cluj-napoca": "https://korter.ro/vanzare-apartamente-cluj-napoca",
    "arad": "https://korter.ro/vanzare-apartamente-arad",
    "bacău": "https://korter.ro/vanzare-apartamente-bac%C4%83u",
    "botoșani": "https://korter.ro/vanzare-apartamente-boto%C8%99ani",
    "bragadiru": "https://korter.ro/vanzare-apartamente-bragadiru",
    "brașov": "https://korter.ro/vanzare-apartamente-bra%C8%99ov",
    "chiajna": "https://korter.ro/vanzare-apartamente-chiajna",
    "chitila": "https://korter.ro/vanzare-apartamente-chitila",
    "constanța": "https://korter.ro/vanzare-apartamente-constan%C5%A3a",
    "craiova": "https://korter.ro/vanzare-apartamente-craiova",
    "dobroești": "https://korter.ro/vanzare-apartamente-dobroe%C8%99ti",
    "iași": "https://korter.ro/vanzare-apartamente-ia%C8%99i",
    "mamaia": "https://korter.ro/vanzare-apartamente-mamaia",
    "mamaia-sat": "https://korter.ro/vanzare-apartamente-mamaia-sat",
    "mangalia": "https://korter.ro/vanzare-apartamente-mangalia",
    "măgurele": "https://korter.ro/vanzare-apartamente-m%C4%83gurele",
    "mogoșoaia": "https://korter.ro/vanzare-apartamente-mogo%C8%99oaia",
    "oradea": "https://korter.ro/vanzare-apartamente-oradea",
    "otopeni": "https://korter.ro/vanzare-apartamente-otopeni",
    "pantelimon": "https://korter.ro/vanzare-apartamente-pantelimon",
    "pitești": "https://korter.ro/vanzare-apartamente-pite%C8%99ti",
    "ploiesti": "https://korter.ro/vanzare-apartamente-ploie%C8%99ti",
    "popesti-leordeni": "https://korter.ro/vanzare-apartamente-pope%C8%99ti-leordeni",
    "sebeș": "https://korter.ro/vanzare-apartamente-sebe%C8%99",
    "sibiu": "https://korter.ro/vanzare-apartamente-sibiu",
    "sighișoara": "https://korter.ro/vanzare-apartamente-sighi%C8%99oara",
    "slatina": "https://korter.ro/vanzare-apartamente-slatina",
    "suceava": "https://korter.ro/vanzare-apartamente-suceava",
    "targoviste": "https://korter.ro/vanzare-apartamente-targoviste",
    "targu-mures": "https://korter.ro/vanzare-apartamente-targu-mures",
    "timișoara": "https://korter.ro/vanzare-apartamente-timi%C8%99oara",
    "tunari": "https://korter.ro/vanzare-apartamente-tunari",
    "voluntari": "https://korter.ro/vanzare-apartamente-voluntari",
}

if urls:
    # will not work
    # the server cannot handle these many requests
    # with ThreadPoolExecutor(max_workers=2) as executor:
    #     futures = {
    #         executor.submit(korter.process_listings, page_url, base_name): (page_url, base_name)
    #         for base_name,page_url in urls.items()
    #     }

    #     for future in as_completed(futures):
    #         future.result()

    for base_name, url in urls.items():
        korter.process_listings(base_name=base_name, base_url=url)
