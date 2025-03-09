import json
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

import webdriver_manager
from webdriver_manager import WebDriverManager

import atexit
from selenium import webdriver


# Register a cleanup function to close the WebDriver when the program exits


# WebDriver will stay open until the script ends, then `driver.quit()` will run automatically


# ✅ Setup Chrome with anti-detection options


# CarLookup.py
driver = WebDriverManager.get_driver()

# Perform car lookup...


color = "Red"

BASE_URL = "https://www.truecar.com/new-cars-for-sale/listings/mercedes-benz/glc/location-new-york-ny/?exteriorColorGeneric[]=" + color + "&trimSlug[]=GLC%20300&trimSlug[]=glc-300"

base_url = BASE_URL

  # Generate the refined URL
# print("🔗 Searching with URL:", base_url)

import time

def scrape_all_pages():
    all_listings = []
    current_page = 1
    previous_count = 0  # Track the number of listings in previous iteration

    while True:
        url = base_url + "&page=" + str(current_page)
        # print(f"📄 Scraping page {current_page}: {url}")

        driver.get(url)  # Navigate to the page
        time.sleep(5)  # Allow time for the page to load

        # Extract listings
        WebDriverManager.get_driver()
        listings = extract_listings()  # Ensure this function returns data
        # print(f"🔍 DEBUG: Extracted {len(listings)} listings on page {current_page}")

        if listings:
            all_listings.extend(listings)  # Append found listings to the main list
            previous_count = len(all_listings)  # Update count

        # If no listings OR count isn't increasing, stop paginating
        if not listings or len(all_listings) == previous_count:
            # print(f"✅ No more pages to load. Stopping at page {current_page}.")
            break

        current_page += 1  # Move to the next page

    # print(f"🚗 Total vehicles found: {len(all_listings)}")
    return all_listings

def extract_vins():
    vins = []
    listings = extract_listings()  # Assuming extract_listings() returns a list of vehicle data

    for listing in listings:
        vin = listing.get("vehicleidentificationnumber")  # Extract the VIN
        if vin:
            vins.append(vin)

    return vins  # Returns a list of VINs


def extract_listings():
    WebDriverManager.get_driver()
    soup = BeautifulSoup(driver.page_source, "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")

    listings = []

    for script in scripts:
        try:
            json_data = json.loads(script.string)

            # Print raw JSON for debugging
            # print("\n🔍 DEBUG: Extracted JSON-LD Data:\n", json.dumps(json_data, indent=2))

            # Check if 'vehicles' array exists (this is where the listings are)
            if isinstance(json_data, dict) and "vehicles" in json_data:
                listings.extend(json_data["vehicles"])
            elif isinstance(json_data, list):
                for item in json_data:
                    if "vehicles" in item:
                        listings.extend(item["vehicles"])

        except json.JSONDecodeError:
            continue

    return listings


# ✅ Scroll to load more results
SCROLL_PAUSE_TIME = 2
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME)

    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        # print("✅ No more pages to load.")
        break
    last_height = new_height

# ✅ Extract and Print Listings
all_listings = scrape_all_pages()
# print(f"🚗 Found {len(all_listings)} car listings from TrueCar!\n")

for car in all_listings:
    try:
        year = car.get("releaseDate", "Unknown Year")
        make = car.get("brand", {}).get("name", "Unknown Make")
        model = car.get("model", "Unknown Model")
        trim = car.get("trim", "Unknown Trim")
        price = car.get("offers", {}).get("price", "N/A")
        currency = car.get("offers", {}).get("priceCurrency", "USD")
        vin = car.get("vehicleidentificationnumber", "N/A")
        url = car.get("offers", {}).get("url", "N/A")
        image = car.get("image", "N/A")

        # print(f"{year} {make} {model} {trim} - {price} {currency}")
        # print(f"Dealer: {make}")
        # print(f"VIN: {vin}")
        # print(f"URL: {url}")
        # print(f"Image: {image}\n")

    except Exception as e:
        print(f"❌ Error processing car: {e}")

# vins = extract_vins()
# print(vins)
