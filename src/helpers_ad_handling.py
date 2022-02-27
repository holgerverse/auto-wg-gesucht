import re
import os
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as exp_cond
from selenium.webdriver.common.by import By

from src.helpers_general import try_read_json_file, save_file_to_json
from src.helpers_page_handling import go_to_next_flat_ad_page

def create_hash(text: str):
    """ create hash function that generates equal hash for equal strings across multiple sessions as this is not the
    case for the python hash function """
    self_made_hash = 0
    for ch in text:
        self_made_hash = (self_made_hash*281 ^ ord(ch)*997) & 0xFFFFFFFF
    return self_made_hash


def get_flat_ad_boxes(driver):
    sleep(15)
    ad_boxes_list = WebDriverWait(driver, 20).until(
        exp_cond.visibility_of_all_elements_located((By.CLASS_NAME, 'card_body')))
    print("Number of ads on page:\t" + str(len(ad_boxes_list)))
    return ad_boxes_list


def check_if_real_flat(box_element):
    res = box_element.find_elements_by_class_name("partners")
    return len(res) == 0


def get_relevant_info_from_ad_box(ad_box):
    # sub-title info
    sub_title = ad_box.find_elements_by_class_name("col-xs-11")
    street = sub_title[0].text.split('| ')[2]
    people_count = int(sub_title[0].text.split('er WG')[0]) - 1
    # title info
    title = ad_box.find_elements_by_tag_name("h3")
    # link info
    link = title[0].find_elements_by_link_text(title[0].text)[0].get_attribute('href')
    # time of upload info
    online_list = ad_box.find_elements_by_class_name("flex_space_between")

    online_list_text_values = [el.text for el in online_list if 'Online: ' in el.text]

    for el_text in online_list_text_values:
        contact = el_text.split('Online:')[0].replace("\n", "")
        online_since = el_text.split('Online:')[1]
    return {
        'title': title[0].text, 'link': link, 'online': online_since, 'contact': contact, 'people_count': people_count,
        'street': street
    }


def get_flat_ad_info_as_dict(driver):
    ad_boxes_list = get_flat_ad_boxes(driver)
    ad_dict = {}
    for key, value in enumerate(ad_boxes_list):
        real_ad = check_if_real_flat(value)
        if real_ad:
            ad_dict[key] = get_relevant_info_from_ad_box(value)
    return ad_dict


def collect_flat_info_on_page(driver, hash_columns):
    """ Get info for flats on current page and return them as dict with an added hash """
    ad_dict = get_flat_ad_info_as_dict(driver)
    hashed_ad_dict = dict()
    for key, value in ad_dict.items():
        hash_created = create_hash(value[hash_columns[0]] + value[hash_columns[1]])  # bad code
        hashed_ad_dict[hash_created] = value
    return hashed_ad_dict


def get_context_for_word_list(highlight_list, text, ad_key, link, prefix):
    regex = re.compile(r"((\s|^)" + r"(\s|$))|((\s|^)".join(highlight_list) + r"(\s|$))")
    result = regex.search(text.lower())
    if result:
        context = text[result.start() - 100: result.end() + 100]
        print("Identified context (" + prefix + "):\n" + context + "\n")
        highlight_file = prefix + str(ad_key) + ".txt"
        other_matches = regex.findall(text.lower())
        with open(os.path.join("..", "outputs", highlight_file), "w") as outfile:
            outfile.write(link + "\n" + str(other_matches) + "\n" + context)
        return context


def update_hash_list(hash_list_folder, hash_list_name, hashed_flat_dict):
    old_hash_list = try_read_json_file(hash_list_name, os.path.join('..', hash_list_folder), [])
    print("Number of old hashes:\t" + str(len(old_hash_list)))
    hash_list = list(hashed_flat_dict.keys())
    print("Number of collected hashes:\t" + str(len(hash_list)))
    updated_hash_list = list(set(hash_list + old_hash_list))
    print("Number of new and old hashes combined:\t" + str(len(updated_hash_list)))
    save_file_to_json(updated_hash_list, "hash_list", os.path.join("..", "outputs"))
    return updated_hash_list


def assemble_message_content(new_flat_dict, file_folder, file_name):
    betreff = str(len(new_flat_dict)) + " new flats for your filter"
    if len(new_flat_dict) > 0:
        print(betreff)
        # save results for review
        save_file_to_json(new_flat_dict, file_name, os.path.join("..", file_folder))


def iterate_over_flat_content(driver, flat_dict, black_list, highlight_words):
    print(str(len(flat_dict.keys())) + " new links to iterate over...")
    flats_to_remove = []
    for key, flat_ad in flat_dict.items():
        driver.get(flat_ad['link'])
        flat_ad_text = WebDriverWait(driver, 10).until(
            exp_cond.visibility_of_element_located((By.ID, 'ad_description_text')))
        # last_300_letters = flat_ad_text.text[-300:]
        print(flat_ad['link'])

        # Filter out ads with no-go-words in ad-text
        no_go_context = get_context_for_word_list(
            black_list, flat_ad_text.text, key, flat_ad['link'], "blacklist_case_")
        if no_go_context:
            flats_to_remove.append(key)

        # Check for highlight words
        highlight_context = get_context_for_word_list(highlight_words, flat_ad_text.text, key, flat_ad['link'],
                                                      "marked_highlight_")
        if highlight_context:
            flat_dict[key]['highlight'] = highlight_context
    # Iterate over filtered out keys and remove the entries from dict
    for flat_key in flats_to_remove:
        flat_dict.pop(flat_key)
    return flat_dict


def collect_flat_info_all_pages(driver, hash_columns):
    new_ads_dict = dict()
    page_number = 1
    while page_number:
        print("On flat ad page " + str(page_number) + " -----------------------------------------")

        # Get info for all flats, update hash list and only keep new flats
        hashed_ad_dict = collect_flat_info_on_page(driver, hash_columns=hash_columns)
        updated_hash_list = update_hash_list('outputs', 'hash_list', hashed_ad_dict)
        new_flats_dict = {new_key: hashed_ad_dict[new_key] for new_key in updated_hash_list}
        print("Number of new hashes:\t" + str(len(new_flats_dict)))

        # End loop if there are no new flat ads on this page
        if len(new_flats_dict) == 0:
            break
        else:  # if there are new flat ads, add them to the dictionary collecting new flats from all pages
            new_ads_dict.update(new_flats_dict)

        # Going to the next page
        page_number = go_to_next_flat_ad_page(driver, page_number)
        if not page_number:
            break
    return new_ads_dict
