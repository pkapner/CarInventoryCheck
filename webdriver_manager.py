# webdriver_manager.py
import atexit
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from undetected_chromedriver import ChromeOptions


class WebDriverManager:
    _instance = None

    @staticmethod
    def get_driver():
        if WebDriverManager._instance is None:
            options = Options()
            options.add_argument(
                "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            # ✅ Initialize WebDriver
            service = Service("/opt/homebrew/bin/chromedriver")
            WebDriverManager._instance = webdriver.Chrome(service=service, options=options)
            atexit.register(WebDriverManager._instance.quit)
        return WebDriverManager._instance
