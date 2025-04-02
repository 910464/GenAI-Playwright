import os.path

import pandas as pd
from io import StringIO
from Code.PlaywrightJavascript import playwright_javascript_generator
from Code.ManualTCProcessing import create_timestamp_filename, categorize_line, merge_to_camel_case, parse_json
from Code.WebPageCrawlerCraft import WebPageCrawlerCraft
from Code import GenerateFormattedTC
from Code import BDDTokenizer

def generate(file_content, input_param):
    inter_file = create_timestamp_filename(
        f"../Data/intermediate_files",
        ".csv")
    if not os.path.exists(
            f"../Data/intermediate_files"):
        os.makedirs(
            f"../Data/intermediate_files")

    non_crawl_languages = ['CypressApiTs', 'CypressApiJs']

    if input_param['crawl'] and input_param['language'] not in non_crawl_languages:

        if input_param['isBDD']:
            delimiter = '|'
            output = BDDTokenizer.tokenize_bdd(input_param, file_content)
        else:
            delimiter = ','
            output = GenerateFormattedTC.generate(input_param, file_content)

        output = output.strip()

        data = {'PageClass': [], 'Action': [], 'Object': [], 'Test Data': [], 'Condition': [], 'Condition_Value': [],
                'Input': []}
        # with open(file_path, 'r') as file:
        # page_class_info = ''
        if "PageClass" in str(output.split('\n')[0]):
            lines = output.split('\n')[1:]
        else:
            lines = output.split('\n')
        for line in lines:
            try:
                page_class, action, obj, test_data, condition, condition_value, _, _ = line.split(delimiter)
            except:
                try:
                    page_class, action, obj, test_data, condition, condition_value, _ = line.split(delimiter)
                except:
                    try:
                        page_class, action, obj, test_data, condition, condition_value = line.split(delimiter)
                    except:
                        try:
                            page_class, action, obj, test_data, condition = line.split(delimiter)
                        except:
                            page_class, action, obj, test_data = line.split(delimiter)
            # if line.strip().endswith(':'):
            #     page_class_info = merge_to_camel_case(str(line.strip().split(':')[0]))
            if action:
                print(
                    f"Action: {action}, Object: {obj}, Test Data: {test_data}, Condition:{condition}, Condition Value:{condition_value}")

                if "'" in page_class:
                    page_class = page_class.replace("'", "")
                if '"' in page_class:
                    page_class = page_class.replace('"', '')
                if '.' in page_class:
                    page_class = page_class.replace('.', '')
                if ' ' in page_class:
                    page_class = page_class.replace(' ', '')
                data['PageClass'].append(page_class.strip())

                if "'" in action:
                    action = action.replace("'", "")
                if '"' in action:
                    action = action.replace('"', '')
                data['Action'].append(action.strip())

                if "'" in obj:
                    obj = obj.replace("'", "")
                if '"' in obj:
                    obj = obj.replace('"', '')
                obj = obj.replace("option", "")
                obj = obj.replace("button", "")
                obj = obj.replace("link", "")
                obj = obj.replace("tab", "")
                obj = obj.replace("input field", "")
                data['Object'].append(obj.strip())

                if "'" in test_data:
                    test_data = test_data.replace("'", "")
                if '"' in test_data:
                    test_data = test_data.replace('"', '')
                data['Test Data'].append(test_data.strip())

                if "'" in condition:
                    condition = condition.replace("'", "")
                if '"' in condition:
                    condition = condition.replace('"', '')
                data['Condition'].append(condition.strip())

                if "'" in condition_value:
                    condition_value = condition_value.replace("'", "")
                if '"' in condition_value:
                    condition_value = condition_value.replace('"', '')
                data['Condition_Value'].append(condition_value.strip())

                data['Input'].append(line)

        df = pd.DataFrame(data)
        crawler = WebPageCrawlerCraft('https://www.google.co.in/')
        try:
            crawler.start('chrome', headless=False)
            crawler.crawl(df, inter_file, input_param)
        except:
            crawler.start('chrome', headless=False)
            crawler.crawl(df, inter_file, input_param)
        finally:
            crawler.stop()
        print(df)
        inter_file_path = inter_file
        # inter_file_path = (
        #     "../CoreLogicLayer/IntelligentAutomation/FunctionalTestAutomation/KarateFrameworkPython/data/Ecom_intermediate_main.csv"
        # )
        df_inter = pd.read_csv(inter_file_path)
        print(df_inter)
    else:
        test_data = StringIO(file_content)
        df_inter = pd.read_csv(test_data, sep=',')

    if input_param['language'] == "Playwright-Javascript":
        print("Generating Playwright Javascript Automation Script...")
        playwright_javascript_generator(df_inter, input_param)
    else:
        pass
