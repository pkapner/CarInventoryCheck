import requests
import json
import time
from bs4 import BeautifulSoup

from InventoryCheck import extract_vins  # Ensure this function is correctly implemented

API_KEY = "ss"
CX = "s"
SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


def search_dealer_by_vin(vin):
    params = {
        "q": f"{vin} -site:edmunds.com -site:capitalone.com",  # exclude these sites
        "key": API_KEY,
        "cx": CX,
        "num": 10  # Limit results to 5
    }

    try:
        response = requests.get(SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json().get("items", [])

        if not data:
            print(f"⚠️ No results found for VIN {vin}")
            return None

        inventory_keywords = ["edmunds", "new-vehicles", "used-vehicles"]

        for result in data:
            result_url = result.get("link", "")

            # If VIN is in the URL, it's a strong match
            if vin.lower() in result["link"].lower():
                return result  # Likely the correct dealer link

            # If the URL is a generic inventory page, skip
            if any(keyword in result_url for keyword in inventory_keywords):
                print(f"🔍 Skipping inventory page: {result_url}")
                continue

            # Check if the VIN appears on the actual webpage
            if check_vin_on_page(result_url, vin):
                return result

        print(f"⚠️ No direct VIN match found for VIN {vin}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Error for VIN {vin}: {e}")
        return None


def check_vin_on_page(url, vin):
    """Fetches the page content and checks if the VIN appears in the text."""
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

        response = session.get(url)
        # headers = {
        #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        # }
        # response = requests.get(url, headers=headers)

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text()

        if vin in page_text:
            print(f"✅ VIN {vin} found on page: {url}")
            return True
        else:
            print(f"⚠️ VIN {vin} NOT found on page: {url}")
            return False

    except requests.exceptions.RequestException:
        print(f"❌ Failed to fetch page: {url}")
        return False


def extract_dealer_info(vin, results):
    if not results:  # If no results, return None
        print(f"⚠️ No dealer data found for VIN {vin}, skipping.")
        return None

    for item in results:
        if not isinstance(item, dict):
            print(f"⚠️ Skipping invalid entry: {item}")
            continue

        # Check if VIN appears in the metadata description (if available)
        metatags = item.get("pagemap", {}).get("metatags", [{}])[0]
        description = metatags.get("og:description", "")

        # if vin not in description:
        #     # print(f"⚠️ Skipping entry: VIN {vin} not found in description")
        #     continue  # Skip this entry

        # Extract dealer info
        link = item.get("link", "")
        title = item.get("title", "Unknown Vehicle")
        dealer_name = item.get("displayLink", "Unknown Dealer")
        if "edmunds" in dealer_name:
            continue

        # Extract price (check multiple potential fields)
        price = None
        if "product:price:amount" in metatags:
            price = metatags["product:price:amount"]
        elif "twitter:data1" in metatags:
            price = metatags["twitter:data1"]
        elif "$" in description:
            try:
                price = description.split("$")[1].split()[0].replace(",", "")
            except (IndexError, ValueError):
                price = "Unknown"

        # Extract image URL
        image_url = metatags.get("og:image", "")

        # Ensure price is valid
        if not price or price == "Unknown":
            # print(f"⚠️ Warning: Invalid price format for VIN {vin}: {price}")
            price = "N/A"

        return {
            "VIN": vin,
            "Dealer Name": dealer_name,
            "Car Model": title,
            "Price": price,
            "Listing URL": link,
            "Image": image_url
        }

    return None  # If no valid entry is found


def process_vins(vin_list):
    dealer_info = {}

    for vin in vin_list:
        # print(f"🔍 Searching for dealer info on VIN: {vin}")
        search_results = search_dealer_by_vin(vin)

        if not search_results:
            print(f"⚠️ No search results for VIN {vin}, skipping.")
            continue

        dealer_data = extract_dealer_info(vin, search_results)

        if dealer_data:  # Only store valid results
            dealer_info[vin] = dealer_data
        else:
            print(f"⚠️ No valid dealer data found for {vin}")

        time.sleep(1)  # Prevent API rate limiting

    return dealer_info


def clean_and_sort_results(data):
    """Remove duplicates, filter out invalid entries, and sort results by price."""
    unique_results = {}

    for entry in data:
        # Ensure entry is a dictionary and not a header row
        if not isinstance(data, dict) or data.get(entry, "").get("VIN").strip() in ["VIN", ""]:
            print(f"⚠️ Skipping invalid or header entry: {entry}")
            continue

        vin = data[entry].get("VIN", "Unknown VIN")

        # Ensure valid VIN format (should be 17 characters long)
        if len(vin) != 17 or not vin.isalnum():
            print(f"⚠️ Skipping invalid VIN entry: {vin}")
            continue

        # Extract price, handling missing values
        price = data[entry].get("Price", "Unknown")
        if isinstance(price, (int, float)):
            valid_price = price
        elif isinstance(price, str) and price.replace(".", "").isdigit():
            valid_price = float(price)
        else:
            # print(f"⚠️ Warning: Invalid price format for {vin}: {price}")
            valid_price = float('inf')

        data[entry][price] = valid_price
        unique_results[vin] = data[entry]  # Use VIN as unique key

    # Sort by price (lowest to highest), placing 'Unknown' prices at the end
    sorted_results = sorted(unique_results.values(), key=lambda x: x["Price"])

    return sorted_results


# 🔰 MAIN EXECUTION
if __name__ == "__main__":
    # Extract VINs from TrueCar
    vin_list = extract_vins()

    # Search for dealer info
    raw_results = process_vins(vin_list)

    # Clean & sort results
    final_results = clean_and_sort_results(raw_results)

    # Output formatted results
    print("\n🔹 **Final Car Inventory Sorted by Price:** 🔹")
    for entry in final_results:
        print(json.dumps(entry, indent=4))
