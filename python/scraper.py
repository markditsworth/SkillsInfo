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
- debug issues caused by scrolling necessity
- kafka producer
"""
import argparse
import time
import selenium
from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException, NoSuchElementException


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
        
        #print(users_links)
        return users_links
    
    def scrapeLocation(self):
        return self.browser.find_element_by_xpath('//*[@id="ember52"]/div[2]/div[2]/div[1]/ul[2]/li[1]').text
    
    def scrapeEmployment(self):
        employment_history = []
        employment_section = self.browser.find_element_by_id('experience-section')
        for h in employment_section.find_elements_by_tag_name('li'):
            role = h.find_element_by_xpath('section/div/div/a/div[2]/h3').text
            co = h.find_element_by_xpath('section/div/div/a/div[2]/p[2]').text
            employment_history.append("{}: {}".format(co, role))
        return employment_history
            
    def scrapeEducation(self):
        edu_history = []
        edu_section = self.browser.find_element_by_id('education-section')
        for school in edu_section.find_elements_by_tag_name('li'):
            institution = school.find_element_by_xpath('div/div/a/div[2]/div[1]/h3').text
            degree = school.find_element_by_xpath('div/div/a/div[2]/div[1]/p[1]/span[2]').text
            subject = school.find_element_by_xpath('div/div/a/div[2]/div[1]/p[2]/span[2]').text
            edu_history.append("{}: {},{}".format(institution, degree, subject))
        return edu_history
    
    def scrapeSkills(self):
        top_skills_list = []
        skills_list = []
        # scroll to bottom
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # wait for new content to generate after scrolling
        time.sleep(2)
        # get skills section
        skills_section = self.browser.find_element_by_class_name('pv-skill-categories-section') 
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
        time.sleep(2)
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
        page_info = {}
        page_info['location'] = self.scrapeLocation()
        page_info['experience'] = self.scrapeEmployment()
        page_info['education'] = self.scrapeEducation()
        top_skills, skills = self.scrapeSkills()
        page_info['top_skills'] = top_skills
        page_info['skills'] = skills
        page_info['languages'] = self.scrapeLanguages()
        return page_info
        

if __name__ == '__main__':
    username, password, driverpath, url = parseArgs()
    LIS = LinkedInScraper(username, password, driverpath, url)
    LIS.loginToLinkedIn()
    relevant_users = LIS.searchForRelevantLIProfiles('"computer vision"', page_limit=2)
    for user_link in relevant_users:
        info = LIS.scrapePage(user_link)
        print('Info from {}:'.format(user_link))
        for x in info:
            print("{}: {}".format(x, info[x]))
        print('')


