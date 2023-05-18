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


def main():
    # Load the cookies pkl file and store them in a session object
    session = get_cookies(validate=True)


    # Store the cookies in a pickle file
    storeCookies(session)


if __name__ == "__main__":
    main()