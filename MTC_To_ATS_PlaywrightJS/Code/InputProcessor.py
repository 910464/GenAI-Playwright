# import os.path
# import pandas as pd
# import shutil
#
# from Src.CoreLogicLayer.TestPlanning.ManualTestCaseGeneration.src.GetTestCaseResults import getTC, getTC_no_context
# from Src.DAOLayer import MongoReadWrite
# from Src.Constants import DBConstants
# from Src.DAOLayer.ChromaDBConnector import ChromaDBConnector
from Code.LLM import LLM


def generate(input_param, file_content):
    model = LLM()
    template_tc = """
                 As an Automation Engineer, you are tasked to write test steps in a JSON format.
            You will be given the Test Steps and the Test Data. Identify Test Data required for each Test Step and map them.
            Important:
            1. Always extract URL from the Test Data, write it with app_url and remove URL from test data.
            2. For test steps that contain multiple actions, split them into separate "step" and "test_data" fields.
            3. If a test step does not contain a data value, set the "test_data" field as an empty string.
            4. test_data must always contain string.
            5. Only return the response in the specified JSON format. Do not give any additional information.
            6. Steps Actions can be Navigate , Launch , Click , Uncheck , Enter , Populate , Upload ,Assert_text , Validate , Verify ,Select , Hover , Hover_and_Click
            7. Always give your answer as Action-Object pair in "step". Include test data in "test_data" if required.
            8. STRICTLY ALWAYS include element name and have proper test step with test data. As it is mandatory.
            Your response can only be in the following JSON format:
            {{
            "app_url": "<URL>",
            "steps": [
            {{
            "step": "<TEST STEP ACTION 1>",
            "test_data": "<TEST_DATA FOR ACTION 1>"
            }},
            {{
            "step": "<TEST STEP ACTION 2>",
            "test_data": "<TEST_DATA FOR ACTION 2>"
            }},
            {{
            ...
            }}
            ]
            }}
            STRICTLY Stick to above format ONLY.
            The Test Steps and Test Data you need to use is {mtc}
            STRICTLY ALWAYS include element name and have proper test step with test data. As it is mandatory.
        """
    #     """
    # As an Automation Engineer, you are tasked to write test steps in a JSON format.
    # You will be given the Test Steps and the Test Data. Identify Test Data required for each Test Step and map them.
    # Important:
    # 1. Always extract URL from the Test Data, write it with app_url and remove URL from test data.
    # 2. For test steps that contain multiple actions, split them into separate "step" and "test_data" fields.
    # 3. If a test step does not contain a data value, set the "test_data" field as an empty string.
    # 4. test_data must always contain string.
    # 5. Only return the response in the specified JSON format. Do not give any additional information.
    # 6. Actions can be Navigate , Launch , Click , Uncheck , Enter , Populate , Upload ,Assert_text , Validate , Verify ,Select , Hover , Hover_and_Click
    # Your response can only be in the following JSON format:
    # {{
    # "app_url": "<URL>",
    # "steps": [
    # {{
    # "step": "<TEST STEP ACTION 1>",
    # "test_data": "<TEST_DATA FOR ACTION 1>"
    # }},
    # {{
    # "step": "<TEST STEP ACTION 2>",
    # "test_data": "<TEST_DATA FOR ACTION 2>"
    # }},
    # {{
    # ...
    # }}
    # ]
    # }}
    # The Test Steps and Test Data you need to use is {mtc}
    # """

    # input_param['model_name'] = "gpt-4-32k"

    output = model.send_request(input_param, template_tc, ["mtc"],
                                {"mtc": file_content})

    input_param['model_name'] = "gpt-35-turbo"

    return output