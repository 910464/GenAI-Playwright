from Code.PlaywrightJavascriptPrompts import PlaywrightJavascriptPrompts
from Code.FileHandling import write_code_to_file
from Code.LLM import LLM


class PageClassTemplate:
    def __init__(self, input_param):
        self.model = LLM()
        self.input_param = input_param
        self.extn = "js"
        self.playwrightPath = "../Data"

    def generate(self, page_name, page_data):
        prompt_instance = PlaywrightJavascriptPrompts()
        template_page_class = prompt_instance.template_page_class
        field_details = "Details of all actions on web element objects with test data and Xpath given below in the form of " \
                        "'Action - Object - Test data - Xpath'. Create one method of each action - object pair.\n"
        for _, row in page_data.iterrows():
            field_details += str(row['action']) + " - " + str(row['object']) + " - " + str(row['data']) + " - " + str(
                row['Xpath']) + "\n"
        print(field_details)
        input_variables = ["page_class", "field_details"]
        input_variables_dict = {'page_class': page_name, 'field_details': field_details}

        output_qa_prompt = self.model.send_request(self.input_param, template_page_class, input_variables,
                                                   input_variables_dict)

        write_code_to_file(output_qa_prompt, f"{self.playwrightPath}/", "Output/pages/",
                           page_name + f"Page.{self.extn}")

        print(f"{page_name}Page class file generated")
        return output_qa_prompt
