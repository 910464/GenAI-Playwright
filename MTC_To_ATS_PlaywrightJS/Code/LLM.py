from langchain.chat_models import AzureChatOpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain import LLMChain
import configparser
import json


# Create a ConfigParser object
configs = configparser.ConfigParser()

# Read the .properties file
configs.read('../Config/config.properties')

def read_properties(file_path):
    properties = {}
    with open(file_path, "r") as file:
        for line in file:
            # Ignore comments and blank l   ines
            if line.strip() and not line.startswith("#"):
                parts = line.strip().split("=")
                if len(parts) == 2:
                    key, value = parts
                    properties[key.strip()] = value.strip()

    return properties


properties_file = '../Config/configGPT.properties'
config_properties = read_properties(properties_file)

OPENAI_API_KEY = config_properties.get("OPENAI_API_KEY")
OPENAI_API_BASE = config_properties.get("OPENAI_API_BASE")
OPENAI_API_VERSION = config_properties.get("OPENAI_API_VERSION")
DEPLOYMENT_NAME = config_properties.get("DEPLOYMENT_NAME")
TEMPERATURE = configs.getfloat('LLM', 'TEMPERATURE')


class LLM:

    def send_request(self, input_param, template_prompt, input_variables, input_variables_dict, temperature=None):

        prompt = PromptTemplate(
            input_variables=input_variables,
            template=template_prompt)

        temp = TEMPERATURE

        if temperature is not None:
            temp = temperature

        if input_param['model_name'] == "gpt-35-turbo":
            qa_prompt = LLMChain(
                llm=AzureChatOpenAI(deployment_name=DEPLOYMENT_NAME, model_name="gpt-4o", temperature=temp,
                                    openai_api_key=OPENAI_API_KEY,
                                    openai_api_base=OPENAI_API_BASE,
                                    openai_api_version=OPENAI_API_VERSION),
                prompt=prompt, verbose=False)

        # elif input_param['model_name'] == "gpt-4-32k":
        #     qa_prompt = LLMChain(
        #         llm=AzureChatOpenAI(deployment_name=DEPLOYMENT_NAME_4, model_name="gpt-4-32k", temperature=TEMPERATURE,
        #                             openai_api_key=OPENAI_API_KEY_4,
        #                             openai_api_base=OPENAI_API_BASE_4,
        #                             openai_api_version=OPENAI_API_VERSION_4),
        #         prompt=prompt, verbose=False)

        output_qa_prompt = qa_prompt.run(input_variables_dict)

        return output_qa_prompt

    # def send_request_aws(self, encoded_image, prompt):
    #     body = json.dumps({
    #         "max_tokens": 4096,
    #         "messages": [
    #             {
    #                 "role": "user",
    #                 "content": [
    #                     {
    #                         "type": "image",
    #                         "source": {
    #                             "type": "base64",
    #                             "media_type": "image/png",
    #                             "data": encoded_image,
    #                         },
    #                     },
    #                     {
    #                         "type": "text",
    #                         "text": prompt
    #
    #                     }
    #                 ],
    #             }
    #         ],
    #         "anthropic_version": "bedrock-2023-05-31"
    #     })
    #
    #     response = bedrock.invoke_model(body=body, modelId="anthropic.claude-3-sonnet-20240229-v1:0")
    #     # "anthropic.claude-3-opus-20240229-v1:0"
    #     # "anthropic.claude-3-haiku-20240307-v1:0"
    #     # anthropic.claude-3-sonnet-20240229-v1:0
    #     response_body = json.loads(response.get("body").read())
    #     return response_body.get("content")[0]['text']