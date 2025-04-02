from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

def get_element_xpath(driver, element):
    return driver.execute_script("""
        function getElementXPath(elt) {
            var path = "";
            for (; elt && elt.nodeType == 1; elt = elt.parentNode) {
                idx = getElementIdx(elt);
                xname = elt.tagName;
                if (idx > 1)
                    xname += "[" + idx + "]";
                path = "/" + xname + path;
            }
            return path.toLowerCase();
        }

        function getElementIdx(elt) {
            var count = 1;
            for (var sib = elt.previousSibling; sib; sib = sib.previousSibling) {
                if (sib.nodeType == 1 && sib.tagName == elt.tagName)
                    count++;
            }
            return count;
        }

        return getElementXPath(arguments[0]);
    """, element)

def get_iframe_details(driver):
    all_details = []

    def process_iframe(driver, iframe, parent_xpath):
        iframe_xpath = get_element_xpath(driver, iframe)
        driver.switch_to.frame(iframe)
        current_xpath = parent_xpath + [iframe_xpath]

        elements = driver.find_elements(By.XPATH, "//*")
        for element in elements:
            try:
                rect = element.rect
                if rect['width'] > 0 and rect['height'] > 0:
                    xpath = get_element_xpath(driver, element)
                    tag_name = element.tag_name
                    element_text = element.text.strip() if element.text.strip() else element.get_attribute('title')
                    coordinates = {
                        'x': rect['x'],
                        'y': rect['y'],
                        'width': rect['width'],
                        'height': rect['height'],
                        'center_x': rect['x'] + rect['width'] / 2,
                        'center_y': rect['y'] + rect['height'] / 2
                    }
                    all_details.append({
                        'tagName': "iframe -> " + tag_name,
                        'iframe_xpath': current_xpath,
                        'xpath': xpath,
                        'element': element_text,
                        'coordinates': coordinates
                    })
            except StaleElementReferenceException:
                continue

        nested_iframes = driver.execute_script("return Array.from(document.getElementsByTagName('iframe'));")
        for nested_iframe in nested_iframes:
            process_iframe(driver, nested_iframe, current_xpath)

        driver.switch_to.parent_frame()

    top_level_iframes = driver.execute_script("return Array.from(document.getElementsByTagName('iframe'));")
    for iframe in top_level_iframes:
        process_iframe(driver, iframe, [])

    return all_details

