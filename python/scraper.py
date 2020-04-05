#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  5 09:16:52 2020

@author: markd

HOW TO USE
Requirements
- Google Chrome
- a chrome driver corresponding to your version of chrome (see https://sites.google.com/a/chromium.org/chromedriver/downloads)

Example:
python scraper.py --username <your linkedin username> --password <your linkedin password> --driver-path </path/to/chrome/driver> --login-url <https://linkedin.com/path/to/login/path?and&other&params>

--driver-path defaults to /usr/local/bin/chromedriver
--login-url defaults to the login page as of April 5, 2020
"""
import argparse

from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException


def parseArgs():
    parser = argparse.ArgumentParser(description='Use LinkedIn')
    parser.add_argument('--username', type=str,
                        help='LinkedIn Username')
    parser.add_argument('--password', type=str,
                        help='LinkedIn User password')
    parser.add_argument('--driver-path', type=str, default='/usr/local/bin/chromedriver',
                        help='Path to chromedriver')
    parser.add_argument('--login-url', type=str, default='https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin',
                        help='Path to URL page')
    
    args = parser.parse_args()
    return args.username, args.password, args.driver_path, args.login_url

class LinkedInScraper:
    def __init__(self, username, password, driverpath, login_url):
        self.username=username
        self.password=password
        self.login_url = login_url
        option = webdriver.ChromeOptions()
        option.add_argument(" — incognito")
        self.browser = webdriver.Chrome(executable_path=driverpath, chrome_options=option)
        self.browser.get(self.login_url)
        
    def login(self):
        username_input = self.browser.find_element_by_id("username")
        username_input.send_keys(username)
        
        password_input = self.browser.find_element_by_id("password")
        password_input.send_keys(password)
        
        #XPATH="/html/body/div/main/div/form/div[3]/button"//*[@id="app__container"]/main/div/form/div[3]/button
        #XPATH="/html/body/div/main/div/form/div[conatins(@class,'login__form_action_container')]/button"
        #div[contains(@class, 'Caption') and text()='Model saved']
        XPATH="/html/body/div/main/div/form/div[contains(@class, 'login__form_action_container')]/button"
        login_button = self.browser.find_element_by_xpath(XPATH)
        login_button.click()
    
    def searchLI(self, query):
        search_bar = self.browser.find_element_by_xpath("/html/body/header/div/form/div/div/div/div/div[1]/div/input")
        search_bar.send_keys(query)
    

if __name__ == '__main__':
    username, password, driverpath, url = parseArgs()
    LIS = LinkedInScraper(username, password, driverpath, url)
    LIS.login()
    #LIS.searchLI('Test')


