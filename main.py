import requests
import pickle
import os
from bs4 import BeautifulSoup
import pandas as pd

# User defined parameters

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
def getLagerStand(session, productID):
    print("Getting the Lagerstand")
    base_url = "https://erp.digitecgalaxus.ch"
    find_product_url = base_url + "/de/Product/Availability/"

    r = session.get(find_product_url + productID)
    soup = BeautifulSoup(r.text, 'html.parser')

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


def main():
    # Load the cookies pkl file and store them in a session object
    session = get_cookies(validate=True)

    # Get the Lagerstand
    session, lagerstand = getLagerStand(session, "23253714")

    print(lagerstand)

    # Store the cookies in a pickle file
    storeCookies(session)


if __name__ == "__main__":
    main()