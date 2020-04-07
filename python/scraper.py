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
python scraper.py --topic computer_vision --username <your linkedin username> --password <your linkedin password> --driver-path </path/to/chrome/driver> --login-url <https://linkedin.com/path/to/login/path?and&other&params>

--driver-path defaults to /usr/local/bin/chromedriver
--login-url defaults to the login page as of April 5, 2020

To Do:
- Add comments and clean up
"""
import argparse
import time
import random
import json
import selenium
from selenium import webdriver
from kafka import KafkaProducer
from hashlib import sha256

def parseArgs():
    parser = argparse.ArgumentParser(description='Use LinkedIn')
    parser.add_argument('--topic', type=str, help='search term. Replace spaces with _')
    parser.add_argument('--username', type=str, help='LinkedIn Username')
    parser.add_argument('--password', type=str, help='LinkedIn User password')
    parser.add_argument('--driver-path', type=str, default='/usr/local/bin/chromedriver', help='Path to chromedriver')
    parser.add_argument('--login-url', type=str, default='https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin', help='Path to URL page')
    parser.add_argument('--limit', type=int, default=3, help='number of google pages to limit search to')
    parser.add_argument('--kafka-host', type=str, default="localhost", help='kafka host')
    parser.add_argument('--kafka-port', type=int, default=29092, help='kafka port')
    parser.add_argument('--backup', action='store_true', help='output to local json file <topic>_output.json')
    
    args = parser.parse_args()
    return args.topic, args.username, args.password, args.driver_path, args.login_url, args.limit, args.kafka_host, args.kafka_port, args.backup

'''
Serialize dict for publishing to kafka
'''
def serialize(dictionary):
    return json.dumps(dictionary).encode('ascii')
    
class LinkedInScraper:
    def __init__(self, username, password, driverpath, login_url):
        self.username=username
        self.password=password
        self.login_url = login_url
        option = webdriver.ChromeOptions()
        option.add_argument(" — incognito") # use incognito mode
        self.browser = webdriver.Chrome(executable_path=driverpath, chrome_options=option)
        
    def loginToLinkedIn(self):
        self.browser.get(self.login_url)
        username_input = self.browser.find_element_by_id("username")
        username_input.send_keys(username)
        
        # wait upwards of 5 seconds before moving to password
        time.sleep(random.random() * 5)
        
        password_input = self.browser.find_element_by_id("password")
        password_input.send_keys(password)
        
        XPATH="/html/body/div/main/div/form/div[contains(@class, 'login__form_action_container')]/button"
        login_button = self.browser.find_element_by_xpath(XPATH)
        
        # wait upwards of 3 seconds before submitting
        time.sleep(random.random() * 3)
        login_button.click()
        
        # Wait 4 seconds for next page to load
        time.sleep(4)
    
    '''
    Search Google for relevant LinkedIn Profiles
    '''
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
            
            # gincrement page count
            count += 1
            # if enough pages have been viewed, terminate loop
            if count == page_limit:
                break
            next_button = self.browser.find_element_by_id('pnnext')
            next_page_link = next_button.get_attribute('href')
            self.browser.get(next_page_link)
        
        return users_links
    
    '''
    Find the user's given location from their profile
    '''
    def scrapeLocation(self):
        try:
            location = self.browser.find_element_by_class_name('pv-top-card').find_element_by_xpath('div[2]/div[2]/div[1]/ul[2]/li[1]').text
        
        # If the element is not available, the page does not exist (Google shows a cached page)
        except selenium.common.exceptions.NoSuchElementException:
            # Set location to false so downstream login knows to skip the given user
            location = False
        return location
    
    '''
    Find the user's listed skills
    '''
    def scrapeSkills(self):
        top_skills_list = []
        skills_list = []
        # Wait a second
        time.sleep(1)
        
        # Scroll downwards until the skills section is available
        scroll=500
        while True:
            try:
                skills_section = self.browser.find_element_by_class_name('pv-skill-categories-section')
                break # end loop when section is found
                
            except selenium.common.exceptions.NoSuchElementException:
                # scroll down
                self.browser.execute_script("window.scrollTo(0, {});".format(scroll))
                
                # increment scroll postion for next pass
                scroll += 500
                
                # if we have scrolled down over 10 times, the skills section is not populated.
                #   so return the empty lists
                if scroll > 5000:
                    return top_skills_list, skills_list
                
                # pause for 1-2 seconds between scroll attempts
                time.sleep(random.random() + 1)
                
        # once skills section is found, grab the top 3 skills
        subsection = skills_section.find_element_by_tag_name('ol')
        top_skills = subsection.find_elements_by_tag_name('li')
        
        
        for top_skill in top_skills:
            try:
                skill = top_skill.find_element_by_xpath('div/div/p/a/span').text
                
                # add skill to the list
                top_skills_list.append(skill)
            except selenium.common.exceptions.NoSuchElementException:
                continue
            
        # add top skills to the skills list
        skills_list.extend(top_skills_list)
        
        # expand to show more skills if possible
        try:
            show_more_button = skills_section.find_element_by_xpath('div[2]/button')
            show_more_button.click()
            
            # Pause 1 second to let expansion happen
            time.sleep(1)
            
            # get expanded section
            expanded_section = self.browser.find_element_by_id('skill-categories-expanded')
            for x in expanded_section.find_elements_by_tag_name('div'):
                for area in x.find_elements_by_tag_name('li'):
                    try:
                        skill = area.find_element_by_xpath('div/div/p/a/span').text
                        
                        # add skill to list
                        skills_list.append(skill)
                    except selenium.common.exceptions.NoSuchElementException:
                        # some li-s don't have that xpath, but they do not contain skills, so skip them
                        continue
                    
        # account for further skills not being populated
        except selenium.common.exceptions.NoSuchElementException:
            pass
        except selenium.common.exceptions.ElementClickInterceptedException:
            pass
        
        return top_skills_list, skills_list
    
    '''
    Find the user's listed languages, if possiblt
    '''
    def scrapeLanguages(self):
        langs = []
        # scroll to bottom
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # wait for new content to generate after scrolling
        time.sleep(1)
        
        try:
            lang_section = self.browser.find_element_by_id('languages-expandable-content').find_element_by_xpath('ul')
            for x in lang_section.find_elements_by_tag_name('li'):
                
                # add language to list
                langs.append(x.text)
        
        # account for languages not being there
        except selenium.common.exceptions.NoSuchElementException:
            pass
        return langs
    
    '''
    Scrape user's page for desired info
    '''
    def scrapePage(self, url):
        self.browser.get(url)
        time.sleep(random.random()*3 + 1)
        page_info = {}
        page_info['id'] = sha256(url.encode('utf-8')).hexdigest()
        location = self.scrapeLocation()
        
        # if location is not False, the page exists, so continue
        if location:
            page_info['location'] = location
            top_skills, skills = self.scrapeSkills()
            page_info['top_skills'] = top_skills
            page_info['skills'] = skills
            page_info['languages'] = self.scrapeLanguages()
            return page_info
        
        # if location is False, the page does not exist, so inform the downstream logic
        else:
            return False
        

if __name__ == '__main__':
    topic, username, password, driverpath, url, page_limit, host, port , backup = parseArgs()
    
    # Setup Kafka producer
    producer = KafkaProducer(bootstrap_servers=["{}:{}".format(host,port)])
    
    # Initialize LinkedInScraper object
    LIS = LinkedInScraper(username, password, driverpath, url)
    
    # construct the google query from the topic
    query = '"{}"'.format(' '.join(topic.split('_')))
    
    # search for the relevant users
    relevant_users = LIS.searchForRelevantLIProfiles(query, page_limit=page_limit)
    
    # login to the linkedin account
    LIS.loginToLinkedIn()
    
    # for each user
    for user_link in relevant_users:
        # print the url for debugging purposes
        print(user_link)
        
        # get info from page
        info = LIS.scrapePage(user_link)
        
        # if 'info' is not false, page was successfully scraped, so if it is False, skip this user
        if not info:
            continue
        
        # if --backup was passed in, write results to local file
        if backup:
            with open('{}_output.json'.format(topic), 'a') as fObj:
                fObj.write(json.dumps(info))
                fObj.write('\n')
        
        # publish to Kafka topic
        producer.send(topic, serialize(info))
        
    # flush data to topic at end to ensure all message get through
    producer.flush()
        


