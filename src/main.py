import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as exp_cond

import json
import argparse

from time import sleep
from helper_functions import get_cookie_button, click_button_by_class_name, fill_login_form, go_to_filter_page, \
    get_flat_ad_info_as_dict, create_hash

filterName = "Köln again"
nogo_words = ['burschenschaft', 'verbindung']


def find_no_go_ads(no_go_word_list, text, ad_key, link):
    no_go_regex = re.compile("(" + ")|(".join(no_go_word_list) + ")")
    no_go_result = no_go_regex.search(text.lower())
    if no_go_result:
        context = text[no_go_result.start() - 100: no_go_result.end() + 100]
        print("Filtered out text:\n" + context)
        no_go_file = "filtered_out_no_go_" + str(ad_key) + ".txt"
        with open(no_go_file, "w") as outfile:
            outfile.write(link + "\n" + context)
        return ad_key



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
    next_page_available = True
    while next_page_available:
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
        print([el for el in hash_list if el not in old_hash_list])
        updated_hash_json = json.dumps(updated_hash_list, indent=4)
        with open("hash_list.json", "w") as outfile:
            outfile.write(updated_hash_json)

        # only keep new ads
        for old_hash in old_hash_list:
            try:
                hashed_ad_dict.pop(old_hash)
            except KeyError:
                pass
        new_hashes = len(hashed_ad_dict)
        print("Length of new hashes:\t" + str(new_hashes))
        # if there are no new flat ads on this page, there won't be new ones on the next page so we can stop here
        if new_hashes == 0:
            break
        # if there are new flat ads, add them to the dictionary collecting new flats from all pages
        else:
            new_ads_dict.update(hashed_ad_dict)

        # Going to the next page
        try:
            next_page_button = driver.find_elements(By.CLASS_NAME, "next")
            next_page_button[0].click()
            print("\nGoing to the next page")
            next_page_available = True
        # if there is no next page we can end the loop
        except IndexError:
            next_page_available = False

    # iterate over message content
    print(str(len(new_ads_dict.keys())) + " new links to iterate over...")
    flats_to_remove = []  # delete later
    for key, flat_ad in new_ads_dict.items():
        driver.get(flat_ad['link'])
        flat_ad_text = WebDriverWait(driver, 10).until(
            exp_cond.visibility_of_element_located((By.ID, 'ad_description_text')))
        # new_ads_dict[key]['text'] = flat_ad_text.text
        print(flat_ad['link'])
        # filter out ads with no-go-words in ad-text
        no_go_key = find_no_go_ads(nogo_words, flat_ad_text.text, key, flat_ad['link'])
        assert no_go_key is None or key == no_go_key
        if no_go_key:
            flats_to_remove.append(key)

    # iterate over filtered out keys and remove the entries from dict
    for flat_key in flats_to_remove:
        new_ads_dict.pop(flat_key)

    # assemble message content
    betreff = str(len(new_ads_dict)) + " new flats for your filter"
    content = str(list(new_ads_dict.values()))
    if len(new_ads_dict) > 0:
        print(betreff)
        print(content)
        # save results for review
        content_json = json.dumps(new_ads_dict, indent=4)
        with open("flat_content.json", "w") as outfile:
            outfile.write(content_json)

    # Todo count pages and mention page in comment
    # Todo fix problem with German special characters when saving content to json
    # Todo add information on mandatory questions
    # Todo remove balcony filter and create self-made balcony OR garden-filter
    # Todo add proper logging

    # close window after sleep period for debugging
    time.sleep(140)
    driver.close()
    # send  message
    return new_ads_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-e", "--email", help="The email address of the user.", type=str, required=True)
    parser.add_argument("-p", "--password", help="The password of the user.", type=str, required=True)

    arguments_used = parser.parse_args()

    main(arguments_used)
