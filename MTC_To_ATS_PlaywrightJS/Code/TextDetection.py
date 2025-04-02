import io
import cv2
import time
import base64
import easyocr
import pandas as pd
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


def full_page_screenshot(driver):
    # Wait until the page is fully loaded
    WebDriverWait(driver, 200).until(ec.presence_of_element_located((By.TAG_NAME, "body")))
    scroll_pause_time = 30
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)  # Adjust sleep time if necessary
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Set the window size to the full height of the page
    total_width = driver.execute_script("return document.body.scrollWidth")
    total_height = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(total_width, total_height)

    # Activate the Chrome DevTools Protocol
    driver.execute_cdp_cmd('Page.enable', {})
    result = driver.execute_cdp_cmd('Page.captureScreenshot', {'format': 'png', 'fromSurface': True})

    # Decode the base64 data and save the image
    image = Image.open(io.BytesIO(base64.b64decode(result['data'])))
    image.save("../Data/Full_Page_Screenshot.png")
    ss = cv2.imread("../Data/Full_Page_Screenshot.png")
    return ss


def extract_text(image_file):
    data = []
    reader = easyocr.Reader(['en'], gpu=False)
    results = reader.readtext(image_file)
    for result in results:
        text, bbox = result[1], result[0]
        x0, y0 = bbox[0]
        x1, y1 = bbox[2]
        top_left = (x0, y0)
        bottom_right = (x1, y1)
        data.append([text, top_left, bottom_right])
    return data


def fullpageOCR(driver):
    screenshot = full_page_screenshot(driver)
    data = extract_text(screenshot)
    df = pd.DataFrame(data, columns=['Extracted Text', 'Top Left', 'Bottom Right'])
    df.drop_duplicates()
    return df