def inject_html_context_retrieval(driver):
    js_script = """
        try {
            return (function() {
                function extractDetails() {
                    const generateXPath = (element) => {
                        if (!element) return '';
                        if (element === document.body) {
                            return '/html/body';
                        }
                        let index = 0;
                        let sibling = element.previousElementSibling;
                        while (sibling) {
                            if (sibling.nodeName === element.nodeName) {
                                index++;
                            }
                            sibling = sibling.previousElementSibling;
                        }
                        const tagName = element.nodeName.toLowerCase();
                        const nth = index ? `[${index + 1}]` : '';
                        return `${generateXPath(element.parentNode)}/${tagName}${nth}`;
                    };

                    const isValidXPath = (xpath) => {
                        try {
                            document.evaluate(xpath, document, null, XPathResult.ANY_TYPE, null);
                            return true;
                        } catch (e) {
                            return false;
                        }
                    };

                    const cleanTextContent = (text) => {
                        return text.replace(/\\s+/g, ' ').trim();
                    };

                    const allElements = document.querySelectorAll('*');
                    const elementMap = new Map();

                    allElements.forEach((element) => {
                        const tagName = element.tagName.toLowerCase();

                        if (['div', 'script', 'style'].includes(tagName)) {
                            return;
                        }

                        let label = cleanTextContent(element.innerText || element.textContent || '');
                        const elementXPath = generateXPath(element);
                        const rect = element.getBoundingClientRect();

                        if (['html', 'body'].includes(tagName) && label.length > 100) {
                            return;
                        }

                        if (tagName === 'label') {
                            const associatedElement = element.querySelector('input, select, textarea');
                            if (associatedElement) {
                                const associatedXPath = generateXPath(associatedElement);
                                if (isValidXPath(associatedXPath)) {
                                    elementMap.set(associatedXPath, {
                                        tagName: associatedElement.tagName.toLowerCase(),
                                        xpath: associatedXPath,
                                        element: cleanTextContent(element.innerText.trim()),
                                        coordinates: {
                                            x: rect.x,
                                            y: rect.y,
                                            width: rect.width,
                                            height: rect.height,
                                            center_x: rect.x + rect.width / 2,
                                            center_y: rect.y + rect.height / 2
                                        }
                                    });
                                }
                            }
                        } else if (tagName === 'select') {
                            const parentLabel = element.closest('label') ? cleanTextContent(element.closest('label').innerText.split('\\n')[0].trim()) : cleanTextContent(label.split('\\n')[0].trim());
                            if (isValidXPath(elementXPath)) {
                                elementMap.set(elementXPath, {
                                    tagName: tagName,
                                    xpath: elementXPath,
                                    element: parentLabel,
                                    coordinates: {
                                        x: rect.x,
                                        y: rect.y,
                                        width: rect.width,
                                        height: rect.height,
                                        center_x: rect.x + rect.width / 2,
                                        center_y: rect.y + rect.height / 2
                                    }
                                });
                            }
                            Array.from(element.options).forEach((option, index) => {
                                const optionRect = option.getBoundingClientRect();
                                const optionXPath = `${elementXPath}/option[${index + 1}]`;
                                if (isValidXPath(optionXPath)) {
                                    elementMap.set(`${elementXPath}${optionXPath}`, {
                                        tagName: 'option',
                                        element: `${parentLabel}: ${cleanTextContent(option.text)}`,
                                        xpath: optionXPath,
                                        coordinates: {
                                            x: optionRect.x,
                                            y: optionRect.y,
                                            width: optionRect.width,
                                            height: optionRect.height,
                                            center_x: optionRect.x + optionRect.width / 2,
                                            center_y: optionRect.y + optionRect.height / 2
                                        }
                                    });
                                }
                            });
                        } else if (tagName === 'input' && element.type === 'radio') {
                            const radioWrapper = element.closest('label');
                            const associatedLabel = radioWrapper ? radioWrapper.textContent : '';
                            label = cleanTextContent(associatedLabel);
                            if (isValidXPath(elementXPath)) {
                                elementMap.set(elementXPath, {
                                    tagName: tagName,
                                    xpath: elementXPath,
                                    element: label,
                                    coordinates: {
                                        x: rect.x,
                                        y: rect.y,
                                        width: rect.width,
                                        height: rect.height,
                                        center_x: rect.x + rect.width / 2,
                                        center_y: rect.y + rect.height / 2
                                    }
                                });
                            }
                        } else {
                        if (!label) {
                            label = element.getAttribute('aria-label') || element.getAttribute('placeholder') || element.getAttribute('name') || element.getAttribute('title') || element.getAttribute('value') || '';
                        } else {
                            // Concatenate text content of parent element if it contains a <b> tag
                            const parentElement = element.closest('div');
                            if (parentElement && parentElement.querySelector('b')) {
                                label = cleanTextContent(parentElement.textContent);
                            }
                        }
                            if (isValidXPath(elementXPath) && (!elementMap.has(elementXPath) || (elementMap.has(elementXPath) && label))) {
                                elementMap.set(elementXPath, {
                                    tagName: tagName,
                                    xpath: elementXPath,
                                    element: label,
                                    coordinates: {
                                        x: rect.x,
                                        y: rect.y,
                                        width: rect.width,
                                        height: rect.height,
                                        center_x: rect.x + rect.width / 2,
                                        center_y: rect.y + rect.height / 2
                                    }
                                });
                            }
                        }

                        // Ensure all buttons are added to the elementMap
                        if (tagName === 'button') {
                            elementMap.set(elementXPath, {
                                tagName: tagName,
                                xpath: elementXPath,
                                element: label,
                                coordinates: {
                                    x: rect.x,
                                    y: rect.y,
                                    width: rect.width,
                                    height: rect.height,
                                    center_x: rect.x + rect.width / 2,
                                    center_y: rect.y + rect.height / 2
                                }
                            });
                        }

                        // Handle special characters
                        if (['span', 'a'].includes(tagName) && element.style.fontFamily) {
                            const parentElement = element.closest('a');
                            const title = parentElement ? parentElement.getAttribute('title') : '';
                            const ariaLabel = parentElement ? parentElement.getAttribute('aria-label') : '';
                            label = `${title || ariaLabel}`.trim();
                            if (isValidXPath(elementXPath)) {
                                elementMap.set(elementXPath, {
                                    tagName: tagName,
                                    xpath: elementXPath,
                                    element: label,
                                    coordinates: {
                                        x: rect.x,
                                        y: rect.y,
                                        width: rect.width,
                                        height: rect.height,
                                        center_x: rect.x + rect.width / 2,
                                        center_y: rect.y + rect.height / 2
                                    }
                                });
                            }
                        }
                    });

                    // Assign nearest label's main text to input elements if their text is empty
                    elementMap.forEach((value, key) => {
                        if (value.tagName === 'input' && !value.element) {
                            const labelElement = document.evaluate(`${key}/preceding::label[1]`, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                            if (labelElement) {
                                const labelText = labelElement.querySelector('span[id$="-label"]') ? cleanTextContent(labelElement.querySelector('span[id$="-label"]').innerText.trim()) : cleanTextContent(labelElement.innerText.trim());
                                if (labelText) {
                                    value.element = labelText;
                                }
                            }
                        }
                    });

                    const filteredElements = Array.from(elementMap.values()).reduce((acc, element) => {
                if (element.tagName === 'input') {
                    acc.push(element);
                    return acc;
                }
                const existingElement = acc.find(e => e.element === element.element && e.xpath.startsWith(element.xpath.slice(0, Math.floor(element.xpath.length * 0.9))));
                if (existingElement) {
                    if (element.xpath.length > existingElement.xpath.length) {
                        acc = acc.filter(e => e !== existingElement);
                        acc.push(element);
                    }
                } else {
                    acc.push(element);
                }
                return acc;
            }, []);

            const uniqueElements = filteredElements.map((element) => {
                const elements = document.evaluate(element.xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                if (elements.snapshotLength > 1) {
                    for (let i = 0; i < elements.snapshotLength; i++) {
                        const el = elements.snapshotItem(i);
                        if (el.innerText.trim() === element.element) {
                            element.xpath = `${element.xpath}[${i + 1}]`;
                            break;
                        }
                    }
                }
                return element;
            });

            const finalElements = uniqueElements.filter((element, index, self) => {
                if (element.tagName === 'button' || element.tagName === 'a' || element.tagName === 'input') {
                    return true;
                }
                return !self.some((e) => e.xpath.startsWith(element.xpath) && e.xpath !== element.xpath);
            });

            console.log('Final Elements:', finalElements);
            return finalElements;
        }
        return extractDetails();
    })();
        } catch (error) {
            return {error: error.message};
        }
        """
    details = driver.execute_script(js_script)
    return details

