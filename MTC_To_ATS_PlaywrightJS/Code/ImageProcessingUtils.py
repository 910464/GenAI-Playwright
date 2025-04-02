import os.path
import time
from io import BytesIO

from PIL import Image


# Function to split the long images
def split_screenshot(source_image, x):
    # Open the source image
    source = Image.open(source_image)

    # Get the dimensions of the source image
    width, height = source.size

    if height > x:
        # Calculate the number of images based on the height and x value
        num_images = height // x

        # Calculate the height of the last piece
        last_piece_height = height % x

        # Create a list to store the generated images
        images = []

        # Iterate over the number of images
        for i in range(num_images):
            # Calculate the starting and ending pixel coordinates for each piece
            start_y = i * x
            end_y = (i + 1) * x

            # Crop the piece from the source image
            piece = source.crop((0, start_y, width, end_y))

            # Add the cropped piece to the list of images
            images.append(piece)

        # Handle the last piece
        if last_piece_height >= x / 2:
            # Crop and add the last piece as a separate image
            start_y = num_images * x
            end_y = height
            last_piece = source.crop((0, start_y, width, end_y))
            images.append(last_piece)
        else:
            # Extend the second-to-last piece with the last piece
            second_last_piece = images[-1]
            second_last_piece.paste(source.crop((0, num_images * x, width, height)), (0, x - last_piece_height))

        # Return the generated images
        return images
    else:
        # Return the screenshots as such if its height is smaller than the default size
        return [source]


def stitch_screenshots_vertically(screenshot_list):
    # Calculate the total height and maximum width of the stitched image
    total_height = sum(screenshot.height for screenshot in screenshot_list)
    max_width = max(screenshot.width for screenshot in screenshot_list)

    # Create a new image with the maximum width and total height of the screenshots
    stitched_image = Image.new('RGB', (max_width, total_height))

    # Track the current y-coordinate for pasting the screenshots
    current_y = 0

    # Paste the screenshots onto the stitched image vertically
    for screenshot in screenshot_list:
        stitched_image.paste(screenshot, (0, current_y))
        current_y += screenshot.height

    return stitched_image


def custom_full_screenshot(driver, path):
    driver.maximize_window()
    driver.execute_script(f"window.scrollTo(0, {0});")

    # Get the total scroll height of the webpage
    scroll_height = driver.execute_script("return document.documentElement.scrollHeight")
    scroll_width = driver.execute_script("return document.documentElement.scrollWidth")
    inner_height = driver.execute_script("return window.innerHeight")
    outer_height = driver.execute_script("return window.outerHeight")
    outer_width = driver.execute_script("return window.outerWidth")
    print(inner_height)
    num_iterations = scroll_height // inner_height + 1

    screenshot_splits = []
    # Take screenshots iteratively
    for i in range(num_iterations):
        # Scroll to the end of innerHeight
        if scroll_height - i * inner_height < inner_height:
            driver.set_window_size(scroll_width + outer_width,
                                   scroll_height - inner_height * i + outer_height - inner_height)
        driver.execute_script(f"window.scrollTo(0, {inner_height * i});")

        # Capture screenshot
        screenshot_bytes = driver.get_screenshot_as_png()
        screenshot_i = Image.open(BytesIO(screenshot_bytes))

        size_script = '''
                var size = [window.innerHeight,window.innerWidth]
                return size
                '''
        [height, width] = driver.execute_script(size_script)

        resized_image = screenshot_i.resize((width, height))

        try:
            if resized_image.height < screenshot_splits[-1].height / 2:
                screenshot_splits[-1] = stitch_screenshots_vertically([screenshot_splits[-1], resized_image])
            else:
                screenshot_splits.append(resized_image)
        except:
            screenshot_splits.append(resized_image)

    driver.execute_script(f"window.scrollTo(0, {0});")
    driver.maximize_window()
    full_screenshot = stitch_screenshots_vertically(screenshot_splits)
    full_screenshot.save(path)


def take_headful_screenshots(driver, path, height, width):
    driver.maximize_window()

    # Get the total scroll height of the webpage
    scroll_height = driver.execute_script("return document.documentElement.scrollHeight")
    scroll_width = driver.execute_script("return document.documentElement.scrollWidth")
    inner_height = driver.execute_script("return window.innerHeight")
    inner_width = driver.execute_script("return window.innerWidth")
    outer_height = driver.execute_script("return window.outerHeight")
    outer_width = driver.execute_script("return window.outerWidth")
    print(inner_height)
    num_iterations = scroll_height // inner_height + 1

    screenshot_splits = []
    # Take screenshots iteratively
    for i in range(num_iterations):
        # Scroll to the end of innerHeight
        if scroll_height - i * inner_height < inner_height:
            driver.set_window_size(1297, scroll_height - inner_height * i + outer_height - inner_height)
        driver.execute_script(f"window.scrollTo(0, {inner_height * i});")

        # Capture screenshot
        screenshot_path = f"{path}/screenshot_part_{i}.png"
        driver.save_screenshot(screenshot_path)

        size_script = '''
        var size = [window.innerHeight,window.innerWidth]
        return size
        '''
        [height, width] = driver.execute_script(size_script)
        image = Image.open(screenshot_path)
        resized_image = image.resize((width, height))

        try:
            if resized_image.height < screenshot_splits[-1].height / 2:
                screenshot_splits[-1] = stitch_screenshots_vertically([screenshot_splits[-1], resized_image])
            else:
                screenshot_splits.append(resized_image)
        except:
            screenshot_splits.append(resized_image)

    driver.execute_script(f"window.scrollTo(0, {0});")
    driver.maximize_window()
    full_screenshot = stitch_screenshots_vertically(screenshot_splits)
    full_screenshot.save(os.path.join(os.path.dirname(path), 'full_screenshot.png'))
    return screenshot_splits


# Function to scroll up and down
def quick_scroll(driver):
    scroll_height = driver.execute_script("return document.documentElement.scrollHeight")
    driver.maximize_window()
    driver.execute_script(f"window.scrollTo(0, {scroll_height});")
    time.sleep(5)
    driver.execute_script(f"window.scrollTo(0, {0});")
