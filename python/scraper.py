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

To Do:
- Add comments!
- scrape info from page
- kafka producer
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
        
    def loginToLinkedIn(self):
        username_input = self.browser.find_element_by_id("username")
        username_input.send_keys(username)
        
        password_input = self.browser.find_element_by_id("password")
        password_input.send_keys(password)
        
        XPATH="/html/body/div/main/div/form/div[contains(@class, 'login__form_action_container')]/button"
        login_button = self.browser.find_element_by_xpath(XPATH)
        login_button.click()
    
    def searchForRelevantLIProfiles(self, query, page_limit=3):
        count = 0           # for keeping track of pagination
        users_links = []    # initialize empty list for urls to user pages
        
        self.browser.get("https://google.com")
        
        # enter query into Google search bar, limiting to linkedin.com/in/ sites
        search_bar = self.browser.find_element_by_name('q')
        query = "site:linkedin.com/in/ AND " + query
        search_bar.send_keys(query)
        # submit query
        search_button = self.browser.find_element_by_xpath("/html/body/div/div[4]/form/div[2]/div[1]/div[3]/center/input[1]")
        search_button.click()
        
        # iterate through google serach pages
        while True:
            # get all search results
            results = self.browser.find_elements_by_class_name('r')
            
            # organize all hrefs to the users_links list
            users_links.extend([result.find_element_by_tag_name('a').get_attribute('href') for result in results])
            
            # go to next page
            next_button = self.browser.find_element_by_id('pnnext')
            next_page_link = next_button.get_attribute('href')
            self.browser.get(next_page_link)
            count += 1
            if count == page_limit:
                break
        
        print(users_links)
        return users_links
    
    def scrapePage(url):
        page_info = {}
        page_info['user'] = # name
        page_info['url'] = url
        page_info['current_company'] = # current company
        page_info['current_role'] = # current role
        page_info['previous_companies'] = # list of previous companies
        page_info['previous_roles'] = # list of previous roles
        page_info['skills'] = # list of skills
        page_info['location'] = # current location
        page_info['hobbies'] = # hobbies
        page_info['edu_institutions'] = # educational institutions attended
        page_info['edu_'] = # degrees, etc.
        
        return page_info
        

if __name__ == '__main__':
    username, password, driverpath, url = parseArgs()
    LIS = LinkedInScraper(username, password, driverpath, url)
    LIS.loginToLinkedIn()
    LIS.searchForRelevantLIProfiles('"computer vision"')


