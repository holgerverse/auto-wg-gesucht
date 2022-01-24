import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as exp_cond

import json
import argparse

from time import sleep
from src.helpers_page_handling import get_cookie_button, click_button_by_class_name, fill_login_form, go_to_filter_page
from src.helpers_ad_handling import get_context_for_word_list, create_hash, get_flat_ad_info_as_dict

filterName = "Köln again"
blackList = ['burschenschaft', 'verbindung']
highlightWords = ['garten', 'van']


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
    go_to_filter_page(driver, filterName)

    # Iterate over pages until there are no further pages or there are no new ads
    new_ads_dict = dict()
    on_page = 1
    while on_page:
        print("On flat ad page " + str(on_page) + " -----------------------------------------")
        # get all flat ad-elements
        ad_dict = get_flat_ad_info_as_dict(driver)

        # read existing hashes
        try:
            with open(os.path.join("..", "outputs", 'hash_list.json'), 'r') as openfile:
                old_hash_list = json.load(openfile)
        except FileNotFoundError:
            "No file called hash_list.json"
            old_hash_list = []
        print("Number of old hashes:\t" + str(len(old_hash_list)))

        # create hashes and write to hash-list if not existent
        hashed_ad_dict = dict()
        for key, value in ad_dict.items():
            hash_created = create_hash(value['title'] + value['contact'])
            hashed_ad_dict[hash_created] = value
        hash_list = list(hashed_ad_dict.keys())
        print("Number of collected hashes:\t" + str(len(hash_list)))
        updated_hash_list = list(set(hash_list + old_hash_list))
        print("Number of new and old hashes combined:\t" + str(len(updated_hash_list)))
        updated_hash_json = json.dumps(updated_hash_list, indent=4)
        with open(os.path.join("..", "outputs", "hash_list.json"), "w") as outfile:
            outfile.write(updated_hash_json)

        # Remove known ads
        for old_hash in old_hash_list:
            try:
                hashed_ad_dict.pop(old_hash)
            except KeyError:
                pass
        new_hashes = len(hashed_ad_dict)
        print("Number of new hashes:\t" + str(new_hashes))
        # if there are no new flat ads on this page, there won't be new ones on the next page so we can stop here
        if new_hashes == 0:
            break
        else:  # if there are new flat ads, add them to the dictionary collecting new flats from all pages
            new_ads_dict.update(hashed_ad_dict)

        # Going to the next page
        try:
            next_page_button = driver.find_elements(By.CLASS_NAME, "next")
            next_page_button[0].click()
            on_page += 1
            print("Going to the next page (" + str(on_page) + ").\n")
        except IndexError:  # if there is no next page we can end the loop
            print("No next page.\n")
            break
    # DELETE LATER: remove hashes to have enough ads for working on the code
    os.remove(os.path.join("..", "outputs", "hash_list.json"))

    # iterate over message content
    print(str(len(new_ads_dict.keys())) + " new links to iterate over...")
    flats_to_remove = []
    for key, flat_ad in new_ads_dict.items():
        driver.get(flat_ad['link'])
        flat_ad_text = WebDriverWait(driver, 10).until(
            exp_cond.visibility_of_element_located((By.ID, 'ad_description_text')))
        # new_ads_dict[key]['text'] = flat_ad_text.text
        print(flat_ad['link'])
        # filter out ads with no-go-words in ad-text
        no_go_context = get_context_for_word_list(blackList, flat_ad_text.text, key, flat_ad['link'], "blacklist_case_")
        if no_go_context:
            flats_to_remove.append(key)
        # check for highlight words
        highlight_context = get_context_for_word_list(highlightWords, flat_ad_text.text, key, flat_ad['link'],
                                                      "marked_highlight_")
        if highlight_context:
            # highlights.update({key: highlight_context})
            new_ads_dict[key]['highlight'] = highlight_context

    # iterate over filtered out keys and remove the entries from dict
    for flat_key in flats_to_remove:
        new_ads_dict.pop(flat_key)

    # assemble message content
    betreff = str(len(new_ads_dict)) + " new flats for your filter"
    if len(new_ads_dict) > 0:
        print(betreff)
        # save results for review
        content_json = json.dumps(new_ads_dict, indent=4)
        with open(os.path.join("..", "outputs", "flat_content.json"), "w") as outfile:
            outfile.write(content_json)

    # Todo add information on mandatory questions
    # Todo remove balcony filter and create self-made balcony OR garden-filter
    # Todo add proper logging
    # Todo add time of ad to logging for later statistical analysis
    # Todo fix problem with German special characters when saving content to json
    # Todo REFACTOR (Add function descriptions, add data input and output type)

    # close window after sleep period for debugging
    sleep(140)
    driver.close()
    # send  message
    return new_ads_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-e", "--email", help="The email address of the user.", type=str, required=True)
    parser.add_argument("-p", "--password", help="The password of the user.", type=str, required=True)

    arguments_used = parser.parse_args()

    main(arguments_used)
