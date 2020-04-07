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
#from selenium.webdriver.common.by import By 
#from selenium.webdriver.support.ui import WebDriverWait 
#from selenium.webdriver.support import expected_conditions as EC 
#from selenium.common.exceptions import TimeoutException, NoSuchElementException
from kafka import KafkaProducer
from hashlib import sha256

def parseArgs():
    parser = argparse.ArgumentParser(description='Use LinkedIn')
    parser.add_argument('--topic', type=str, help='search term. Replace spaces with _')
    parser.add_argument('--username', type=str,
                        help='LinkedIn Username')
    parser.add_argument('--password', type=str,
                        help='LinkedIn User password')
    parser.add_argument('--driver-path', type=str, default='/usr/local/bin/chromedriver',
                        help='Path to chromedriver')
    parser.add_argument('--login-url', type=str, default='https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin',
                        help='Path to URL page')
    parser.add_argument('--limit', type=int, default=3,
                        help='number of google pages to limit search to')
    parser.add_argument('--kafka-host', type=str, default="localhost",
                        help='kafka host')
    parser.add_argument('--kafka-port', type=int, default=29092,
                        help='kafka port')
    parser.add_argument('--backup', action='store_true', help='output to local json file <topic>_output.json')
    
    args = parser.parse_args()
    return args.topic, args.username, args.password, args.driver_path, args.login_url, args.limit, args.kafka_host, args.kafka_port, args.backup

def serialize(dictionary):
    return json.dumps(dictionary).encode('ascii')
    
class LinkedInScraper:
    def __init__(self, username, password, driverpath, login_url):
        self.username=username
        self.password=password
        self.login_url = login_url
        option = webdriver.ChromeOptions()
        option.add_argument(" — incognito")
        self.browser = webdriver.Chrome(executable_path=driverpath, chrome_options=option)
        
    def loginToLinkedIn(self):
        self.browser.get(self.login_url)
        username_input = self.browser.find_element_by_id("username")
        username_input.send_keys(username)
        time.sleep(random.random() * 5)
        
        password_input = self.browser.find_element_by_id("password")
        password_input.send_keys(password)
        
        XPATH="/html/body/div/main/div/form/div[contains(@class, 'login__form_action_container')]/button"
        login_button = self.browser.find_element_by_xpath(XPATH)
        time.sleep(random.random() * 3)
        login_button.click()
        time.sleep(4)
    
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
            count += 1
            if count == page_limit:
                break
            next_button = self.browser.find_element_by_id('pnnext')
            next_page_link = next_button.get_attribute('href')
            self.browser.get(next_page_link)
        
        #print(users_links)
        return users_links
    
    def scrapeLocation(self):
        try:
            location = self.browser.find_element_by_class_name('pv-top-card').find_element_by_xpath('div[2]/div[2]/div[1]/ul[2]/li[1]').text
        except selenium.common.exceptions.NoSuchElementException:
            location = False
        return location
    
    def scrapeSkills(self):
        top_skills_list = []
        skills_list = []
        # scroll to bottom
        #self.browser.execute_script("window.scrollTo(0, 500);") #document.body.scrollHeight);")
        # wait for new content to generate after scrolling
        time.sleep(1)
        # get skills section
        scroll=500
        while True:
            try:
                skills_section = self.browser.find_element_by_class_name('pv-skill-categories-section')
                break
            except selenium.common.exceptions.NoSuchElementException:
                self.browser.execute_script("window.scrollTo(0, {});".format(scroll))
                scroll += 500
                if scroll > 5000:
                    return top_skills_list, skills_list
                time.sleep(random.random() + 1)
        subsection = skills_section.find_element_by_tag_name('ol')
        top_skills = subsection.find_elements_by_tag_name('li')
        #print(len(top_skills))
        #print("Top Skills:")
        for top_skill in top_skills:
            try:
                skill = top_skill.find_element_by_xpath('div/div/p/a/span').text
         #       print(skill)
                top_skills_list.append(skill)
            except selenium.common.exceptions.NoSuchElementException:
                continue
            
        #print("expanding to get more...")
        skills_list.extend(top_skills_list)
        try:
            show_more_button = skills_section.find_element_by_xpath('div[2]/button')
            show_more_button.click()
            time.sleep(1)
            #print('Other skills:')
            expanded_section = self.browser.find_element_by_id('skill-categories-expanded')
            for x in expanded_section.find_elements_by_tag_name('div'):
                for area in x.find_elements_by_tag_name('li'):
                    try:
                        skill = area.find_element_by_xpath('div/div/p/a/span').text
                        #print(skill)
                        skills_list.append(skill)
                    except selenium.common.exceptions.NoSuchElementException:
                        continue
        except selenium.common.exceptions.NoSuchElementException:
            pass
        except selenium.common.exceptions.ElementClickInterceptedException:
            pass
        
        return top_skills_list, skills_list
    
    def scrapeLanguages(self):
        langs = []
        # scroll to bottom
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # wait for new content to generate after scrolling
        time.sleep(1)
        #print('Languages:')
        try:
            lang_section = self.browser.find_element_by_id('languages-expandable-content').find_element_by_xpath('ul')
            for x in lang_section.find_elements_by_tag_name('li'):
                #print(x.text)
                langs.append(x.text)
        except selenium.common.exceptions.NoSuchElementException:
            pass
        return langs
    
    def scrapePage(self, url):
        self.browser.get(url)
        time.sleep(random.random()*3 + 1)
        page_info = {}
        page_info['id'] = sha256(url.encode('utf-8')).hexdigest()
        location = self.scrapeLocation()
        if location:
            page_info['location'] = location
            top_skills, skills = self.scrapeSkills()
            page_info['top_skills'] = top_skills
            page_info['skills'] = skills
            page_info['languages'] = self.scrapeLanguages()
            return page_info
        else:
            return False
        

if __name__ == '__main__':
    topic, username, password, driverpath, url, page_limit, host, port , backup = parseArgs()
    producer = KafkaProducer(bootstrap_servers=["{}:{}".format(host,port)])
    
    LIS = LinkedInScraper(username, password, driverpath, url)
    query = '"{}"'.format(' '.join(topic.split('_')))
    relevant_users = LIS.searchForRelevantLIProfiles(query, page_limit=page_limit)
    LIS.loginToLinkedIn()
    for user_link in relevant_users[48:]:
        print(user_link)
        info = LIS.scrapePage(user_link)
        if not info:
            continue
        if backup:
            with open('{}_output.json'.format(topic), 'a') as fObj:
                fObj.write(json.dumps(info))
                fObj.write('\n')
        producer.send(topic, serialize(info))
        
    # flush data to topic at end
    producer.flush()
        