def inject_mutation_observer(driver):
    observer_script = """
    (function() {
  function generateXPath(element) {
    if (!element) return '';
    if (element === document.body) {
      return '/html/body';
    }

    let index = 1;
    let sibling = element.previousElementSibling;
    while (sibling) {
      if (sibling.nodeName === element.nodeName) {
        index++;
      }
      sibling = sibling.previousElementSibling;
    }
    const tagName = element.nodeName.toLowerCase();
    return `${generateXPath(element.parentNode)}/${tagName}[${index}]`;
  }

  function processNode(node) {
    const rect = node.getBoundingClientRect();
    let elementName = node.getAttribute('aria-label') || node.getAttribute('alt') || node.getAttribute('title') || node.tagName.toLowerCase();

    if (node.tagName.toLowerCase() === 'input' || node.tagName.toLowerCase() === 'textarea') {
      elementName = node.getAttribute('placeholder') || node.getAttribute('aria-label') || node.getAttribute('alt') || node.getAttribute('title') || '';
      const label = node.closest('label') || document.querySelector(`label[for="${node.id}"]`);
      if (label) {
        elementName = label.innerText || elementName;
      }
    } else if (node.tagName.toLowerCase() === 'button') {
      elementName = node.getAttribute('aria-label') || node.getAttribute('alt') || node.getAttribute('title') || node.innerText || '';
    }

    return {
      tagName: node.tagName.toLowerCase(),
      xpath: generateXPath(node),
      element: elementName.trim(),
      coordinates: {
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height,
        center_x: rect.x + rect.width / 2,
        center_y: rect.y + rect.height / 2
      }
    };
  }

  function getAllElements(node) {
    const interactableTags = ['button', 'a', 'input', 'textarea', 'select', 'option', 'label'];
    const elements = [];
    if (node.nodeType === 1 && interactableTags.includes(node.tagName.toLowerCase())) {
      elements.push(processNode(node));
    }
    node.querySelectorAll(interactableTags.join(',')).forEach(child => {
      elements.push(processNode(child));
    });
    return elements;
  }

  function extractAllElements() {
    const allElements = [];
    document.querySelectorAll('*').forEach(node => {
      allElements.push(...getAllElements(node));
    });
    return allElements;
  }

  const observer = new MutationObserver((mutations) => {
    const newElements = [];
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        setTimeout(() => {
          newElements.push(...getAllElements(node));
        }, 100); // Adjust the delay as needed
      });
    });

    setTimeout(() => {
      if (newElements.length > 20) {
        const allElements = extractAllElements();
        console.log('All Elements:', JSON.stringify(allElements, null, 2));
        window.newElements = allElements;
      } else if (newElements.length > 0) {
        console.log('New Elements:', JSON.stringify(newElements, null, 2));
        window.newElements = newElements;
      }
    }, 150); // Adjust the delay as needed
  });

  observer.observe(document.body, { childList: true, subtree: true, attributes: true, characterData: true });
})();

"""
    driver.execute_script(observer_script)
