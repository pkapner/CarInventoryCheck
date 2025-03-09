import openai
import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from InventoryCheck import extract_vins  # Ensure this function is correctly implemented
from webdriver_manager import WebDriverManager

SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
OPENAI_API_KEY = 'key'
EXCLUDE_SITES = "-site:edmunds.com -site:capitalone.com"

driver = WebDriverManager.get_driver()


def google_search_vin(vin):
    """Search Google for dealer listings of a specific VIN and extract result links."""
    search_url = f"https://www.google.com/search?q={vin}+-site:edmunds.com+-site:capitalone.com+-site:kbb.com"

    driver.get(search_url)

    try:
        # Wait until search results are fully loaded
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tF2Cxc")))

        # Use a better selector: Google's results are in <div class="tF2Cxc">, each with an <a>
        results = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc a")

        urls = []
        for r in results:
            url = r.get_attribute("href")
            if url and "google.com" not in url:  # Avoid Google redirects
                urls.append(url)

        print(f"🔍 Found {len(urls)} result(s).")
        return urls[:5]  # Return top 5 valid results

    except Exception as e:
        print(f"❌ Error extracting Google results: {e}")
        return []


def extract_page_source(url):
    """Load a webpage and return the full HTML source."""
    driver.get(url)
    time.sleep(3)  # Allow JavaScript to render
    return driver.page_source


def extract_car_details(html_content, url):
    """Send HTML to OpenAI and extract structured car details in JSON format."""
    openai.api_key = OPENAI_API_KEY

    prompt = f"""
    You are an AI that extracts car details from dealership pages. 
    Given the raw HTML below, return a JSON object with:

    - "Make": Car manufacturer (e.g., "Mercedes-Benz")
    - "Model": Car model (e.g., "GLC 300")
    - "Year": Year (e.g., "2025")
    - "Trim": Trim level (e.g., "4MATIC")
    - "Price": Advertised price (e.g., "59995")
    - "Mileage": Odometer reading (if available, else null)
    - "Dealer Name": The dealership selling the car
    - "Location": City and State of the dealer
    - "VIN": The car's Vehicle Identification Number
    - "Features": A list of notable options (e.g., ["Panoramic Roof", "Heated Seats"])

    ONLY return a JSON object. Do NOT include explanations or text outside JSON.

    HTML Content:
    {html_content[:10000]}  # Limit input size for safety
    """

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    raw_output = response["choices"][0]["message"]["content"]

    try:
        parsed_data = json.loads(raw_output)  # Ensure the response is valid JSON
        parsed_data["URL"] = url  # Add the source URL
        return parsed_data
    except json.JSONDecodeError:
        print("❌ Error: OpenAI returned invalid JSON.")
        print("🔍 Raw Output:", raw_output)  # Debugging: Print the raw response
        return None


def scrape_vin(vin):
    """Find and scrape dealer pages for a given VIN."""
    dealer_urls = google_search_vin(vin)

    car_data = []
    for url in dealer_urls:
        print(f"🔍 Checking {url}...")

        # Fetch the page source
        page_html = extract_page_source(url)

        if page_html:  # Ensure we actually got HTML
            # Pass BOTH arguments: HTML content + URL
            car_data = extract_car_details(page_html, url)

            if car_data:
                print(f"✅ Extracted Data:\n{json.dumps(car_data, indent=2)}\n")
        else:
            print(f"❌ Failed to retrieve page source for {url}")

    return car_data


vins = extract_vins()
for vin in vins:
    print(f"🔍 Searching for VIN: {vin}")
    car_details = scrape_vin(vin)
    print(json.dumps(car_details, indent=4))

#
# # Example usage
# vin_to_search = "W1NKM4HB7SF239161"
# car_details = scrape_vin(vin_to_search)
#
# # Save to JSON file
# with open("car_data.json", "w") as f:
#     json.dump(car_details, f, indent=4)
#
# print(json.dumps(car_details, indent=4))

# Close Selenium WebDriver
driver.quit()
