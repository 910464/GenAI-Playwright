from Code.PlaywrightJavascriptPrompts import PlaywrightJavascriptPrompts
from Code.FileHandling import write_code_to_file
from Code.LLM import LLM

class TestScriptTemplate:

    def __init__(self, input_param):
        self.model = LLM()
        self.input_param = input_param
        self.extn = "js"
        self.playwrightPath = "../Data"

    def testScriptTemplategenerate(self, test_class, page_class_code):

        prompt_instance = PlaywrightJavascriptPrompts()

        template_testscript_class = prompt_instance.template_script_generate
        sample_method_to_follow = """test('basic test with Page Object Model', async ({ page }) => {
        await page.goto('https://demo.seleniumeasy.com/input-form-demo.html');
        const inputpageobj = new Inputformpage(page);
        await inputpageobj.fillForm();
        await inputpageobj.submitForm();
        });"""


        input_variables = ["test_class", "sample_method_to_follow", "page_class_code"]
        input_variables_dict = {'test_class': test_class, 'sample_method_to_follow': sample_method_to_follow, 'page_class_code':page_class_code}

        output_qa_prompt = self.model.send_request(self.input_param, template_testscript_class, input_variables,
                                                   input_variables_dict)

        write_code_to_file(output_qa_prompt, f"{self.playwrightPath}/", "Output/tests/", test_class + f".spec.{self.extn}")
        print("TestScript Class Generated")
        return output_qa_prompt





        # template_testscript_class = prompt_instance.template_script_generate
        #
        # db = ChromaDBConnector("../CoreLogicLayer/IntelligentAutomation/FunctionalTestAutomation/PlaywrightJavascript/data/embed_data_core")
        #
        # reusable_code_details = ""
        # for class_name in self.input_param['reusable_class_names']['testscripts']:
        #     reusable_code_details = reusable_code_details + db.get_doc_by_id(class_name)['documents'][0] + '\n'
        # print("Core files retrieval completed")
        #
        # sample_method_to_follow = """
        # const { chromium } = require('playwright');
        # (async () => {
        #     const browser = await chromium.launch();
        #     const context = await browser.newContext();
        #     const page = await context.newPage();
        #     await page.goto('https://example.com');
        #     await page.waitForSelector('h1');
        #     const title = await page.title();
        #     console.log('Title of the page:', title);
        #     await browser.close();
        # })();
        # """
        #
        # input_variables = ["reusable_code_details", "page_class",
        #                    "component_class", "sample_method_to_follow"]
        # input_variables_dict = {'reusable_code_details': reusable_code_details, 'page_class': page_name,
        #                         'component_class': comp_code, 'sample_method_to_follow': sample_method_to_follow}
        # output_qa_prompt_test = self.model.send_request(self.input_param, template_testscript_class, input_variables,
        #                                                 input_variables_dict)
        # print("TestScript Generated")
        #
        # return output_qa_prompt_test