import ast
import os
import re
import shutil
import time
from datetime import datetime
from urllib.parse import urlparse

import pandas as pd
import validators
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException

from Code.SavingOutputUtils import create_folder
from Code.XpathBuilder import XpathBuilder
from Code.TextDetector import get_text_elements

class WebPageCrawlerCraft:
    failed_msg = ''

    def __init__(self, url):
        # not needed for craft
        self.url = url
        self.driver = None
        # self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_store = None

    def store_data(self, filename, data):
        with open(filename, 'w') as file:
            file.write(str(data))

    def start(self, browser_type='chrome', headless=False):
        if browser_type == 'chrome':
            # Launch the Chrome browser using Chromedriver
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--start-maximized")
            if headless:
                chrome_options.add_argument("--headless")
            # chrome_options.add_argument(
            #     "--user-data-dir=C:/Users/ASHISPTDFST/AppData/Local/Google/Chrome/User data/Default")
            self.driver = webdriver.Chrome(options=chrome_options)

        elif browser_type == 'edge':
            edge_options = EdgeOptions()
            if headless:
                edge_options.add_argument("--headless")  # Run Edge in headless mode
            edge_options.add_argument("--start-maximized")
            # edge_options.add_argument(
            #     r"--user-data-dir=C:\Users\ASHISPTDFST\AppData\Local\Microsoft\Edge\User data\Default")
            # Instantiate the Edge driver
            self.driver = webdriver.Edge(options=edge_options)

    def crawl(self, action_object_data,inter_file, input_param, headless=False):
        if headless:
            driver_type = 'headless'
        else:
            driver_type = 'head'
        result_path_detections = create_folder(
            '../Data/detections')
        print("result_path_detections: ", result_path_detections)
        # # Navigate to the URL
        self.driver.get(self.url)
        # time.sleep(10)
        current_url = self.url
        next_url = self.url
        # time.sleep(50)
        # Wait for the page to fully load
        while not bool(self.driver.execute_script("return document.readyState == 'complete';")):
            time.sleep(2)

        # switch to default content before any interaction
        self.driver.switch_to.default_content()

        ##
        # html = etree.HTML(self.driver.page_source)
        ##
        # Parse the HTML content of the page using BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        i = 0
        # Loop through the action, object and test data
        for i, row in action_object_data.iterrows():
            # time.sleep(5)
            if i == 0:
                print('stage 1')
                if input_param['textElementDetection']:
                    get_text_elements(self.driver, self.driver.current_url)

            elif current_url != self.driver.current_url:
                # ------------------------ This block is used to capture the functional blocks ------------------------
                print('resumed:')
                if input_param['textElementDetection']:
                    get_text_elements(self.driver, self.driver.current_url)

            page = row['PageClass']
            action = row['Action']
            obj = row['Object']
            test_data = row['Test Data']
            input_data = row['Input']
            wait_time = 10
            print(f"Action:{action}, Object:{obj}, data:{test_data}")
            wait = WebDriverWait(self.driver, wait_time)
            # input_param['isShadowDom']= True


            # time.sleep(9)
            if str(action) == '':
                continue
            elif str(action).startswith('Navigate') or str(action).startswith('Launch'):
                # Navigate to the URL
                if validators.url(test_data):
                    try:
                        self.driver.get(test_data)
                    except WebDriverException as e:
                        for j, r in action_object_data.iterrows():
                            self.record_page_object_details(r['PageClass'], r['Action'], r['Object'], r['Test Data'],
                                                            '', r['Input'],
                                                            self.driver, input_param, '', '', inter_file,
                                                            '',
                                                            '')
                        return
                    current_url = test_data
                    next_url = test_data
                    page = self.extract_page_name(test_data)
                    self.record_page_object_details(page, 'Navigate', obj, test_data,
                                                    WebPageCrawlerCraft.failed_msg, input_data,
                                                    self.driver, input_param, '', '', inter_file,
                                                    '',
                                                    '')
                elif validators.url(obj):
                    try:
                        self.driver.get(obj)
                    except WebDriverException as e:
                        for j, r in action_object_data.iterrows():
                            self.record_page_object_details(r['PageClass'], r['Action'], r['Object'], r['Test Data'],
                                                            '', r['Input'],
                                                            self.driver, input_param, '', '', inter_file,
                                                            '',
                                                            '')
                        return
                    current_url = obj
                    next_url = obj
                    page = self.extract_page_name(obj)
                    self.record_page_object_details(page, 'Navigate', obj, test_data,
                                                    WebPageCrawlerCraft.failed_msg, input_data,
                                                    self.driver, input_param,'', '', inter_file,
                                                    '',
                                                    '')
                else:
                    for j, r in action_object_data.iterrows():
                        self.record_page_object_details(r['PageClass'], r['Action'], r['Object'], r['Test Data'],
                                                        '', r['Input'],
                                                        self.driver, input_param, '', '', inter_file,
                                                        '',
                                                        '')
                    return
            elif action == 'Click' or action == 'Uncheck':
                if input_param['isShadowDom']:
                    try:
                        ready = False
                        while not ready:
                            ready = self.driver.execute_script("return document.readyState") == "complete"
                            time.sleep(1)
                        time.sleep(2)
                        if str(obj).endswith('button'):
                            obj = str(obj).replace('button', '').strip()
                            # removed button for now at ending, in future need to address this
                        jspath = XpathBuilder.process_dom_with_js_path(XpathBuilder, self.driver, obj,
                                                                       action)
                        if jspath:
                            print("Shadow Dom Element Detected")
                            check_for_visible_element = self.driver.execute_script(f'return {jspath}')
                            final_xpath = jspath
                            page = self.extract_page_name(self.driver.current_url)
                            self.record_page_object_details(page, action, obj, test_data,
                                                            WebPageCrawlerCraft.failed_msg, input_data,
                                                            self.driver, input_param, check_for_visible_element,
                                                            final_xpath, inter_file, '', '')
                            check_for_visible_element.click()
                            continue
                    except:
                        xpath = ''
                        check_for_visible_element = ""
                        WebPageCrawlerCraft.failed_msg = 'No Such Element is Found'
                        page = self.extract_page_name(self.driver.current_url)
                        self.record_page_object_details(page, action, obj, test_data,
                                                        WebPageCrawlerCraft.failed_msg, input_data,
                                                        self.driver, input_param,
                                                        check_for_visible_element, xpath, inter_file,
                                                        '', '')

                if str(obj).endswith('button'):
                    obj = str(obj).replace('button', '').strip()
                    # removed button for now at ending, in future need to address this
                time.sleep(5)
                get_live_obj, frame_id = XpathBuilder.create_xpath_from_link_text(XpathBuilder, soup, obj, self.driver, obj)

                if not get_live_obj:
                    if input_param['isContinue']:
                        self.record_page_object_details(self.extract_page_name(self.driver.current_url), action, obj,
                                                        test_data, 'Invalid action: No such object ' + obj, input_data,
                                                        self.driver, input_param,
                                                        None, '', inter_file,
                                                        '', '')
                        continue
                    else:
                        break


                final_xpath = ''
                # print('current_url: ', current_url)
                # print('next_url: ', next_url)
                # if below magic is no more working, then use the final shastra
                if frame_id:
                    print('frame id detected: ', frame_id)
                    print('get_live_obj iframe: ', get_live_obj)
                    # ifmx = self.driver.find_elements(By.TAG_NAME, 'iframe')
                    # print("iframes: ", ifmx)
                    #     # step to add
                    #     # 1. switch to iframe
                    #     # 2. perform action as per instruction
                    #     # the remaining after switch to the frame is same only
                    # self.driver.switch_to.frame(frame_id)
                    page = self.extract_page_name(self.driver.current_url)
                    self.record_page_object_details(page, 'switch to iframe', obj, test_data,
                                                    WebPageCrawlerCraft.failed_msg, input_data,
                                                    self.driver, '',
                                                    frame_id, inter_file, '', '')
                try:
                    if str(current_url) == str(next_url):
                        get_last_xpath = self.record_page_get_last_xpath(inter_file)
                        ele_last_xp = wait.until(EC.visibility_of_element_located((By.XPATH, get_last_xpath)))
                        if ele_last_xp.location['x'] == 0 and ele_last_xp.location['y'] == 0:
                            ele_last_xp = ele_last_xp.find_element(By.XPATH, '..')
                            print('Retracted to one step back to parent node')
                        self.driver.execute_script("arguments[0].style.border='3px solid red'", ele_last_xp)
                        min_dist = 0
                        for xp_nr in get_live_obj:
                            xp_nr = str(xp_nr).rpartition("/")[0]
                            ele_xp_nr = wait.until(EC.visibility_of_element_located((By.XPATH, xp_nr)))
                            dist = XpathBuilder.calculate_distance(XpathBuilder, ele_last_xp, ele_xp_nr)
                            # print('dist: ', dist)
                            if min_dist == 0:
                                final_xpath = xp_nr
                                min_dist = dist
                            elif min_dist > dist:
                                final_xpath = xp_nr
                                min_dist = dist

                    else:
                        final_xpath = str(get_live_obj[0]).rpartition("/")[0]
                except Exception as e:
                    final_xpath = str(get_live_obj[0]).rpartition("/")[0]
                print("Web Element: ", obj)
                # print('xpath: ', str(get_live_obj))
                print("Xpath: ", final_xpath)
                # self.driver.find_element(By.XPATH, final_xpath).click()
                check_for_visible_element = wait.until(EC.visibility_of_element_located((By.XPATH, final_xpath)))
                page = self.extract_page_name(self.driver.current_url)
                self.record_page_object_details(page, action, obj, test_data,
                                                WebPageCrawlerCraft.failed_msg, input_data,
                                                self.driver, input_param, check_for_visible_element,
                                                final_xpath, inter_file, '', '')
                # check_for_visible_element.click()
                current_url = self.driver.current_url
                self.driver.execute_script("arguments[0].click();", check_for_visible_element)
                next_url = self.driver.current_url

            elif action == 'Enter' or action == 'Populate' or action == 'Upload':
                if input_param['isShadowDom']:
                    try:
                        ready = False
                        while not ready:
                            ready = self.driver.execute_script("return document.readyState") == "complete"
                            time.sleep(1)
                        jspath = XpathBuilder.process_dom_with_js_path(XpathBuilder, self.driver, obj,
                                                                       action)
                        if jspath:
                            print("Shadow Dom Element Detected")
                            check_for_visible_element = self.driver.execute_script(f'return {jspath}')
                            final_xpath = jspath
                            page = self.extract_page_name(self.driver.current_url)
                            self.record_page_object_details(page, action, obj, test_data,
                                                            WebPageCrawlerCraft.failed_msg, input_data,
                                                            self.driver, input_param,
                                                            check_for_visible_element,
                                                            final_xpath,
                                                            inter_file, '', '')
                            check_for_visible_element.send_keys(str(test_data))
                            continue
                    except:
                        xpath = ''
                        check_for_visible_element = ""
                        WebPageCrawlerCraft.failed_msg = 'No Such Element is Found'
                        page = self.extract_page_name(self.driver.current_url)
                        self.record_page_object_details(page, action, obj, test_data,
                                                        WebPageCrawlerCraft.failed_msg, input_data,
                                                        self.driver, input_param,
                                                        check_for_visible_element, xpath, inter_file,
                                                        '', '')

                elif test_data:
                    if str(obj).startswith('mandatory field') or 'mandatory field' in str(obj):
                        print('process fields')
                        form_df = self.detect_form_elements(self.driver, action_object_data)
                        print(form_df)
                        self.crawl(form_df, inter_file, input_param)
                        # process here list of action, object and test data
                    else:
                        try:
                            xp, get_nearest_input = XpathBuilder.get_nearest_input(XpathBuilder, soup, obj,
                                                                                   self.driver,
                                                                                   action)
                            if xp == '' and get_nearest_input is None:
                                if input_param['isContinue']:
                                    self.record_page_object_details(
                                        self.extract_page_name(self.driver.current_url), action, obj,
                                        test_data,
                                        'Invalid action: Invalid data ' + test_data + ' for object ' + obj,
                                        input_data,
                                        self.driver, input_param,
                                        None, '', inter_file,
                                        '', '')
                                    continue
                                else:
                                    break
                            # raise ValueError(f"No test data provided for row {i + 1}.")
                            page = self.extract_page_name(self.driver.current_url)
                            self.record_page_object_details(page, action, obj, test_data,
                                                            WebPageCrawlerCraft.failed_msg, input_data,
                                                            self.driver, input_param,
                                                            get_nearest_input, xp, inter_file, '', '')
                            get_nearest_input.clear()
                            get_nearest_input.send_keys(str(test_data))
                        except:
                            try:
                                check_for_visible_element = self.driver.find_element(By.XPATH,
                                                                                     f"//*[text()='{obj}']//..//input")
                                page = self.extract_page_name(self.driver.current_url)
                                self.record_page_object_details(page, action, obj, test_data,
                                                                WebPageCrawlerCraft.failed_msg, input_data,
                                                                self.driver, input_param,
                                                                check_for_visible_element,
                                                                f"//*[text()='{obj}']//..//input", inter_file, '',
                                                                '')
                                check_for_visible_element.send_keys(str(test_data))
                            except:
                                try:
                                    check_for_visible_element = self.driver.find_element(By.XPATH,
                                                                                         f"//*[text()='{obj}']//..//textarea")
                                    page = self.extract_page_name(self.driver.current_url)
                                    self.record_page_object_details(page, action, obj, test_data,
                                                                    WebPageCrawlerCraft.failed_msg, input_data,
                                                                    self.driver, input_param,
                                                                    check_for_visible_element,
                                                                    f"//*[text()='{obj}']//..//textarea", inter_file,
                                                                    '',
                                                                    '')

                                    check_for_visible_element.send_keys(str(test_data))
                                except:
                                    try:
                                        check_for_visible_element = self.driver.find_element(By.CSS_SELECTOR,
                                                                                             f"[placeholder='{obj}']")
                                        page = self.extract_page_name(self.driver.current_url)
                                        self.record_page_object_details(page, action, obj, test_data,
                                                                        WebPageCrawlerCraft.failed_msg, input_data,
                                                                        self.driver, input_param,
                                                                        check_for_visible_element,
                                                                        f"//*[contains(@placeholder, '{obj}')]",
                                                                        inter_file, '', '')
                                        check_for_visible_element.send_keys(str(test_data))
                                    except:
                                        xpath = ''
                                        check_for_visible_element = ""
                                        WebPageCrawlerCraft.failed_msg = 'No Such Element is Found'
                                        self.record_page_object_details(page, action, obj, test_data,
                                                                        WebPageCrawlerCraft.failed_msg, input_data,
                                                                        self.driver, input_param,
                                                                        check_for_visible_element, xpath, inter_file,
                                                                        '', '')


            elif action == 'Assert_text' or action == 'Validate' or action == 'Verify':
                condition = row['Condition']
                if condition:
                    # condition is present in extracted data, process likewise
                    if condition == 'is displayed' or condition == 'is not displayed' or (
                            'displayed' in str(condition)):
                        # add the code for validation on either object or page
                        # check for condition value
                        condition_value = row['Condition_Value']
                        if condition_value:
                            # both condition and codnition value present, store details
                            page = self.extract_page_name(self.driver.current_url)
                            self.record_page_object_details(page, action, obj, test_data,
                                                            WebPageCrawlerCraft.failed_msg, input_data,
                                                            self.driver, input_param,
                                                            '', '', inter_file, condition,
                                                            condition_value)
                else:
                    # condition is not present, so most likely its in object, detect and extract and process
                    if 'displayed' in str(obj):
                        # the condition is in object, process
                        condition = ''
                        if str(obj).endswith('is displayed'):
                            condition = 'is displayed'
                        elif str(obj).endswith('is not displayed'):
                            condition = 'is not displayed'
                        condition_value = 'page/header'
                        self.record_page_object_details(page, action, obj, test_data,
                                                        WebPageCrawlerCraft.failed_msg, input_data,
                                                        self.driver, input_param,
                                                        '', '', inter_file, condition,
                                                        condition_value)
            elif action == 'Select':
                if input_param['isShadowDom']:
                    try:
                        ready = False
                        while not ready:
                            ready = self.driver.execute_script("return document.readyState") == "complete"
                            time.sleep(1)
                        jspath = XpathBuilder.process_dom_with_js_path(XpathBuilder, self.driver, test_data,
                                                                       action)
                        if jspath:
                            print("Shadow Dom Element Detected")
                            check_for_visible_td_element = self.driver.execute_script(f'return {jspath}')
                            final_xpath = jspath
                            page = self.extract_page_name(self.driver.current_url)
                            self.record_page_object_details(page, action, obj, test_data,
                                                            WebPageCrawlerCraft.failed_msg, input_data,
                                                            self.driver, input_param,
                                                            check_for_visible_td_element,
                                                            final_xpath,
                                                            inter_file, '', '')
                            check_for_visible_td_element.click()
                            continue
                    except:
                        xpath = ''
                        check_for_visible_element = ""
                        WebPageCrawlerCraft.failed_msg = 'No Such Element is Found'
                        page = self.extract_page_name(self.driver.current_url)
                        self.record_page_object_details(page, action, obj, test_data,
                                                        WebPageCrawlerCraft.failed_msg, input_data,
                                                        self.driver, input_param,
                                                        check_for_visible_element, xpath, inter_file,
                                                        '', '')

                elif test_data and str(test_data) != 'nan':
                    try:
                        get_live_td, frame_id = XpathBuilder.create_xpath_from_link_text(XpathBuilder, soup, test_data,
                                                                               self.driver, obj)
                        try:
                            final_xpath_of_td = str(get_live_td[0]).rpartition("/")[0]
                        except:
                            final_xpath_of_td = get_live_td
                        check_for_visible_td_element = self.driver.find_element(By.XPATH, final_xpath_of_td)
                        page = self.extract_page_name(self.driver.current_url)
                        self.record_page_object_details(page, action, obj, test_data,
                                                        WebPageCrawlerCraft.failed_msg, input_data,
                                                        self.driver, input_param,
                                                        check_for_visible_td_element,
                                                        final_xpath_of_td, inter_file, '', '')
                        check_for_visible_td_element.click()
                    except:
                        # print(h'Test data Entry: ', test_data)
                        get_live_td = XpathBuilder.create_releative_xpath_from_link_text(XpathBuilder, soup, test_data,
                                                                                         obj,
                                                                                         self.driver)
                        if get_live_td == '':
                            if input_param['isContinue']:
                                self.record_page_object_details(self.extract_page_name(self.driver.current_url), action,
                                                                obj, test_data,
                                                                'Invalid action: Invalid data ' + test_data + ' for object ' + obj,
                                                                input_data,
                                                                self.driver, input_param,
                                                                None, '', inter_file,
                                                                '', '')
                                continue
                            else:
                                break
                        # final_xpath_of_td = str(get_live_td[0]).rpartition("/")[0]
                        final_xpath_of_td = get_live_td
                        check_for_visible_td_element = self.driver.find_element(By.XPATH, final_xpath_of_td)
                        page = self.extract_page_name(self.driver.current_url)
                        self.record_page_object_details(page, action, obj, test_data,
                                                        WebPageCrawlerCraft.failed_msg, input_data,
                                                        self.driver, input_param,
                                                        check_for_visible_td_element,
                                                        final_xpath_of_td, inter_file, '', '')
                        self.driver.execute_script("arguments[0].click();", check_for_visible_td_element)
                else:
                    get_live_obj, frame_id = XpathBuilder.create_xpath_from_link_text(XpathBuilder, soup, obj, self.driver, obj)
                    if len(get_live_obj) == 0:
                        if input_param['isContinue']:
                            self.record_page_object_details(self.extract_page_name(self.driver.current_url), action,
                                                            obj, test_data,
                                                            'Invalid action: Invalid data ' + test_data + ' for object ' + obj,
                                                            input_data,
                                                            self.driver, input_param,
                                                            None, '', inter_file,
                                                            '', '')
                            continue
                        else:
                            break
                    if get_live_obj:
                        final_xpath = str(get_live_obj[0]).rpartition("/")[0]
                        final_xpath = str(final_xpath) + "[text()=\"" + obj + "\"]"
                        check_for_visible_element = self.driver.find_element(By.XPATH, final_xpath)
                        page = self.extract_page_name(self.driver.current_url)
                        self.record_page_object_details(page, action, obj, test_data,
                                                        WebPageCrawlerCraft.failed_msg, input_data,
                                                        self.driver, input_param,
                                                        check_for_visible_element,
                                                        final_xpath, inter_file, '', '')
                        check_for_visible_element.click()
                    else:
                        pass

            elif action == 'Hover':
                get_live_obj, frame_id = XpathBuilder.create_xpath_from_link_text_without_prim(XpathBuilder, soup, obj,
                                                                                     self.driver)
                if len(get_live_obj) == 0:
                    if input_param['isContinue']:
                        self.record_page_object_details(self.extract_page_name(self.driver.current_url), action, obj,
                                                        test_data,
                                                        'Invalid action: No such object ' + obj, input_data,
                                                        self.driver, input_param,
                                                        None, '', inter_file,
                                                        '', '')
                        continue
                    else:
                        break
                final_xpath = str(get_live_obj[0]).rpartition("/")[0]
                print(final_xpath, ":", obj)
                check_for_visible_element = self.driver.find_element(By.XPATH, final_xpath)
                second_element = wait.until(EC.element_to_be_clickable((By.XPATH, final_xpath)))

                action_chains = ActionChains(self.driver)
                action_chains.move_to_element(second_element).perform()

                self.record_page_object_details(page, action, obj, test_data,
                                                WebPageCrawlerCraft.failed_msg, input_data,
                                                self.driver, input_param, check_for_visible_element,
                                                final_xpath, inter_file, '', '')

            elif action == 'Hover_and_Click':
                get_live_obj, frame_id = XpathBuilder.create_xpath_from_link_text_without_prim(XpathBuilder, soup, obj,
                                                                                     self.driver)
                if len(get_live_obj) == 0:
                    if input_param['isContinue']:
                        self.record_page_object_details(self.extract_page_name(self.driver.current_url), action, obj,
                                                        test_data,
                                                        'Invalid action: No such object ' + obj, input_data,
                                                        self.driver, input_param,
                                                        None, '', inter_file,
                                                        '', '')
                        continue
                    else:
                        break
                if frame_id:
                    print('frame id detected: ', frame_id)
                    print('get_live_obj iframe: ', get_live_obj)
                    # ifmx = self.driver.find_elements(By.TAG_NAME, 'iframe')
                    # print("iframes: ", ifmx)
                    #     # step to add
                    #     # 1. switch to iframe
                    #     # 2. perform action as per instruction
                    #     # the remaining after switch to the frame is same only
                    # self.driver.switch_to.frame(frame_id)
                    page = self.extract_page_name(self.driver.current_url)
                    self.record_page_object_details(page, 'switch to iframe', obj, test_data,
                                                    WebPageCrawlerCraft.failed_msg, input_data,
                                                    self.driver, '',
                                                    frame_id, inter_file, '', '')
                final_xpath = str(get_live_obj[0]).rpartition("/")[0]
                print(final_xpath, ":", obj)
                check_for_visible_element = self.driver.find_element(By.XPATH, final_xpath)

                action_chains = ActionChains(self.driver)
                action_chains.move_to_element(check_for_visible_element).perform()

                if test_data:
                    get_live_obj_2, frame_id_2 = XpathBuilder.create_xpath_from_link_text_without_prim(XpathBuilder, soup,
                                                                                           test_data,
                                                                                           self.driver)
                    if len(get_live_obj_2) == 0:
                        if input_param['isContinue']:
                            WebPageCrawlerCraft.failed_msg = 'Invalid action: No such object ' + obj

                            self.record_page_object_details(self.extract_page_name(self.driver.current_url), action,
                                                            obj, test_data,
                                                            WebPageCrawlerCraft.failed_msg, input_data,
                                                            self.driver, input_param,
                                                            None, '', inter_file,
                                                            '', '')
                            continue
                        else:
                            break
                    final_xpath_2 = str(get_live_obj_2[0]).rpartition("/")[0]
                    print(final_xpath_2, ":", test_data)
                    # second_element = wait.until(EC.visibility_of_element_located((By.XPATH, final_xpath_2)))
                    second_element = wait.until(EC.element_to_be_clickable((By.XPATH, final_xpath_2)))

                    action_chains.move_to_element(second_element).click().perform()

                else:
                    raise ValueError("XPath of the second element is missing in test_data")

                self.record_page_object_details(page, action, obj, test_data,
                                                WebPageCrawlerCraft.failed_msg, input_data,
                                                self.driver, input_param, check_for_visible_element,
                                                final_xpath_2, inter_file, '', '')

            else:
                # raise ValueError(f"Invalid action '{action}' for row {i + 1}.")
                WebPageCrawlerCraft.failed_msg = 'Invalid action'
                check_for_visible_element = ""
                xpath = ''
                self.record_page_object_details(page, action, obj, test_data, WebPageCrawlerCraft.failed_msg,
                                                input_data,
                                                self.driver, input_param,
                                                check_for_visible_element, xpath, inter_file, '', '')

        if i != len(action_object_data) - 1 is False:
            print("\nFailed Steps:")
            for j, row in action_object_data.iterrows():
                if j < i:
                    continue
                page = self.extract_page_name(self.driver.current_url)
                action = row['Action']
                obj = row['Object']
                test_data = row['Test data']
                input_data = row['Input']

                print(f"Action:{action}, Object:{obj}, data:{test_data}")

                invalid_object_actions = ["Click", "Uncheck", "Hover", "Hover_and_Click"]
                invalid_data_actions = ["Enter", "Populate", "Upload", "Select"]

                if j == i:
                    if action in invalid_object_actions:
                        WebPageCrawlerCraft.failed_msg = 'Invalid action: No such object ' + obj
                    if action in invalid_data_actions:
                        WebPageCrawlerCraft.failed_msg = 'Invalid action: Invalid data ' + test_data + ' for object ' + obj
                else:

                    WebPageCrawlerCraft.failed_msg = 'Invalid action: Dependant on previously for_comparison step'

                self.record_page_object_details(page, action, obj, test_data,
                                                WebPageCrawlerCraft.failed_msg, input_data,
                                                self.driver, input_param,
                                                None, '', inter_file,
                                                '', '')
    def stop(self):
        # Close the browser
        self.driver.quit()
        self.driver = None
        # # delete folder self.embedded_data_path
        # try:
        #     # Check if the folder exists
        #     if os.path.exists(self.embedded_data_path):
        #         # Remove the folder and all its contents
        #         shutil.rmtree(self.embedded_data_path)
        #         print(f"Folder '{self.embedded_data_path}' has been deleted successfully.")
        #     else:
        #         print(f"Folder '{self.embedded_data_path}' does not exist.")
        # except Exception as e:
        #     print(f"An error occurred while deleting the folder: {e}")

    def record_page_object_details(self, page, action, obj, test_data, failed_msg, input_data, driver,
                                   input_param, check_for_visible_element, xpath,
                                   file_name, condition, condition_value):
        get_url = driver.current_url
        rows = []
        cols = []
        cols.append('url')
        cols.append('page')
        cols.append('action')
        cols.append('object')
        cols.append('data')
        cols.append('failure')
        cols.append('input')
        rows.append(get_url)
        rows.append(page)
        rows.append(action)
        rows.append(obj)
        rows.append(test_data)
        rows.append(failed_msg)
        rows.append(input_data)
        # for attrib in check_for_visible_element.get_property('attributes'):
        #     cols.append(attrib['name'])
        #     rows.append(attrib['value'])
        #     print(cols, ", ", rows)
        if action == 'Navigate':
            get_all_attrib_dict = ''
            cols.append('TagName')
            rows.append('')
            cols.append('ID')
            rows.append('')
            cols.append('Class')
            rows.append('')
            cols.append('Name')
            rows.append('')
            cols.append('LinkText')
            rows.append('')
            cols.append('CssSelector_with_Class')
            rows.append('')
            cols.append('CssSelector_with_ID')
            rows.append('')
            cols.append('All_Attributes')
            rows.append(get_all_attrib_dict)
            cols.append('Xpath')
            rows.append(xpath)
            cols.append('RelXpath')
            rows.append('')
            cols.append('Locator')
            rows.append('')
            cols.append('Condition')
            rows.append('')
            cols.append('Condition_Value')
            rows.append('')
        elif action == 'switch to iframe':
            get_all_attrib_dict = ''
            cols.append('TagName')
            rows.append('')
            cols.append('ID')
            rows.append(xpath)
            cols.append('Class')
            rows.append('')
            cols.append('Name')
            rows.append('')
            cols.append('LinkText')
            rows.append('')
            cols.append('CssSelector_with_Class')
            rows.append('')
            cols.append('CssSelector_with_ID')
            rows.append('')
            cols.append('All_Attributes')
            rows.append(get_all_attrib_dict)
            cols.append('Xpath')
            rows.append('')
            cols.append('Condition')
            rows.append('')
            cols.append('Condition_Value')
            rows.append('')
        elif action == 'Validate' or action == 'Verify':
            get_all_attrib_dict = ''
            cols.append('TagName')
            rows.append('')
            cols.append('ID')
            rows.append('')
            cols.append('Class')
            rows.append('')
            cols.append('Name')
            rows.append('')
            cols.append('LinkText')
            rows.append('')
            cols.append('CssSelector_with_Class')
            rows.append('')
            cols.append('CssSelector_with_ID')
            rows.append('')
            cols.append('All_Attributes')
            rows.append(get_all_attrib_dict)
            cols.append('Xpath')
            rows.append('')
            cols.append('RelXpath')
            rows.append('')
            cols.append('Locator')
            rows.append('')
            cols.append('Condition')
            rows.append(condition)
            cols.append('Condition_Value')
            rows.append(condition_value)
        else:
            if check_for_visible_element:
                get_all_attrib_dict = self.driver.execute_script(
                    'var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) '
                    '{ items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;',
                    check_for_visible_element)
                cols.append('TagName')
                rows.append(check_for_visible_element.get_attribute('tagName'))
                cols.append('ID')
                rows.append(check_for_visible_element.get_attribute('id'))
                cols.append('Class')
                rows.append(check_for_visible_element.get_attribute('class'))
                cols.append('Name')
                rows.append('')
                cols.append('LinkText')
                rows.append('')
                cols.append('CssSelector_with_Class')
                rows.append(check_for_visible_element.get_attribute('class'))
                cols.append('CssSelector_with_ID')
                rows.append(check_for_visible_element.get_attribute('id'))
                cols.append('All_Attributes')
                rows.append(get_all_attrib_dict)
            else:
                cols.append('TagName')
                rows.append('')
                cols.append('ID')
                rows.append('')
                cols.append('Class')
                rows.append('')
                cols.append('Name')
                rows.append('')
                cols.append('LinkText')
                rows.append('')
                cols.append('CssSelector_with_Class')
                rows.append('')
                cols.append('CssSelector_with_ID')
                rows.append('')
                cols.append('All_Attributes')
                rows.append({})
            cols.append('Xpath')
            rows.append(xpath)
            cols.append('RelXpath')
            rows.append('')
            cols.append('Locator')
            rows.append('')
            cols.append('Condition')
            rows.append('')
            cols.append('Condition_Value')
            rows.append('')
        df = pd.DataFrame(columns=cols)
        df.loc[len(df)] = rows
        if action != 'Navigate':
            priority_list = ast.literal_eval(input_param['locatorPriority'])
            locator, rel_xpath = self.locator_priority(priority_list, df, check_for_visible_element)
            df['Locator'] = locator
            df['RelXpath'] = rel_xpath
        filename = file_name
        df.to_csv(filename, mode='a', header=not os.path.isfile(filename), index=False)
        return True

    def locator_priority(self, priority_list, df, element):
        locator_list = {'ID': By.ID, 'Name': By.NAME, 'Class': By.CLASS_NAME, 'TagName': By.TAG_NAME,
                        'LinkText': By.LINK_TEXT, 'CssSelector_with_Class': By.CSS_SELECTOR, 'CssSelector_with_ID': By.CSS_SELECTOR,
                        'Xpath': By.XPATH}
        rel_xpath = ''
        locator = ''
        for _, row in df.iterrows():
            for item in range(len(priority_list)):
                if row[priority_list[item]] != '' and not pd.isna(row[priority_list[item]]):
                    locator = priority_list[item]
                    locator_item = locator_list.get(locator)
                    if locator_item:
                        try:
                            check_for_visible_element = self.driver.find_element(locator_item, row[priority_list[item]])
                            if element == check_for_visible_element:
                                rel_xpath = XpathBuilder.generate_relative_xpath(XpathBuilder, self.driver,
                                                                                 check_for_visible_element)
                                if locator == 'Xpath':
                                    locator = 'RelXpath'
                                break
                        except:
                            item += 1
                else:
                    item += 1
        return locator, rel_xpath

    def detect_form_elements(self, driver, df):
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        form = soup.find('form')
        if form:
            # Initialize a list to store form elements
            form_elements = []
            actions = []
            # Find visible labels within the form
            labels = form.find_all('label')

            for label in labels:
                label_text = label.text.strip()
                associated_input = label.find_next('input')
                if label.find_next('select') is None:
                    input_type = associated_input.get('type')
                    if input_type == 'radio':
                        action = 'Select'
                    else:
                        action = 'Enter'
                else:
                    select_index = label.find_all_next().index(label.find_next('select'))
                    input_index = label.find_all_next().index(label.find_next('input'))
                    if int(select_index) < int(input_index):
                        input_type = 'select'
                        associated_input = label.find_next('select')
                        action = 'Select'
                    else:
                        input_type = associated_input.get('type')
                        action = 'Enter'
                # print(f"label_text: {label_text}, ...........associated_input: {associated_input}")
                associated_input_web = []
                if associated_input.get('id'):
                    associated_input_web = self.driver.find_element(By.ID, associated_input.get('id'))
                else:
                    associated_input_web = self.driver.find_element(By.XPATH, self.xpath_soup(associated_input))
                if label_text and label_text != 'Male' and label_text != 'Female' and associated_input and associated_input_web.is_displayed():
                    # Store the label and associated input type in the list
                    form_elements.append((label_text.split('\n')[0], input_type, action))
                elif label_text and label_text == 'Gender':
                    form_elements.append((label_text.split('\n')[0], input_type, action))

            # Create a DataFrame from the form elements list
            df = pd.DataFrame(form_elements, columns=["Label", "InputType", "Action"])

            # Print the DataFrame
            # read_datasheet = "C:/Users/COG22K/Documents/DataSheet.xlsx"
            # datasheet = pd.read_excel(read_datasheet)

            datasheet = pd.DataFrame(columns=['Object', 'Test data'])

            for index, row in df.iterrows():
                datasheet = datasheet.append(
                    pd.DataFrame({'Object': row['Object'], 'Test data': row['Test data']}, index=[0]),
                    ignore_index=True)

            values = []

            for label in df['Label']:
                if label in datasheet.columns:
                    value = datasheet[label].iloc[0]
                    values.append(value)
                else:
                    values.append('NoTestDataProvided')
            # label_to_value = {label: datasheet[label] for label in df['Label'] if label in datasheet.columns}
            # df['value']= df['Label'].map(label_to_value)
            df['value'] = values
            # map this data with detected form elements and assign the data in above
            print(df)
            df.rename(columns={'Label': 'Object', 'value': 'data'}, inplace=True)
            df['page'] = 'formPage'
            print('updated field list:')
            df = df[df.Data != 'NoTestDataProvided']
            print(df)
            return df
        else:
            print("No form found on the page.")
            return "No form found on the page."

    def extract_page_name(self, url):
        parsed_url = urlparse(url)
        if parsed_url.path:
            page_name = re.sub(r'\W+', '_', parsed_url.path.split('/')[-1])
            if page_name:
                return page_name
            else:
                return "landing_page"
        return "landing_page"

    def record_page_get_last_xpath(self, inter_file):
        xpath = pd.read_csv(inter_file).iloc[-1]['Xpath']
        if xpath:
            return xpath
        else:
            return pd.read_csv(inter_file).iloc[-2]['Xpath']

    def xpath_soup(self, element):
        components = []
        child = element if element.name else element.parent
        for parent in child.parents:
            siblings = parent.find_all(child.name, recursive=False)
            components.append(
                child.name
                if siblings == [child] else
                '%s[%d]' % (child.name, 1 + siblings.index(child))
            )
            child = parent
        components.reverse()
        return '/%s' % '/'.join(components)