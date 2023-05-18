import requests
import pickle
import os
from bs4 import BeautifulSoup
import pandas as pd

# User defined parameters

# Functions
def get_cookies(cookiesFilePath = "data/cookies.pkl", validate = True):
    print("Loading the cookies...")

    # Create an empty session
    session = requests.Session()

    # Get the cookies 
    if os.path.exists(cookiesFilePath):
        with open(cookiesFilePath, 'rb') as file:
            cookies = pickle.load(file) # Could not figure out how to authenticate with the ERP (especially because of 2FA), so I just copy the cookies from my browser and keep track of the Auth2.0 behaviour. Defeneteley something to change in the future.
    else:
        print("No cookies found in path: " + cookiesFilePath)

    # Store the cookies in the session
    try:
        session.cookies.update(cookies)
    except Exception as e:
        print("An unknown error occured. Please try again. The cookies are probably not in the right format.")
        print(e)
        return None

    # Check if the cookies are valid
    if validate:
        response = session.get("https://erp.digitecgalaxus.ch/de/Welcome")
        if response.url.startswith("https://erp.digitecgalaxus.ch/de/Login"): # If im redirected to the login page, the cookies are not valid
            print("Cookies are not valid. Please run the cookiesGrab.py.")
            return None

    return session

def storeCookies(session, cookiesFilePath = "data/cookies.pkl"):
    print("Storing the cookies...")

    # make sure the data folder exists
    if not os.path.exists('data'):
        os.makedirs('data')

    with open(cookiesFilePath, 'wb') as file:
        pickle.dump(session.cookies, file)

# Function to change the key name of a dictionary. Python should have a built in function for this
def change_key_name(dictionary, old_key, new_key):
    if old_key in dictionary:
        value = dictionary.pop(old_key)
        dictionary[new_key] = value
    return dictionary

# Takes in a session and a productID and raeturns the Lagerstand in a dictionary with the city as the key being the filiale and the value being how many available products there are in that filiale
def getLagerStand(session, soup, productID):
    print("Getting the Lagerstand")

    # Find the table
    table = soup.select_one("#ProductProductWarehouseCompartment2 > div.content.erpBoxContent > div > div > div > table")

    # Parse the table
    tr_elements = table.find_all("tr")[1:]
    td_elements = [tr_element.find_all("td")[1:] for tr_element in tr_elements]
    td_elements = [[td_element.text.strip() for td_element in td_element] for td_element in td_elements]

    lagerstand = {}

    for td_element in td_elements:
        if td_element[0] == "verfügbar":
            if td_element[1] not in lagerstand:
                lagerstand[td_element[1]] = int(td_element[2])
            else:
                lagerstand[td_element[1]] += int(td_element[2])

    if "StGallen" in lagerstand:
        lagerstand = change_key_name(lagerstand, "StGallen", "St. Gallen")
    if "Zurich" in lagerstand:
        lagerstand = change_key_name(lagerstand, "Zurich", "Zürich")

    return session, lagerstand

# takes in a session and productID and deleates all the zielbestand rules of said product
def deleateZielbestand(session, soup, productID):
    print("Deleating the current Zielbestand")

    # Find out how many rules there are
    rule_table = soup.select_one("#ProductSiteTargetInventoryOverrideTable4 > form > table")

    # Parse the table
    tbody_elements = rule_table.find_all("tbody")[0]
    tr_elements = tbody_elements.find_all("tr")
    hrefs = [tr_element.find_all("a")[0]["href"] for tr_element in tr_elements]

    currentURL = "https://erp.digitecgalaxus.ch/de/Product/Availability/" + productID

    # Traverse the hrefs and deleate the rules
    for href in hrefs:
        deleate_url = "https://erp.digitecgalaxus.ch" + href

        params = {
            'ajaxerplist': '2'
        }

        data = {
            'crud': 'delete'
        }

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,de-CH;q=0.8,de;q=0.7',
            'Content-Length': '11',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://erp.digitecgalaxus.ch',
            'Referer': currentURL,
            'Sec-Ch-Ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }

        r = session.post(deleate_url, params=params, data=data, headers=headers)

        print(r)

    return session

# Takes in a session, productID and information about the new Zielbestand and adds it to the product for every filiale in the filialen list
def addZielbestand(session, soup, productID, from_date, to_date, product_quantity, filialen = ["Basel", "Bern", "Dietikon", "Genf", "Kriens", "Lausanne", "St. Gallen", "Winterthur", "Zürich"]):
    print("Adding the new Zielbestand")

    # Values encoded
    values_encoded ={
        'Basel': 246967,
        'Bern': 246970,
        'Dietikon': 246971,
        'Genf': 246975,
        'Kriens': 246968,
        'Lausanne': 246965,
        'St. Gallen': 246974,
        'Winterthur': 246969,
        'Wohlen': 246977,
        'Zürich': 246938
    }

    # Find out the product mandant, necessary for the request
    mandant = soup.select_one("#ProductBox1 > div.content.erpBoxContent > div:nth-child(3) > div:nth-child(8) > div:nth-child(2)").text.strip()

    # The url on which the post request is made
    create_url = "https://erp.digitecgalaxus.ch/ProductSiteTargetInventoryOverride/TableNew/" + mandant
    currentURL = "https://erp.digitecgalaxus.ch/de/Product/Availability/" + productID

    for filiale in filialen:

        params = {
                'ajaxerplist': '2'
        }

        data = {
            "ProductSiteTargetInventoryOverride.SiteId": values_encoded[filiale],
            "ProductSiteTargetInventoryOverride.Quantity": product_quantity,
            "ProductSiteTargetInventoryOverride.ValidFrom": from_date,
            "ProductSiteTargetInventoryOverride.ValidTo" : to_date,
            "save" : "",
        }

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": currentURL,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }

        r = session.post(create_url, params=params, data=data, headers=headers)

        print(r)

    return session

def getProductAvailabilityPage(session, productID):
    find_product_url = "https://erp.digitecgalaxus.ch/de/Product/Availability/"

    r = session.get(find_product_url + productID)
    soup = BeautifulSoup(r.text, 'html.parser')

    return session, soup


def main():
    # Load the cookies pkl file and store them in a session object
    session = get_cookies(validate=True)

    product = "21881888"
    date_start = "16.05.2023"
    date_end = "09.05.2024"
    quantity = 1

    # Get the product availability page
    session, soup = getProductAvailabilityPage(session, product)

    # Get the Lagerstand
    session, lagerstand = getLagerStand(session, soup, product)

    # Deleate the current Zielbestand
    session = deleateZielbestand(session, soup, product)

    # Add the new Zielbestand
    session = addZielbestand(session, soup, product, date_start, date_end, quantity)

    # Store the cookies in a pickle file
    storeCookies(session)


if __name__ == "__main__":
    main()