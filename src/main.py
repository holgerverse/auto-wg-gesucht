from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException

from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as exp_cond

from re import compile
import json
import argparse

import time

filterName = "Köln again"


def create_hash(text: str):
    """ create hash function that generates equal hash for equal strings across multiple sessions as this is not the
    case for the python hash function """
    self_made_hash = 0
    for ch in text:
        self_made_hash = (self_made_hash*281 ^ ord(ch)*997) & 0xFFFFFFFF
    return self_made_hash


def get_cookie_button(driver: webdriver.Firefox):
    """
    Returns the cookie button element.

    Inputs:
    Outputs:
    """
    class_objects = driver.find_elements(By.CLASS_NAME, "cmpboxbtnyes")  # "cmpboxbtn cmpboxbtnyes")
    pattern = compile("Akzeptieren")
    for key, value in enumerate(class_objects):
        if pattern.match(class_objects[key].text):
            return class_objects[key]


def get_button_by_xpath(driver, xpath):
    xpath_object = driver.find_elements(By.XPATH, xpath)
    return xpath_object[0]


def click_button_by_class_name(driver: webdriver.Firefox, class_name: str, regex: str = None, click=True):
    """
    Returns the login button element.

    Inputs:
        driver: Requires a webdriver sessions running Firefox.
    Outputs:
        Returns the login button element.
    """
    # Get all objects that are part of the class 'wgg_tertiary'. The Login button is part of this class.
    class_objects = driver.find_elements(By.CLASS_NAME, class_name)
    # Iterate over all objects inside the 'wgg_tertiary' class. Return the object which has the 'Login' inside the text
    # attribute.
    if regex:
        pattern = compile(regex)
        for key, value in enumerate(class_objects):
            if pattern.match(class_objects[key].text):
                right_key = key
                break
    else:
        right_key = 0
    if click:
        class_objects[right_key].click()
        return
    else:
        return class_objects[right_key]


def fill_login_form(driver: webdriver.Firefox, email: str, password: str) -> bool:
    """
    Fills the login form.

    Inputs:
        driver:   Requires a webdriver sessions running Firefox.
        email:    The email address of the user.
        password: The password of the user.
    Outputs:
        Returns True if the form was filled successfully.
    """

    # Fill in the email filed with the given email.
    try:
        email_field = WebDriverWait(driver, 10).until(
            exp_cond.element_to_be_clickable((By.XPATH, '//*[@id="login_email_username"]')))
        email_field.send_keys(email)
    except ElementNotInteractableException:
        raise Exception("Could not find email field.")

    # Fill in the password field with the given password.
    try:
        password_field = WebDriverWait(driver, 10).until(
            exp_cond.element_to_be_clickable((By.XPATH, '//*[@id="login_password"]')))
        password_field.send_keys(password)
    except ElementNotInteractableException:
        raise Exception("Could not find password field.")

    return True


def go_to_filter_page(driver):
    filter_page_reached = False
    while not filter_page_reached:
        mein_wggesucht_url = "https://www.wg-gesucht.de/mein-wg-gesucht-filter.html"
        driver.get(mein_wggesucht_url)

        # get filter div box
        time.sleep(3)
        try:
            div_box = driver.find_elements(By.LINK_TEXT, filterName)
            div_box[0].click()
            filter_page_reached = True
            print("Reached filter page.")
        except IndexError:
            login_button = driver.find_elements((By.LINK_TEXT, "Login"))
            print("Type login button:" + str(type(login_button)))
            print(login_button)
            login_button[0].click()
            continue


