import json
import math
import time
from typing import List, Union, Dict
from urllib.parse import urljoin
import Levenshtein
import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class XpathBuilder:
    def __init__(self, xp):
        self.xpath = xp

    def calculate_distance(self, element1, element2):
        x1, y1 = element1.location['x'], element1.location['y']
        x2, y2 = element2.location['x'], element2.location['y']

        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return distance

    def create_xpath_from_link_text(self, soup, link_text, driver, action):
        """
        Takes BeautifulSoup, link text, and a Selenium webdriver as inputs and returns a list
        of XPath expressions to select elements that have the specified link text and are visible on the page.
        """
        new_handle=driver.window_handles[-1]
        driver.switch_to.window(new_handle)
        driver.switch_to.default_content()
        is_in_iframe = driver.execute_script("return window.self !== window.top")

        print('is_in_iframe: ', is_in_iframe)
        print('current_window_handle : ', driver.current_window_handle)
        found = False
        elements = []
        xpaths = []
        jspath = ''
        frame_id = ''
        #driver.switch_to.default_content()
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        time_breaker = 20 # change as per web app loading stats
        if is_in_iframe:
            time_breaker = 20 # since as observed, it takes time taken to load options, so for safer side added wait
        start = time.time()
        while not found:
            delta = time.time() - start
            if delta >= time_breaker:
                break
            elements = soup.find_all(text=lambda text: link_text in str(text))
            if elements:
                found = True
            else:
                soup = BeautifulSoup(driver.page_source, 'html.parser')
        if not elements and not is_in_iframe:
            iframes=soup.find_all("frame")

            for iframe in iframes:
                current_page_url = driver.current_url
                iframe_srcs = iframe.get("src")
                iframe_src = urljoin(current_page_url, iframe_srcs)
                getid=iframe.get("id")
                #driver.switch_to.frame(iframe)
                driver.switch_to.frame(getid)
                iframe_contents = driver.page_source
                page_content = ''.join(iframe_contents)
                # print(iframe_contents)
                is_in_iframe = driver.execute_script("return window.self !== window.top")
                print('iis_in_iframe: ', is_in_iframe)
                current_window_handle = driver.current_window_handle
                print('insider current_window_handle: ', current_window_handle)
                try:
                    start = time.time()
                    while not found:
                        delta = time.time() - start
                        if delta >= time_breaker:
                            break
                        if iframe_src:
                            iframe_response=requests.get(iframe_src)
                            iframe_soup=BeautifulSoup(iframe_response.content, "html.parser")

                            elements = iframe_soup.find_all(text=lambda text: link_text in str(text))
                        if not elements:
                            iframe_soup = BeautifulSoup(page_content, "html.parser")
                            elements = iframe_soup.find_all(text=lambda text: link_text in str(text))
                        if elements:
                            frame_id = getid
                            print('iframe search: ', elements)
                            found = True
                        else:
                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                        #driver.switch_to.default_content()
                except Exception as e:
                    print(f"Error while switching to iframe: {e}")
                finally:
                    driver.switch_to.default_content()
                if elements:
                    break
            if frame_id:
                driver.switch_to.frame(frame_id)
        for elem in elements:
            if elem.text == link_text:
                xpath_parts = []
                if link_text == 'Sign in':
                    actual_node=elem
                else:
                    actual_node = elem.parent
                # build the xpath by traversing the element's ancestors
                while elem.parent is not None:
                    # siblings = elem.parent.find_all(text=lambda text: link_text in str(text), recursive=False)

                    xpath_tag = elem.name if isinstance(elem, Tag) else ""
                    siblings = elem.parent.find_all(xpath_tag, recursive=False)
                    if len(siblings) > 1:
                        sibling_index = siblings.index(elem) + 1
                        xpath_parts.append(f"{xpath_tag}[{sibling_index}]")
                    else:
                        xpath_parts.append(xpath_tag)
                    elem = elem.parent
                xpath_parts.reverse()
                xpath = "/".join(xpath_parts)
                if not xpath.startswith('html/head/'):
                    final_xpath = xpath.rpartition("/")[0]
                    if driver.find_element(By.XPATH, final_xpath).is_displayed():
                       xpaths.append(xpath)
        if len(xpaths) == 0:
            for elem in elements:
                xpath_parts = []
                actual_node = elem.parent
                # build the xpath by traversing the element's ancestors
                while elem.parent is not None:
                    # siblings = elem.parent.find_all(text=lambda text: link_text in str(text), recursive=False)

                    xpath_tag = elem.name if isinstance(elem, Tag) else ""
                    siblings = elem.parent.find_all(xpath_tag, recursive=False)
                    if len(siblings) > 1:
                        sibling_index = siblings.index(elem) + 1
                        xpath_parts.append(f"{xpath_tag}[{sibling_index}]")
                    else:
                        xpath_parts.append(xpath_tag)
                    elem = elem.parent
                xpath_parts.reverse()
                xpath = "/".join(xpath_parts)
                if not xpath.startswith('html/head/'):
                    final_xpath = xpath.rpartition("/")[0]
                    if driver.find_element(By.XPATH, final_xpath).is_displayed():
                        xpaths.append(xpath)

        # return xpaths
        return xpaths, frame_id

    def create_xpath_from_link_text_without_prim(self, soup, link_text, driver):
        """
        Takes BeautifulSoup, link text, and a Selenium webdriver as inputs and returns a list
        of XPath expressions to select elements that have the specified link text and are visible on the page.
        """
        new_handle=driver.window_handles[-1]
        driver.switch_to.window(new_handle)
        driver.switch_to.default_content()
        is_in_iframe = driver.execute_script("return window.self !== window.top")

        print('is_in_iframe: ', is_in_iframe)
        print('current_window_handle : ', driver.current_window_handle)
        found = False
        elements = []
        xpaths = []
        frame_id = ''
        #driver.switch_to.default_content()
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        time_breaker = 30 # change as per web app loading stats
        if is_in_iframe:
            time_breaker = 30 # since as observed, it takes time taken to load options, so for safer side added wait
        start = time.time()
        while not found:
            delta = time.time() - start
            if delta >= time_breaker:
                break

            elements = soup.find_all(text=lambda text: link_text in str(text))

            if elements:
                found = True
            else:
                soup = BeautifulSoup(driver.page_source, 'html.parser')
        if not elements and not is_in_iframe:
            iframes=soup.find_all("frame")

            for iframe in iframes:
                current_page_url = driver.current_url
                iframe_srcs = iframe.get("src")
                iframe_src = urljoin(current_page_url, iframe_srcs)
                getid=iframe.get("id")
                #driver.switch_to.frame(iframe)
                driver.switch_to.frame(getid)
                iframe_contents = driver.page_source
                page_content = ''.join(iframe_contents)
                # print(iframe_contents)
                is_in_iframe = driver.execute_script("return window.self !== window.top")
                print('iis_in_iframe: ', is_in_iframe)
                current_window_handle = driver.current_window_handle
                print('insider current_window_handle: ', current_window_handle)
                try:
                    start = time.time()
                    while not found:
                        delta = time.time() - start
                        if delta >= time_breaker:
                            break
                        if iframe_src:
                            iframe_response=requests.get(iframe_src)
                            iframe_soup=BeautifulSoup(iframe_response.content, "html.parser")

                            elements = iframe_soup.find_all(text=lambda text: link_text in str(text))
                        if not elements:
                            iframe_soup = BeautifulSoup(page_content, "html.parser")

                            elements = iframe_soup.find_all(text=lambda text: link_text in str(text))
                        if elements:
                            frame_id = getid
                            print('iframe search: ', elements)
                            found = True
                        else:
                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                        #driver.switch_to.default_content()
                except Exception as e:
                    print(f"Error while switching to iframe: {e}")
                finally:
                    driver.switch_to.default_content()
                if elements:
                    break
            if frame_id:
                driver.switch_to.frame(frame_id)
        for elem in elements:
            if elem.text == link_text:
                xpath_parts = []
                actual_node = elem.parent
                # build the xpath by traversing the element's ancestors
                while elem.parent is not None:
                    # siblings = elem.parent.find_all(text=lambda text: link_text in str(text), recursive=False)

                    xpath_tag = elem.name if isinstance(elem, Tag) else ""
                    siblings = elem.parent.find_all(xpath_tag, recursive=False)
                    if len(siblings) > 1:
                        sibling_index = siblings.index(elem) + 1
                        xpath_parts.append(f"{xpath_tag}[{sibling_index}]")
                    else:
                        xpath_parts.append(xpath_tag)
                    elem = elem.parent
                xpath_parts.reverse()
                xpath = "/".join(xpath_parts)
                if not xpath.startswith('html/head/'):
                    final_xpath = xpath.rpartition("/")[0]
                    if driver.find_element(By.XPATH, final_xpath).is_displayed():
                       xpaths.append(xpath)
        if len(xpaths) == 0:
            for elem in elements:
                xpath_parts = []
                actual_node = elem.parent
                # build the xpath by traversing the element's ancestors
                while elem.parent is not None:
                    # siblings = elem.parent.find_all(text=lambda text: link_text in str(text), recursive=False)

                    xpath_tag = elem.name if isinstance(elem, Tag) else ""
                    siblings = elem.parent.find_all(xpath_tag, recursive=False)
                    if len(siblings) > 1:
                        sibling_index = siblings.index(elem) + 1
                        xpath_parts.append(f"{xpath_tag}[{sibling_index}]")
                    else:
                        xpath_parts.append(xpath_tag)
                    elem = elem.parent
                xpath_parts.reverse()
                xpath = "/".join(xpath_parts)
                if not xpath.startswith('html/head/'):
                    final_xpath = xpath.rpartition("/")[0]
                    if driver.find_element(By.XPATH, final_xpath).is_displayed():
                        xpaths.append(xpath)


        return xpaths, frame_id

    def create_releative_xpath_from_link_text(self, soup, link_text, main_object, driver):
        """
        Takes BeautifulSoup, link text, and a Selenium webdriver as inputs and returns a list
        of XPath expressions to select elements that have the specified link text and are visible on the page.
        """
        found = False
        found_main_object = False
        elements = []
        elements_main_object = []
        xpaths = []
        xpaths_main_object = []
        driver.switch_to.default_content()
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        soup_main_object = BeautifulSoup(driver.page_source, 'html.parser')
        time_breaker = 60
        start = time.time()
        while not found:
            delta = time.time() - start
            if delta >= time_breaker:
                return ''

            elements = soup.find_all(text=lambda text: main_object in str(text))
            if elements:
                found = True
            else:
                soup = BeautifulSoup(driver.page_source, 'html.parser')

        start = time.time()
        while not found_main_object:
            delta = time.time() - start
            if delta >= time_breaker:
                return ''
            elements_main_object = soup_main_object.find_all(text=lambda text: link_text in str(text))
            if elements_main_object:
                found_main_object = True
            else:
                soup_main_object = BeautifulSoup(driver.page_source, 'html.parser')

        for elem in elements:
            xpath_parts = []
            actual_node = elem.parent
            # build the xpath by traversing the element's ancestors
            while elem.parent is not None:
                # siblings = elem.parent.find_all(text=lambda text: link_text in str(text), recursive=False)

                xpath_tag = elem.name if isinstance(elem, Tag) else ""
                siblings = elem.parent.find_all(xpath_tag, recursive=False)
                if len(siblings) > 1:
                    sibling_index = siblings.index(elem) + 1
                    xpath_parts.append(f"{xpath_tag}[{sibling_index}]")
                else:
                    xpath_parts.append(xpath_tag)
                elem = elem.parent
            xpath_parts.reverse()
            xpath = "/".join(xpath_parts)
            if xpath.startswith('html/body'):
                xpaths.append(xpath)
        for elem in elements_main_object:
            xpath_parts = []
            actual_node = elem.parent
            # build the xpath by traversing the element's ancestors
            while elem.parent is not None:
                # siblings = elem.parent.find_all(text=lambda text: link_text in str(text), recursive=False)

                xpath_tag = elem.name if isinstance(elem, Tag) else ""
                siblings = elem.parent.find_all(xpath_tag, recursive=False)
                if len(siblings) > 1:
                    sibling_index = siblings.index(elem) + 1
                    xpath_parts.append(f"{xpath_tag}[{sibling_index}]")
                else:
                    xpath_parts.append(xpath_tag)
                elem = elem.parent
            xpath_parts.reverse()
            xpath = "/".join(xpath_parts)
            if xpath.startswith('html/body'):
                xpaths_main_object.append(xpath)
        final_xpath_of_main = str(xpaths[0]).rpartition("/")[0]
        check_for_visible_main = driver.find_element(By.XPATH, final_xpath_of_main)
        dist = 0
        final_xp = ''
        for xpath_of_sider in xpaths_main_object:
            final_xpath_of_sider = str(xpath_of_sider).rpartition("/")[0]
            check_for_visible_sider = driver.find_element(By.XPATH, final_xpath_of_sider)
            mark = XpathBuilder.calculate_distance(XpathBuilder, check_for_visible_main, check_for_visible_sider)
            if dist == 0:
                final_xp = final_xpath_of_sider
                dist = mark
            elif mark < dist:
                final_xp = final_xpath_of_sider
                dist = mark
        return final_xp

    def get_nearest_input(self, soup, link_text, driver, action):
        found = False
        elements = []
        xpaths = []
        # driver.switch_to.default_content()
        new_handle=driver.window_handles[-1]
        driver.switch_to.window(new_handle)
        driver.switch_to.default_content()

        time_breaker = 60
        start = time.time()
        while not found:
            delta = time.time() - start
            if delta >= time_breaker:
                return '', None
            content = driver.page_source
            new_page_content = ''.join(content)
            soup = BeautifulSoup(new_page_content,"html.parser")
            elements = soup.find_all(text=lambda text: link_text in str(text))
            # Rupesh changes for username
            if link_text == 'Username':
                elements = [elements[1]]
            if elements:
                check_if_any_have_link_text = False
                for elem in elements:
                    if elem.text.find(link_text) != -1:
                        check_if_any_have_link_text = True
                if check_if_any_have_link_text:
                    found = True
                else:
                    driver.switch_to.default_content()
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
            else:
                driver.switch_to.default_content()
                soup = BeautifulSoup(driver.page_source, 'html.parser')
        for elem in elements:
            if elem.text.find(link_text) != -1:
                xpath_parts = []
                # build the xpath by traversing the element's ancestors
                while elem.parent is not None:
                    # siblings = elem.parent.find_all(text=lambda text: link_text in str(text), recursive=False)

                    xpath_tag = elem.name if isinstance(elem, Tag) else ""
                    siblings = elem.parent.find_all(xpath_tag, recursive=False)
                    if len(siblings) > 1:
                        sibling_index = siblings.index(elem) + 1
                        xpath_parts.append(f"{xpath_tag}[{sibling_index}]")
                    else:
                        xpath_parts.append(xpath_tag)
                    elem = elem.parent
                xpath_parts.reverse()
                xpath = "/".join(xpath_parts)
                xpaths.append(xpath)
        # ll select the first one as default selection option
        for xp in xpaths:
            get_el_xp = str(xp).rpartition("/")[0]
            get_el = driver.find_element(By.XPATH, get_el_xp)
            # print('get_el: ', get_el)

        for act_el in elements:
            if act_el.text.strip() == link_text:
                actual_linktext_element = act_el

        if str(action).lower() == 'enter' or str(action).lower() == 'populate':
            in_el = actual_linktext_element.find_next('input')
        elif str(action).lower() == 'select':
            in_el = actual_linktext_element.find_next('select')
        link_text_element = str(xpaths[0]).rpartition("/")[0]
        lt_element = driver.find_element(By.XPATH, link_text_element)
        driver.execute_script("arguments[0].style.border='3px solid red'", lt_element)
        input_ele = driver.find_elements(By.TAG_NAME, 'input')
        # need to change above to get xpaths
        input_list = soup.find_all('input')
        kb_attr_list = ['id', 'name', 'placeholder', 'value', 'title', 'type', 'class']
        distance = 0
        actual_in = None
        rxp = ''
        final_xpath_of_in = XpathBuilder.generate_xpath(XpathBuilder, soup, in_el, driver)
        check_for_visible_element = driver.find_element(By.XPATH, final_xpath_of_in)
        if XpathBuilder.is_element_interactable(XpathBuilder, driver, check_for_visible_element):
            mark = XpathBuilder.calculate_distance(XpathBuilder, lt_element, check_for_visible_element)
            # driver.execute_script("arguments[0].style.border='3px solid red'", inp)
            if distance == 0:
                distance = mark
                actual_in = check_for_visible_element
                rxp = final_xpath_of_in
            elif mark < distance:
                distance = mark
                actual_in = check_for_visible_element
                rxp = final_xpath_of_in
            # print('distance: ', mark)
        print("Xpath: ", final_xpath_of_in)
        # for in_el in input_list:
        #     final_xpath_of_in = XpathBuilder.generate_xpath(XpathBuilder, soup, in_el, driver)
        #     check_for_visible_element = driver.find_element(By.XPATH, final_xpath_of_in)
        #     if XpathBuilder.is_element_interactable(XpathBuilder, driver, check_for_visible_element):
        #         mark = XpathBuilder.calculate_distance(XpathBuilder, lt_element, check_for_visible_element)
        #         # driver.execute_script("arguments[0].style.border='3px solid red'", inp)
        #         if distance == 0:
        #             distance = mark
        #             actual_in = check_for_visible_element
        #             rxp = final_xpath_of_in
        #         elif mark < distance:
        #             distance = mark
        #             actual_in = check_for_visible_element
        #             rxp = final_xpath_of_in
        #         print('distance: ', mark)
        #     print("generated xp: ", final_xpath_of_in)
        #       Keep below code for future reference
        # if (not input_ele.has_attr("type")) or (input_ele.has_attr("type") and input_ele['type'] != "hidden"):
        #     for attr in kb_attr_list:
        #         if input_ele.has_attr(attr):
        #             locator = XpathBuilder.calc_xpath(XpathBuilder, 'input', attr, input_ele)
        #             print(attr, ":", locator)

        driver.execute_script("arguments[0].style.border='3px solid red'", actual_in)
        return rxp, actual_in

    def is_element_interactable(self, driver, by_locator, timeout=10):
        try:
            WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(by_locator))
            return True
        except (TimeoutException, ElementNotInteractableException):
            return False

    def calc_xpath(self, tag, attr, element):
        if type(element[attr]) is list:
            element[attr] = [i.encode('utf-8').decode('latin-1') for i in element[attr]]
            element[attr] = ' '.join(element[attr])
            xpath = "//%s[@%s='%s']" % (tag, attr, element[attr])
            return xpath

    def generate_xpath(self, soup, elem, driver):
        # driver.switch_to.default_content()
        # soup = BeautifulSoup(driver.page_source, 'html.parser')
        xpath_parts = []
        # build the xpath by traversing the element's ancestors
        while elem.parent is not None:
            # siblings = elem.parent.find_all(text=lambda text: link_text in str(text), recursive=False)

            xpath_tag = elem.name if isinstance(elem, Tag) else ""
            siblings = elem.parent.find_all(xpath_tag, recursive=False)
            if len(siblings) > 1:
                sibling_index = siblings.index(elem) + 1
                xpath_parts.append(f"{xpath_tag}[{sibling_index}]")
            else:
                xpath_parts.append(xpath_tag)
            elem = elem.parent
        xpath_parts.reverse()
        xpath = "/".join(xpath_parts)
        return xpath

    def generate_relative_xpath(self, driver, element):
        ele = element
        id_name = element.get_attribute('id')
        placeholder = element.get_attribute('placeholder')
        name = element.get_attribute('name')
        if id_name:
            xpath = f"//{element.tag_name}[@id='{id_name}']"
        elif name:
            xpath = f"//{element.tag_name}[@name='{name}']"
        elif placeholder:
            xpath = f"//{element.tag_name}[@name='{name}']"
        else:
            found = False
            while not found:
                xpath_segments = []
                # Traverse up the DOM hierarchy
                while element.tag_name != 'html':
                    # Get the attributes of the current element
                    attributes = driver.execute_script(
                        'var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index)'
                        '{ items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value; }; return items;',
                        element)
                    if attributes:
                        # Check if any combination of attributes is unique
                        for attr_name, attr_value in attributes.items():
                            if attr_name == 'style' or attr_name == 'value':
                                pass
                            else:
                                xpath = f"//{element.tag_name}[@{attr_name}='{attr_value}']"
                                if len(driver.find_elements(By.XPATH, xpath)) == 1:
                                    xpath_segment = f"//{element.tag_name}[@{attr_name}='{attr_value}']"
                                    xpath_segments.insert(0, xpath_segment)
                                    break
                        xpath = '//'.join(xpath_segments)
                        try:
                            elements = driver.find_elements(By.XPATH, xpath)
                            if len(elements) == 1:
                                found = True
                                break
                            else:
                                raise Exception('Elements is empty')
                        except:
                            # Move up to the parent element
                            xpath_segments.insert(0, element.tag_name)

                            if xpath_segments:
                                # xpath_segments.insert(0, '/')
                                xpath = '//'.join(xpath_segments)
                                xpath = '//' + xpath + f"[contains(text(),'{ele.text}')]"
                                elements = driver.find_elements(By.XPATH, xpath)
                                if len(elements) == 1:
                                    found = True
                                    break
                                else:
                                    xpath = '//'.join(xpath_segments)
                                    if element.parent is not None:
                                        sibling_index = len(element.find_elements(By.XPATH,
                                                                                  f"preceding-sibling::{element.tag_name}")) + 1
                                        xpath_segments[0] = f"{element.tag_name}[{sibling_index}]"
                                        xpath = '//'.join(xpath_segments)
                                        xpath = '//' + xpath
                                        elements = driver.find_elements(By.XPATH, xpath)
                                        if len(elements) == 1:
                                            found = True
                                            break
                                        else:
                                            pass
                            element = element.find_element(By.XPATH, './..')
                    else:
                        xpath_segments.insert(0, element.tag_name)
                        xpath = '//'.join(xpath_segments)
                        xpath = '//' + xpath + f"[contains(text(),'{ele.text}')]"
                        elements = driver.find_elements(By.XPATH, xpath)
                        if len(elements) == 1:
                            found = True
                            break
                        else:
                            if element.parent is not None:
                                sibling_index = len(
                                    element.find_elements(By.XPATH, f"preceding-sibling::{element.tag_name}")) + 1
                                xpath_segments[0] = f"{element.tag_name}[{sibling_index}]"
                                xpath = '//'.join(xpath_segments)
                                xpath = '//' + xpath
                                elements = driver.find_elements(By.XPATH, xpath)
                                if len(elements) == 1:
                                    found = True
                                    break
                                else:
                                    pass
                        # Move up to the parent element
                        element = element.find_element(By.XPATH, './..')
        return xpath

    def process_dom_with_js_path(self, driver, element_name, action):
        try:

            serialize_dom_script = """
       function getJSPath(element) {
        if (element.tagName.toLowerCase() === 'html') {
            return 'document.documentElement';
        }
        if (element === document.body) {
            return 'document.body';
        }

        let path = [];
        while (element) {
            let subSelector = element.localName;
            if (element.id) {
                subSelector += `#${element.id}`;
            } else {
                let sibling = element;
                let nth = 1;
                while (sibling = sibling.previousElementSibling) {
                    if (sibling.localName === element.localName) nth++;
                }
                if (nth !== 1) subSelector += `:nth-of-type(${nth})`;
            }
            path.unshift(subSelector);
            element = element.parentNode;
            if (element instanceof ShadowRoot) {
                path.unshift('shadowRoot');
                element = element.host;
            }
        }

        let jspath = 'document';
        let shadowRootIndex = path.indexOf('shadowRoot');
        while (shadowRootIndex !== -1) {
            jspath += `.querySelector("${path.slice(0, shadowRootIndex).join(' > ')}").shadowRoot`;
            path = path.slice(shadowRootIndex + 1);
            shadowRootIndex = path.indexOf('shadowRoot');
        }
        jspath += `.querySelector("${path.join(' > ')}")`;
        return jspath.replace('document.querySelector(" > html > body', 'document.querySelector("body');
    }

    function getElementDetails(element) {
        let name = element.textContent.trim().replace(/\s+/g, ' ') || element.getAttribute('label') || element.getAttribute('placeholder') || element.getAttribute('text') || element.getAttribute('name') || element.getAttribute('value') || (element.innerText ? element.innerText.trim() : '');
        let tagName = element.tagName.toLowerCase();
        return { name, tagName };
    }

    function traverseShadowDOM(element, paths) {
        if (element.shadowRoot) {
            const shadowElements = element.shadowRoot.querySelectorAll('*');
            shadowElements.forEach(shadowElement => {
                const jspath = getJSPath(shadowElement);
                const details = getElementDetails(shadowElement);
                if (details.name && details.tagName !== 'style') {
                    paths.push({ jspath, ...details });
                }
                // Recursively get paths for nested shadow elements
                traverseShadowDOM(shadowElement, paths);
            });
        }
    }

    function getAllJSPaths() {
        const elements = document.body.querySelectorAll('*');
        const paths = [];
        elements.forEach(element => {
            const jspath = getJSPath(element);
            const details = getElementDetails(element);
            if (details.name && details.tagName !== 'style') {
                paths.push({ jspath, ...details });
            }
            traverseShadowDOM(element, paths);
        });
        return paths;
    }

    const shadowElements = getAllJSPaths();
    return JSON.stringify(shadowElements);

    """
            serialized_dom = driver.execute_script(serialize_dom_script)
            # Check if serialized_dom is None
            if not serialized_dom:
                print("Serialized DOM is None")
            elements = json.loads(serialized_dom)
            threshold = 3  # Define a threshold for acceptable distance
            matching_elements = sorted(elements, key=lambda element: Levenshtein.distance(element_name.lower(),
                                                                                          element['name'].lower()))
            matching_elements = [element for element in matching_elements if
                                 Levenshtein.distance(element_name.lower(), element['name'].lower()) <= threshold]

            # Prioritize elements based on action
            if action == 'Click':
                button_elements = [element for element in matching_elements if element['tagName'].lower() == 'button']
                if not button_elements:
                    # If no exact 'button' elements are found, include elements with 'button' in the tag name or other interactable tags
                    related_tag_names = ['a', 'div', 'span']  # Add more tag names as needed
                    matching_elements = sorted(matching_elements, key=lambda element: (
                    not any(tag in element['tagName'].lower() for tag in related_tag_names),
                    Levenshtein.distance(element_name.lower(), element['name'].lower())))
                else:
                    matching_elements = button_elements
            elif action in ['Enter', 'Populate', 'Upload']:
                input_elements = sorted(matching_elements,
                                        key=lambda element: (element['tagName'].lower() != 'input',
                                                             Levenshtein.distance(element_name.lower(),
                                                                                  element['name'].lower())))
                if not input_elements:
                    # If no elements with 'input' in tag name are found, include elements with related tag names
                    related_tag_names = ['input', 'textarea', 'select']  # Add more tag names as needed
                    matching_elements = sorted(matching_elements, key=lambda element: (
                        not any(tag in element['tagName'].lower() for tag in related_tag_names),
                        Levenshtein.distance(element_name.lower(), element['name'].lower())))
                else:
                    matching_elements = input_elements
            # Collect JS paths of matching elements
            results = [element['jspath'] for element in matching_elements]
            return results[0]
        except:
            pass