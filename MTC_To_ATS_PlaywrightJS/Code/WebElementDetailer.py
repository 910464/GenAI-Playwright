import json
import pandas as pd
from selenium.webdriver.common.by import By


def inject_js_functions(driver):
    script = """
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

        function getTextElementsInParent() {
            var elements = document.querySelectorAll('*');
            var details = [];
            var textElementsMap = new Map(); // To keep track of text elements by parent XPath

            function addElementDetails(elt) {
                var style = window.getComputedStyle(elt);
                var rect = elt.getBoundingClientRect();
                var hasTextContent = elt.innerText && elt.innerText.trim().length > 0;

                if (rect.width > 0 && rect.height > 0 && hasTextContent) {
                    var parentXPath = getElementXPath(elt.parentNode);
                    if (!textElementsMap.has(parentXPath)) {
                        textElementsMap.set(parentXPath, []);
                    }
                    textElementsMap.get(parentXPath).push(elt.innerText.trim());
                    details.push({
                        text: elt.innerText.trim(),                 
                        xpath: getElementXPath(elt),                 
                        coordinates: {                     
                            x: rect.left,                     
                            y: rect.top,                     
                            width: rect.width,                     
                            height: rect.height                 
                        },             
                        parentXPath: parentXPath
                    });
                }
            }

            for (var i = 0; i < elements.length; i++) {             
                addElementDetails(elements[i]);
            }

            var textByParentXPath = Array.from(textElementsMap).map(([parentXPath, texts]) => ({
                parentXPath: parentXPath,
                texts: texts
            }));

            return { details: details, textByParentXPath: textByParentXPath };
        }  
        window.getElementXpath = getElementXPath   
        return JSON.stringify(getTextElementsInParent());
    """
    return json.loads(driver.execute_script(script))


def handle_nested_iframes(driver, parent_texts):
    all_details = []

    def process_iframe(driver, iframe, parent_xpath):
        iframe_xpath = driver.execute_script("return window.getElementXpath(arguments[0]);", iframe)
        driver.switch_to.frame(iframe)
        current_xpath = parent_xpath + [iframe_xpath]
        frame_data = inject_js_functions(driver)
        frame_details = frame_data['details']
        text_by_parent_xpath = frame_data['textByParentXPath']

        # Merge the iframe-specific parent texts with the global parent texts
        for item in text_by_parent_xpath:
            if item['parentXPath'] in parent_texts:
                parent_texts[item['parentXPath']].extend(item['texts'])
            else:
                parent_texts[item['parentXPath']] = item['texts']

        for detail in frame_details:
            detail['xpath'] = current_xpath + [detail['xpath']]
            detail['parentXPath'] = iframe_xpath  # Use iframe's XPath as the parent for inner elements

        all_details.extend(frame_details)

        nested_iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        for nested_iframe in nested_iframes:
            process_iframe(driver, nested_iframe, current_xpath)

        driver.switch_to.parent_frame()

    top_level_iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    for iframe in top_level_iframes:
        process_iframe(driver, iframe, [])

    return all_details, parent_texts


def fullpageJS(driver):
    data = []
    elements = inject_js_functions(driver)
    parent_texts = {item['parentXPath']: item['texts'] for item in elements['textByParentXPath']}
    iframe_details, iframe_texts = handle_nested_iframes(driver, parent_texts)

    for element in elements['details']:
        text = element['text']
        xpath = element['xpath']
        x, y = element['coordinates']['x'], element['coordinates']['y']
        width, height = element['coordinates']['width'], element['coordinates']['height']
        top_left = (x, y)
        bottom_right = (x + width, y + height)
        parent_xpath = element['parentXPath']
        texts_in_parent = parent_texts.get(parent_xpath, [])
        data.append([text, xpath, top_left, bottom_right, texts_in_parent])

    for element in iframe_details:
        text = element['text']
        xpath_list = element['xpath']
        xpath = ' -> '.join(xpath_list)
        x, y = element['coordinates']['x'], element['coordinates']['y']
        width, height = element['coordinates']['width'], element['coordinates']['height']
        top_left = (x, y)
        bottom_right = (x + width, y + height)
        parent_xpath = element['parentXPath']
        texts_in_parent = parent_texts.get(parent_xpath, [])
        data.append([text, xpath, top_left, bottom_right, texts_in_parent])

    df = pd.DataFrame(data, columns=['Extracted Text', 'Extracted Xpath', 'Top Left', 'Bottom Right',
                                     'Common Parent Elements'])
    df['XPath Length'] = df['Extracted Xpath'].apply(len)

    df = df[~df['Extracted Text'].str.contains('\n')]
    df = df.loc[df.groupby('Extracted Text')['XPath Length'].idxmax()]
    df.drop(columns=['XPath Length'], inplace=True)

    return df
