import re
import os
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as exp_cond
from selenium.webdriver.common.by import By


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
    online_list_text_values = [el.text for el in online_list if 'Online' in el.text]
    for el_text in online_list_text_values:
        contact = el_text.split('Online:')[0].replace("\n", "")
        online_since = el_text.split('Online:')[1]
    return {
        'title': title[0].text,
        'link': link,
        'online': online_since,
        'contact': contact,
        'people_count': people_count,
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


def get_context_for_word_list(highlight_list, text, ad_key, link, prefix):
    regex = re.compile("((\s|^)" + "(\s|$))|((\s|^)".join(highlight_list) + "(\s|$))")
    result = regex.search(text.lower())
    if result:
        context = text[result.start() - 100: result.end() + 100]
        print("Identified context (" + prefix + "):\n" + context + "\n")
        highlight_file = prefix + str(ad_key) + ".txt"
        other_matches = regex.findall(text.lower())
        with open(os.path.join("..", "outputs", highlight_file), "w") as outfile:
            outfile.write(link + "\n" + str(other_matches) + "\n" + context)
        return context