def get_flat_ad_info_as_dict(driver):
    ad_boxes_list = WebDriverWait(driver, 20).until(
        exp_cond.visibility_of_all_elements_located((By.CLASS_NAME, 'card_body')))
    print("Number of ads on page:\t" + str(len(ad_boxes_list)))
    ad_dict = {}
    for key, value in enumerate(ad_boxes_list):
        title = value.find_elements(By.TAG_NAME, "h3")
        sub_title = click_button_by_class_name(driver, "col-xs-11", None, False).text
        people_count = int(sub_title.split('er WG')[0]) - 1
        street = sub_title.split('| ')[2]
        link = title[0].find_elements(By.LINK_TEXT, title[0].text)[0].get_attribute('href')
        online_list = value.find_elements(By.CLASS_NAME, "flex_space_between")
        for sub_key, sub_value in enumerate(online_list):
            if "Online:" in online_list[sub_key].text:
                online = online_list[sub_key].text
                contact = online.split('Online:')[0].replace("\n", "")
                online = online.split('Online:')[1]
                ad_dict[key] = {
                    'title': title[0].text,
                    'link': link,
                    'online': online,
                    'contact': contact,
                    'people_count': people_count,
                    'street': street
                }
    return ad_dict


def main(arguments: argparse.Namespace):
    # Create a new instance of the Firefox driver and open 'https://www.wg-gesucht.de/'.
    driver = webdriver.Firefox(executable_path=r'C:\Programme\geckodriver\geckodriver.exe')
    driver.get("https://www.wg-gesucht.de/")

    # Click the cookie button
    try:
        cookie_button = get_cookie_button(driver)
        cookie_button.click()
    except AttributeError:
        print('No cookie popup.\n')

    # Click the login button.
    click_button_by_class_name(driver, "wgg_tertiary", "LOGIN")

    # Fill in the login form.
    fill_login_form(driver, arguments.email, arguments.password)
    login_button = driver.find_elements(By.ID, "login_submit")
    login_button[0].click()
    print("Login form filled.\n")

    # Go to existing filter
    go_to_filter_page(driver)

    # get all flat ad-elements
    ad_dict = get_flat_ad_info_as_dict(driver)

    # read existing hashes
    try:
        with open('hash_list.json', 'r') as openfile:
            old_hash_list = json.load(openfile)
    except FileNotFoundError:
        "No file called hash_list.json"
        old_hash_list = []
    print("Length of old hashes:\t" + str(len(old_hash_list)))

    # create hashes and write to hash-list if not existent
    hashed_ad_dict = dict()
    for key, value in ad_dict.items():
        hash_created = create_hash(value['title'] + value['contact'])
        hashed_ad_dict[hash_created] = value
    hash_list = list(hashed_ad_dict.keys())
    print("Length of collected hashes:\t" + str(len(hash_list)))
    updated_hash_list = list(set(hash_list + old_hash_list))
    print("Length of new and old hashes combined:\t" + str(len(updated_hash_list)))
    print(sorted(hash_list))
    print(sorted(old_hash_list))
    hash_json = json.dumps(updated_hash_list, indent=4)
    with open("hash_list.json", "w") as outfile:
        outfile.write(hash_json)

    # only keep new ads
    for old_hash in old_hash_list:
        try:
            hashed_ad_dict.pop(old_hash)
        except KeyError:
            pass
    print("Length of new hashes:\t" + str(len(hashed_ad_dict)))
    # assemble message content
    betreff = str(len(hashed_ad_dict)) + " new flats for your filter"
    content = str(list(hashed_ad_dict.values()))
    print(betreff)
    print(content)

    # save results for review
    content_json = json.dumps(content, indent=4)
    with open("flat_content.json", "w") as outfile:
        outfile.write(content_json)

    # Going to the next page
    click_button_by_class_name(driver, "next")
    # next_button = driver.find_elements(By.CLASS_NAME, "next")
    print("\nGoing to the next page")
    # next_button[0].click()

    # Todo fix hash comparison as it is not working
    # Todo add information on mandatory questions
    # Todo remove balcony filter and create self-made balcony OR garden-filter
    # Todo add list of no-go-words

    # send  message

    return ad_dict
    # time.sleep(140)
    # driver.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-e", "--email", help="The email address of the user.", type=str, required=True)
    parser.add_argument("-p", "--password", help="The password of the user.", type=str, required=True)

    arguments_used = parser.parse_args()

    main(arguments_used)
