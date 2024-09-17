import undetected_chromedriver as uc
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import random

class RealEstateScraper:
    def __init__(self) -> None:
        self._main_url = "https://www.imobiliare.ro"
        self._sales_url = self._main_url + "/vanzare-imobiliare"
        
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')

        self.driver = uc.Chrome(options=options)
        
        stealth(
            self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True
        )
        self.driver.delete_all_cookies()

    def slow_navigation(self, url):
        self.driver.get(url)
        time.sleep(random.uniform(2, 5))
        
    def grab_listings(self):
        self.slow_navigation(self._sales_url)
        self.driver.implicitly_wait(10)

        try:
            input("Please solve the CAPTCHA if it appears, then press Enter to continue...")

            page_content = self.driver.page_source
            print(page_content)

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            self.driver.quit()