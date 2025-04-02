import os.path

import pandas as pd

from Code.TestScriptTemplate import TestScriptTemplate
from Code.PageClassTemplate import PageClassTemplate


def playwright_javascript_generator(df_inter, input_param):
    page_wise = df_inter.groupby("page", sort=False)
    comp_code = ""
    page_name_and_class = {}
    for page_name, page_data in page_wise:
        print(f"Processing Group '{page_name}':")
        print(page_data)

        pg_generator = PageClassTemplate(input_param)
        pg_code = pg_generator.generate(page_name, page_data)
        print(pg_code)
        page_name_and_class[page_name] = pg_code

    print("************** Page Objects Generated ***************")
    script_generator = TestScriptTemplate(input_param)
    runner_code = script_generator.testScriptTemplategenerate('TestScript', page_name_and_class)
    print("************** Spec file Generated ******************")
