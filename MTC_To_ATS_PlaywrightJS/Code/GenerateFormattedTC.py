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
            Using the input Test Steps provided: '{input}', follow the instructions below to identify and extract the following components:
            1. **PageClass:** Identify the page on which each action is getting performed from input provided
            2. **Action:** Identify the verb or action word that indicates the primary operation. 
            Action should be STRICTLY ONLY from this list [Navigate, Click, Uncheck, Enter, Populate, Upload, Assert_text, Select, Hover, Hover_and_Click].
            3. **Object:** Determine the main subject or object of the action. 
            This represents the primary focus of the statement. i.e. phrase on which Action supposed to execute.
            STRICTLY Include ONLY the Phrase not the type. i.e. Instead of writing 'submit button', write ONLY 'submit'.
            4. **Condition:** Find the phrase or words that indicate the state or circumstance under which the action occurs. 
            Look for conditions such as 'is displayed,' 'navigates to,' or 'in' followed by page name, 
            multiple conditional phrases can be found in single statement. Ensure that condition phrases are listed below 'Condition' column.
            5. **Condition_Value:** Extract the specific information or content associated with the identified Condition. 
            This represents the detailed context or criteria, for e.g. in statement 'Verify that header content is displayed in a XY Page as below: minimum duration added' the condition is 'is displayed in a XY Page' and condition value is 'minimum duration added'. Ensure that condition_value phrases are listed below 'Condition_' column.
            6. **Test_Data*:** So these statements are basically steps in manual test case to execute on web application, so in that context, any value which is available in statement can be used to fill/update in web page can be extracted as Data.
            Whenever, 'Action' is 'Navigate' then, in 'Test Data' URL will be there and 'Object' will be empty
            Wherever, 'Condition' is present in a sentence 'Condition_Value' should contain test data.
            Please provide your findings for each component based on the given instructions.
            
                ==> Refer below example and STRICTLY maintain same format
                        PageClass,Action,Object,Test_Data,Condition,Condition_Value,extra
                        Homepage, Navigate,,https://www.macys.com/,,, 
                        Homepage, Assert_text, search button,,with a search button in the header,,
                        Homepage, Enter, Search field, nike,,,
                        Search Results, Assert_text, nike shoes,,verify "nike shoes" in the search results,,
            
            Make sure you return entire extracted data with comma separated format only and not the truncated dotted format response.
            Maintain the CSV table sequence with STRICTLY 7 columns and add a header with column names as below:
            PageClass,Action,Object,Test_Data,Condition,Condition_Value, extra.
            Strictly put relevant data under extracted columns and keep empty entry in case extracted info is not available.
            Do Not generate any extra row
            """

    # input_param['model_name'] = "gpt-4-32k"

    output = model.send_request(input_param, template_tc, ["input"],
                                {"input": file_content})

    validation_check = """
            This is the input :'{input}'
            LLM gave this response when asked to extract Action, Object, Data, Condition, Condition_Value :'{output}'
            I want you to validate this output given by LLM and do any corrections if needed and return CSV data in same format.
            To validate you can refer below guidelines:
            1. PageClass: This should be the page where specific actions is getting performed.
            2. Action: This should have only one keyword extracted from sentence.
            3. Object: This is Noun Phrase in sentence.
            4. Test Data: This represents test data to enter in web application in that step
            5. Condition: This is represents condition mentioned in step. for e.g. is displayed is condition
            6. Condition_Value: This is value of condition to check for e.g. is displayed is condition followed by any reference is condition_value'
            7. Validate STRICTLY ONLY '7' columns are present not more not less if less columns are there add one empty.
            Return ONLY csv format without any formatting or code markers (e.g., no ''', no csv, no backticks). DON'T give any explanation
            """

    output_validated = model.send_request(input_param, validation_check, ["input", 'output'],
                                          {"input": file_content, "output": output})

    input_param['model_name'] = "gpt-35-turbo"

    return output_validated