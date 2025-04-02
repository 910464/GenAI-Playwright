import datetime
import json

import pandas as pd


def create_timestamp_filename(folder_path, extn):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{folder_path}/data_{timestamp}{extn}"
    return filename


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):].strip()
    return text.strip()


def categorize_line(line):
    action = ""
    obj = ""
    test_data = ""

    start_obj = line.find('[')
    end_obj = line.find(']')
    start_test_data = line.rfind('(')
    end_test_data = line.rfind(')')

    if line.strip().endswith(':'):
        return action, obj, test_data

    if start_obj != -1 and end_obj != -1:
        action = line[:start_obj].strip()
        obj = line[start_obj + 1:end_obj].strip()

    if start_test_data != -1 and end_test_data != -1:
        if not action:
            action = line[:start_test_data].strip()
        test_data = line[start_test_data + 1:end_test_data].strip()
        if test_data.startswith("enter data:"):
            test_data = test_data[len("enter data:"):].strip()

    test_data = remove_prefix(test_data, "enter data:")
    test_data = remove_prefix(test_data, "stage Link:")

    if action.count(' ') > 0 and not action.startswith('Navigate'):
        test_data = obj
        action, obj = action.split(' ', 1)

    return action, obj, test_data


def merge_to_camel_case(line):
    words = line.strip().split()
    camel_case = words[0].capitalize() + ''.join(word.capitalize() for word in words[1:])
    return camel_case


def parse_json(json_content, inter_file_path):
    # # Specify the path to your JSON file
    # json_file_path = f_path
    #
    # # Open the JSON file and load its contents
    # with open(json_file_path, "r") as json_file:
    # json_data = json.loads(json_content)

    parsed_data = {'page': [], 'action': [], 'object': [], 'data': [], 'Xpath': []}

    # Iterate through the JSON data
    for item in json_content:
        page = item.get("className", "")
        action = item.get("action", "")
        obj = item.get("elementObject", "")
        data = item.get("data", "")
        value = item.get("value", "")

        if item.get("type", "").lower() == "xpath":
            xpath = value
        elif item.get("type", "").lower() == "id":
            xpath = f"//*[@id='{value}']"
        elif item.get("type", "").lower() == "class":
            xpath = f"//*[contains(@class, '{value}')]"
        else:
            xpath = f"//*[@{item.get('type', '').lower()}='{value}']"

        # Append the extracted data as a dictionary
        parsed_data['page'].append(page)
        parsed_data['action'].append(action)
        parsed_data['object'].append(obj)
        parsed_data['data'].append(data)
        parsed_data['Xpath'].append(xpath)

    pd.DataFrame(parsed_data).to_csv(inter_file_path, index=False)
    print(f"Data extracted and saved")
