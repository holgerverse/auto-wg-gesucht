from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as exp_cond
from selenium.webdriver.common.by import By
from selenium.webdriver import Firefox
from re import compile
from time import sleep


def create_hash(text: str):
    """ create hash function that generates equal hash for equal strings across multiple sessions as this is not the
    case for the python hash function """
    self_made_hash = 0
    for ch in text:
        self_made_hash = (self_made_hash*281 ^ ord(ch)*997) & 0xFFFFFFFF
    return self_made_hash


def get_cookie_button(driver: Firefox):
    """
    Returns the cookie button element.

    Inputs:
    Outputs:
    """
    class_objects = driver.find_elements_by_class_name("cmpboxbtnyes")
    pattern = compile("Akzeptieren")
    for key, value in enumerate(class_objects):
        if pattern.match(class_objects[key].text):
            return class_objects[key]


def get_button_by_xpath(driver, xpath):
    xpath_object = driver.find_elements_by_path(xpath)
    return xpath_object[0]


def click_button_by_class_name(driver: Firefox, class_name: str, regex: str = None, click=True):
    """
    Returns the login button element.

    Inputs:
        driver: Requires a webdriver sessions running Firefox.
    Outputs:
        Returns the login button element.
    """
    # Get all objects that are part of the class 'wgg_tertiary'. The Login button is part of this class.
    class_objects = driver.find_elements_by_class_name(class_name)
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


def fill_login_form(driver: Firefox, email: str, password: str) -> bool:
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


def go_to_filter_page(driver, filter_name):
    filter_page_reached = False
    while not filter_page_reached:
        mein_wg_gesucht_url = "https://www.wg-gesucht.de/mein-wg-gesucht-filter.html"
        driver.get(mein_wg_gesucht_url)

        # get filter div box
        sleep(3)
        try:
            div_box = driver.find_elements_by_link_text(filter_name)
            div_box[0].click()
            filter_page_reached = True
            print("Reached filter page.")
        except IndexError:
            login_button = WebDriverWait(driver, 10).until(exp_cond.element_to_be_clickable((By.TAG_NAME, 'button')))
            print("Type login button:" + str(type(login_button)))
            print(login_button)
            login_button[0].click()
            continue


def get_flat_ad_info_as_dict(driver):
    sleep(15)
    ad_boxes_list = WebDriverWait(driver, 20).until(
        exp_cond.visibility_of_all_elements_located((By.CLASS_NAME, 'card_body')))
    print("Number of ads on page:\t" + str(len(ad_boxes_list)))
    ad_dict = {}
    for key, value in enumerate(ad_boxes_list):
        sub_title = value.find_elements_by_class_name("col-xs-11")
        title = value.find_elements_by_tag_name("h3")
        link = title[0].find_elements_by_link_text(title[0].text)[0].get_attribute('href')
        online_list = value.find_elements_by_class_name("flex_space_between")
        oll_text_values = [el.text for el in online_list]
        for el_text in oll_text_values:
            if "Online:" in el_text:
                people_count = int(sub_title[0].text.split('er WG')[0]) - 1
                street = sub_title[0].text.split('| ')[2]
                contact = el_text.split('Online:')[0].replace("\n", "")
                online_since = el_text.split('Online:')[1]
                ad_dict[key] = {
                    'title': title[0].text,
                    'link': link,
                    'online': online_since,
                    'contact': contact,
                    'people_count': people_count,
                    'street': street
                }
    return ad_dict
