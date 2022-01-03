from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import ElementNotInteractableException

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from re import compile
from re import match

import argparse

import time

def get_login_button(driver: webdriver.Firefox) -> webdriver.remote.webelement.WebElement:
    '''
    Returns the login button element.
    
    Inputs: 
        driver: Requires a webdriver sessions running Firefox.
    Outputs: 
        Returns the login button element.
    '''

    # Get all objects that are part of the class 'wgg_tertiary'. The Login button is part of this class.
    class_objects = driver.find_elements(By.CLASS_NAME, "wgg_tertiary")
    
    #Iterate over all objects inside the 'wgg_tertiary' class. Return the object which has the 'Login' inside the text attribute.
    pattern = compile("LOGIN")
    for key, value in enumerate(class_objects):
        if pattern.match(class_objects[key].text):
            return class_objects[key]

def fill_login_form(driver: webdriver.Firefox, email: str, password: str):
    '''
    Fills the login form.
    
    Inputs: 
        driver:   Requires a webdriver sessions running Firefox.
        email:    The email address of the user.
        password: The password of the user.
    Outputs:s
    '''
    
    # Fill in the email filed with the given email.
    try:
        email_field = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="login_email_username"]')))
        email_field.send_keys(eMail)                 
    except ElementNotInteractableException:
        raise Exception("Could not find email field.")
    
    # Fill in the password field with the given password.
    try:
        password_field = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="login_password"]')))
        password_field.send_keys(password)
    except ElementNotInteractableException:
        raise Exception("Could not find password field.")

def main(arguments: argparse.Namespace):
      
    # Create a new instance of the Firefox driver and open 'https://www.wg-gesucht.de/'.
    driver = webdriver.Firefox()
    driver.get("https://www.wg-gesucht.de/")
    
    # TODO: Write funciton that handles cookie consent.

    # Click the login button.
    login_button = get_login_button(driver)
    login_button.click()

    # Fill in the login form.
    fill_login_form(driver, arguments.email, arguments.password)
    
    # TODO continue
    
    time.sleep(10)
    
    driver.close()
    
if __name__ == "__main__":
        
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-e", "--email", help="The email address of the user.", type=str)
    parser.add_argument("-p", "--password", help="The password of the user.", type=str)
    
    arguments = parser.parse_args()
    
    main(arguments)