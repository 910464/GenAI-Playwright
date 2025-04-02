import ast
import os
import time

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from Code.get_html import inject_mutation_observer, generate_relative_xpath
from Code.WebPageCrawlerCraft import WebPageCrawlerCraft

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver import ActionChains

def perform(driver: WebDriver, steps: dict, input_param: dict , inter_file , chroma_connector, session_id: str):
    """
    Perform the steps provided in the input dictionary.
    If all actions are successfully performed, return True, 0.
    If any action fails, return False, index of the failed action.
    """
    global xp
    steps_performed = ""
    steps_not_performed = ""
    status = 1
    previous_url = driver.current_url

    # # Initialize crawler if input_param and inter_file are provided
    # crawler = None
    # if input_param and inter_file:
    crawler = WebPageCrawlerCraft('https://www.google.co.in/')

    for step in steps:
        try:
            action = step["action"]
            xp = step.get("xpath", "")
            if action == "enter":
                page_name = crawler.extract_page_name(driver.current_url)
                obj = step['element']
                test_data = step["text"]
                xp = step["xpath"]
                # Get relative XPaths

                # print(relative_xpaths)
                element = driver.find_element(By.XPATH, step["xpath"])
                relative_xpaths = generate_relative_xpath(driver, element)
                element.send_keys(step["text"])
                record_page_object_details(page_name, action, obj,
                                                   test_data, '', '',
                                                   driver, input_param,
                                                   None, xp, inter_file,
                                                   '', '', relative_xpaths)
            elif action == "click":
                page_name = crawler.extract_page_name(driver.current_url)
                obj = step['element']
                xp = step["xpath"]
                # Get relative XPaths

                # print(relative_xpaths)
                element = driver.find_element(By.XPATH, step["xpath"])
                relative_xpaths = generate_relative_xpath(driver, element)
                try:
                    actions = ActionChains(driver)
                    actions.move_to_element(element).click().perform()
                except:  # element = driver.find_element(By.XPATH, step["xpath"])
                    driver.execute_script("arguments[0].click();", element)
                # element.click()

                record_page_object_details(page_name, action, obj,
                                                   '', '', '',
                                                   driver, input_param,
                                                   None, xp, inter_file,
                                                   '', '', relative_xpaths)

            elif action == "hover":
                page_name = crawler.extract_page_name(driver.current_url)
                obj = step['element']
                xp = step["xpath"]
                # Get relative XPaths

                # print(relative_xpaths)
                element = driver.find_element(By.XPATH, step["xpath"])
                relative_xpaths = generate_relative_xpath(driver, element)
                try:
                    actions = ActionChains(driver)
                    actions.move_to_element(element).perform()
                except:  # element = driver.find_element(By.XPATH, step["xpath"])
                    driver.execute_script("arguments[0].hover();", element)
                # element.click()

                record_page_object_details(page_name, action, obj,
                                                   '', '', '',
                                                   driver, input_param,
                                                   None, xp, inter_file,
                                                   '', '', relative_xpaths)

            elif action == "wait":
                driver.implicitly_wait(int(step["time"]))
            elif action == "switch_to_iframe":
                iframe = driver.find_element(By.XPATH, step["iframe_xpath"])
                obj = step['element']
                xp = step["iframe_xpath"]
                relative_xpaths = xp

                # print(relative_xpaths)
                driver.switch_to.frame(iframe)

                page_name = crawler.extract_page_name(driver.current_url)
                record_page_object_details(page_name, action, obj,
                                                   '', '', '',
                                                   driver, input_param,
                                                   None, xp, inter_file,
                                                   '', '', relative_xpaths)
            elif action == "select":
                try:
                    page_name = crawler.extract_page_name(driver.current_url)
                    obj = step['element']
                    test_data = step.get("option", step["element"])
                    xp = step["option_xpath"]
                    # Get relative XPaths

                    # print(relative_xpaths)
                    element = driver.find_element(By.XPATH, step["option_xpath"])
                    relative_xpaths = generate_relative_xpath(driver, element)
                    element.click()

                    record_page_object_details(page_name, action, obj,
                                                       test_data, '', '',
                                                       driver, input_param,
                                                       None, xp, inter_file,
                                                       '', '', relative_xpaths)
                except:
                    try:
                        page_name = crawler.extract_page_name(driver.current_url)
                        obj = step['element']
                        test_data = step.get("option", step["element"])
                        xp = step["xpath"]
                        # Get relative XPaths

                        # print(relative_xpaths)
                        element = driver.find_element(By.XPATH, step["xpath"])
                        relative_xpaths = generate_relative_xpath(driver, element)
                        element.click()

                        record_page_object_details(page_name, action, obj,
                                                           test_data, '', '',
                                                           driver, input_param,
                                                           None, xp, inter_file,
                                                           '', '', relative_xpaths)
                    except:
                        pass
            steps_performed += f"{action} {step['element']}\n"
            ready = False
            while not ready:
                ready = driver.execute_script("return document.readyState") == "complete"
                time.sleep(1)

        except Exception as e:
            # print(f"Error performing step: {e}")
            action = step["action"]
            if action == "select":
                steps_not_performed += f"{action} {step['element']} as option :{step['option']} with xpath: {xp}, "
            elif action == "enter":
                steps_not_performed += f"{action} {step['element']} as :{step['text']} with xpath: {xp}, "
            else:
                steps_not_performed += f"{action} {step['element']} with xpath: {xp}, "
            status = -1
            ready = False
            while not ready:
                ready = driver.execute_script("return document.readyState") == "complete"
                time.sleep(1)

        # Check for URL changes and reinject MutationObserver if needed
        # current_url = driver.current_url
        # if current_url != previous_url:
        #     inject_mutation_observer(driver)
        #     previous_url = current_url

        # Check for new elements
        # new_elements = driver.execute_script("return window.newElements || [];")
        # if new_elements:
        #     print("New elements detected:", new_elements)

    return status, steps_performed, steps_not_performed

def record_page_object_details(page, action, obj, test_data, failed_msg, input_data, driver,
                               input_param, check_for_visible_element, xpath,
                               file_name, condition, condition_value, RelXpath):
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
            get_all_attrib_dict = driver.execute_script(
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
        locator, r_path = locator_priority(driver, priority_list, df, check_for_visible_element)
        # if RelXpath:
        #     df['locator'] = 'RelXpath'
        # else:
        df['Locator'] = 'RelXpath' if RelXpath else locator
        df['RelXpath'] = [RelXpath]
    filename = file_name
    df.to_csv(filename, mode='a', header=not os.path.isfile(filename), index=False)
    return True

def locator_priority(driver, priority_list, df, element):
    locator_list = {'ID': By.ID, 'Name': By.NAME, 'Class': By.CLASS_NAME, 'TagName': By.TAG_NAME,
                    'LinkText': By.LINK_TEXT, 'CssSelector_with_Class': By.CSS_SELECTOR,
                    'CssSelector_with_ID': By.CSS_SELECTOR,
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
                        check_for_visible_element = driver.find_element(locator_item, row[priority_list[item]])
                        if element == check_for_visible_element:
                            rel_xpath = generate_relative_xpath(driver,
                                                                check_for_visible_element)
                            if locator == 'Xpath':
                                locator = 'RelXpath'
                            break
                    except:
                        item += 1
            else:
                item += 1
    return locator, rel_xpath
