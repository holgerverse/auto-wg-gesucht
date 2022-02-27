from time import sleep
from argparse import ArgumentParser, Namespace

from os.path import join
from os import remove
from selenium import webdriver

from src.helpers_page_handling import click_cookie_button, click_button_by_class_name, fill_login_form_and_click, \
    go_to_filter_page
from src.helpers_ad_handling import assemble_message_content, iterate_over_flat_content, collect_flat_info_all_pages
from time import sleep
from src.helpers_page_handling import get_cookie_button, click_button_by_class_name, fill_login_form, go_to_filter_page
from src.helpers_ad_handling import get_context_for_word_list, create_hash, get_flat_ad_info_as_dict

page_url = "https://www.wg-gesucht.de/"
filterName = "Köln again"
blackList = ['burschenschaft', 'verbindung']
highlightWords = ['garten', 'van']
geckodriver_path = r'C:\Programme\geckodriver\geckodriver.exe'


def main(arguments: Namespace):
    # Create a new instance of the Firefox driver and open 'https://www.wg-gesucht.de/'.
    driver = webdriver.Firefox(executable_path=geckodriver_path)
    driver.get(page_url)

    # Click cookie and login button, fill in login form and go to desired filter
    click_cookie_button(driver)
    fill_login_form_and_click(driver, arguments.email, arguments.password)
    go_to_filter_page(driver, filterName)

    # Iterate over pages until there are no further pages or there are no new ads
    new_ads_dict = collect_flat_info_all_pages(driver, ['title', 'contract'])
    # DELETE LATER: remove hashes to have enough ads for working on the code
    remove(join("..", "outputs", "hash_list.json"))

    # Iterate over remaining flats, filter out and save highlights
    new_ads_dict = iterate_over_flat_content(driver, new_ads_dict, blackList, highlightWords)

    # Assemble message content and save it
    assemble_message_content(new_ads_dict, 'outputs', 'flat_content')

    # Todo: create more functions for shorter main function
    # Todo: REFACTOR (Add function descriptions, add data input and output type)
    # Todo: fix problem with German special characters when saving content to json
    # Todo: save last words of each text for later manual search of patterns to automate
    # Todo: add information on mandatory questions
    # Todo: remove balcony filter and create self-made balcony OR garden-filter (or combine several filters)
    # Todo: add proper logging
    # Todo: add time of ad to logging for later statistical analysis

    # close window after sleep period for debugging
    sleep(140)
    driver.close()
    # send  message
    return new_ads_dict


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("-e", "--email", help="The email address of the user.", type=str, required=True)
    parser.add_argument("-p", "--password", help="The password of the user.", type=str, required=True)

    arguments_used = parser.parse_args()

    main(arguments_used)