def generate_relative_xpath(driver, element):
    id_name = element.get_attribute('id')
    placeholder = element.get_attribute('placeholder')
    name = element.get_attribute('name')

    # Try to get the most specific and reliable attribute first
    if id_name:
        return f"//{element.tag_name}[@id='{id_name}']"
    elif name:
        return f"//{element.tag_name}[@name='{name}']"
    elif placeholder:
        return f"//{element.tag_name}[@placeholder='{placeholder}']"

    # If no unique attributes found, start traversing up the DOM
    xpath_segments = []
    while element.tag_name != 'html':
        # Get the attributes of the current element
        attributes = driver.execute_script(
            'var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) '
            '{ items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value; }; return items;',
            element)

        for attr_name, attr_value in attributes.items():
            if attr_name in ['style', 'value']:  # Skip style and value attributes
                continue
            xpath = f"//{element.tag_name}[@{attr_name}='{attr_value}']"

            # Wait for the element to be present and check if it's the right one
            if wait_for_element(driver, xpath):
                # Now check if exactly one element matches the XPath
                elements = driver.find_elements(By.XPATH, xpath)
                if len(elements) == 1:  # Ensure exactly one matching element is found
                    xpath_segments.insert(0, xpath)
                    break

        # If no suitable xpath found, move to the parent element
        if not xpath_segments:
            element = element.find_element(By.XPATH, './..')
        else:
            break

    return '//' + '/'.join(xpath_segments)


def wait_for_element(driver, xpath, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return True
    except:
        return False