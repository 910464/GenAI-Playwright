import os
import time

import matplotlib.pyplot as plt
import seaborn as sns

from Code.ImageProcessingUtils import custom_full_screenshot


# Function to number folders if same folder already exists.
def create_folder(detection_path):
    if not os.path.exists(detection_path):
        os.makedirs(detection_path)
        unique_full_path = detection_path
    else:
        # Find a unique folder name by appending a numbering
        number = 2
        while os.path.exists(f"{detection_path}_{number}"):
            number += 1

        unique_full_path = f"{detection_path}_{number}"
        os.makedirs(unique_full_path)
    return unique_full_path + '/'


def save_list_in_txt(txtfile_path, my_list):
    with open(txtfile_path + '/detections_list', 'w') as file:
        for item in my_list:
            file.write(str(item) + '\n')


# Defining the colors
'''
colors = {
    0: 'SteelBlue',
    1: 'OliveDrab',
    2: 'DarkOrange',
    3: 'MediumPurple',
    4: 'MediumTurquoise',
    5: 'SaddleBrown',
    6: 'DarkSeaGreen',
    7: 'DarkSlateBlue',
    8: 'IndianRed',
    9: 'MediumVioletRed',
    10: 'Sienna',
    11: 'CornflowerBlue',
    12: 'MediumOrchid',
    13: 'MediumSeaGreen',
    14: 'DarkGoldenrod',
    15: 'DarkOliveGreen',
    16: 'SlateBlue',
    17: 'Crimson',
    18: 'DarkCyan',
    19: 'FireBrick'

}
'''
colors = {
    0: 'Red',
    1: 'Lime',
    2: 'Blue',
    3: 'Yellow',
    4: 'Magenta',
    5: 'Cyan',
    6: 'Orange',
    7: 'Pink',
    8: 'Purple',
    9: 'SpringGreen',
    10: 'Gold',
    11: 'DodgerBlue',
    12: 'DeepPink',
    13: 'LimeGreen',
    14: 'OrangeRed',
    15: 'DarkRed',
    16: 'DarkOrange',
    17: 'Teal',
    18: 'DarkViolet',
    19: 'DarkGreen'
}



# Function to save a color chart of the identified bounding boxes
def save_color_chart(class_names, detection_path):
    # Create a color palette with 10 colors
    palette = sns.color_palette(list(colors.values())[:len(class_names)])

    plt.figure(figsize=(25, 5))
    plt.bar(list(class_names.values()), 1, color=palette)

    plt.yticks([])
    plt.xlabel('Web Elements')
    plt.ylabel("Colors")

    plt.savefig(f'{detection_path}/color_chart.png')


def highlight_and_screenshot(refined_coordinates_with_elements, driver, class_names, detection_path, driver_type=None):
    prev_width = driver.execute_script("return window.innerWidth;")
    prev_height = driver.execute_script("return document.documentElement.scrollHeight;")

    # Highlighting the Detections and Taking its Screenshot
    highlight_script2 = '''
    arguments[0].style.border = `2px solid {}`;
    '''
    undo_script = ''' 
    arguments[0].style.border = 'none';
    '''
    print(class_names)
    class_names_dict = {}
    for ids in class_names:
        class_names_dict[class_names[ids]] = ids

    for i in refined_coordinates_with_elements:
        color = colors[class_names_dict[i[5]]]
        element = i[-3]
        driver.execute_script(highlight_script2.format(color), element)

    # Taking Screenshots After Highlighting the Elements
    total_height = driver.execute_script("return document.documentElement.scrollHeight")
    width = driver.execute_script("return window.innerWidth")
    driver.set_window_size(width, total_height)

    screenshot_path2 = detection_path + "/Screenshots/detections_screenshot.png"  # Path to save detections Screenshot

    print('Driver_Type_Check : ', driver_type)
    if driver_type != 'Headless':
        custom_full_screenshot(driver, screenshot_path2)
    else:
        driver.save_screenshot(screenshot_path2)

    time.sleep(5)  ################## PAUSE #############################

    for i in refined_coordinates_with_elements:
        element = i[-3]
        driver.execute_script(undo_script, element)

    driver.set_window_size(prev_width, prev_height)

    # Saving the color chart to identify the classifications
    save_color_chart(class_names, detection_path)


import json

def save_dict_to_json(dictionary, filename):
    with open(filename, 'w') as file:
        json.dump(dictionary, file)

def save_list_to_file(lst, filename):
    with open(filename, 'w') as file:
        for item in lst:
            file.write(str(item) + '\n')
