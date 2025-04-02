import json
import logging
import os
import time
import uuid

import pandas as pd

from selenium import webdriver

from Code.get_html import \
    get_element_xpath, inject_mutation_observer, get_iframe_details, inject_html_context_retrieval
from Code.selenium_agent import perform, record_page_object_details
from Code.WebPageCrawlerCraft import WebPageCrawlerCraft
from Code.LLM import LLM
from Code.Prompt import steps_detection_prompt
from Code.InputProcessor import generate
from Code.ManualTCProcessing import create_timestamp_filename
from Code.ChromaDBConnector import ChromaDBConnector
from Code.PlaywrightJavascript import playwright_javascript_generator

llm = LLM()
chroma_connector = ChromaDBConnector(persist_directory='../Data/SavedContext')
crawler = WebPageCrawlerCraft('https://www.google.co.in/')

def crawl(file_content, input_param):
    inter_file = create_timestamp_filename(
        "../Data/intermediate_files/generic_crawler",
        ".csv")
    if not os.path.exists(
            "../Data/intermediate_files/generic_crawler"):
        os.makedirs(
            "../Data/intermediate_files/generic_crawler")

    output = generate(input_param, file_content)
    print(output)
    if output.startswith("```json"
                         "") and output.endswith("```"):
        output = output[7:-3]  # Remove the '''json prefix and the ending '''
    output_json = json.loads(output)
    test_url = output_json['app_url']  # Use app_id instead of app_url
    test_steps = output_json['steps']
    driver = webdriver.Chrome()
    driver.implicitly_wait(60)
    driver.get(test_url)

    # Check page ready state using JavaScript
    ready = False
    while not ready:
        ready = driver.execute_script("return document.readyState") == "complete"
        time.sleep(1)
    time.sleep(10)

    driver.maximize_window()

    # Inject MutationObserver script
    inject_mutation_observer(driver)
    # context_key = f"current_context_{uuid.uuid4()}"
    context_key = str(uuid.uuid4())

    for test_step in test_steps:
        if str(test_step['step']).lower().strip().startswith(("open", "navigate", "go to", "launch")):
            page_name = crawler.extract_page_name(driver.current_url)
            test_data = test_url
            record_page_object_details(page_name, 'Navigate', '',
                                               test_data, '', '',
                                               driver, input_param,
                                               None, '', inter_file,
                                               '', '','')
            continue

        steps_implemented = False
        scroll = False

        while not steps_implemented:
            current_url = driver.current_url
            # Call the get_iframe_details function
            iframe_details = get_iframe_details(driver)
            # Print the extracted iframe details
            print(iframe_details)
            context = inject_html_context_retrieval(driver)
            print(context)
            combined_context = iframe_details + context
            # Check if context already exists for the session ID
            existing_context = chroma_connector.get_context_by_id(context_key)
            if existing_context:
                # Compare existing context with the new context
                if json.dumps(existing_context) != json.dumps(combined_context):
                    # Update the context in ChromaDB
                    print(f"Updating context for : {context_key} ")
                    chroma_connector.update_context_in_chromadb(combined_context, context_key)
            else:
                # Store context in ChromaDB
                print(f"Storing context for ID: {context_key}")
                chroma_connector.store_context_in_chromadb(combined_context, context_key)
            # Retrieve and filter relevant context from ChromaDB
            query = test_step['step'] + ": " + str(test_step['test_data'])
            k = 1  # Number of results to retrieve
            filtered_elements, docs_with_similarity, threshold = chroma_connector.retrieval_html_context(query=query,
                                                                                                          context_key=context_key)
            print("This is filtered element: ", filtered_elements)

            response = llm.send_request(
                input_param,
                steps_detection_prompt,
                ["test_step", "context"],
                {"test_step": test_step['step'] + ": " + str(test_step['test_data']),
                 "context": json.dumps(filtered_elements)},
                0.25
            )
            if response.startswith("```json"
                                 "") and response.endswith("```"):
                response = response[7:-3]  # Remove the '''json prefix and the ending '''
            response = json.loads(response)
            print(json.dumps(response, indent=4))

            status, steps_performed, steps_not_performed = perform(driver, response["steps"],input_param, inter_file, chroma_connector,
                                                                   context_key)

            if status == -1:
                # Query the vector database for elements related to steps not performed
                query = steps_not_performed
                filtered_elements, docs_with_similarity, threshold = chroma_connector.retrieval_html_context(
                    query=query, context_key=context_key)
                print(f"Filtered elements for not performed steps: ", filtered_elements)
                response = llm.send_request(
                    input_param,
                    steps_detection_prompt,
                    ["test_step", "context"],
                    {"test_step": query,
                     "context": json.dumps(filtered_elements)},
                    0.25
                )
                if response.startswith("```json"
                                       "") and response.endswith("```"):
                    response = response[7:-3]  # Remove the '''json prefix and the ending '''
                response = json.loads(response)
                print(json.dumps(response, indent=4))
                status, steps_performed, steps_not_performed = perform(driver, response["steps"], input_param,
                                                                       inter_file, chroma_connector,
                                                                       context_key)

            if not steps_not_performed:
                logging.debug("Steps implemented successfully")
                steps_implemented = True
            if steps_performed and steps_performed.isspace():
                steps_implemented = False
                scroll = True
            elif steps_performed and not steps_performed.isspace() and status == -1:
                steps_implemented = False
                scroll = True
            elif response["stop_reason"]["Do you Want next set of elements?"] == "yes":
                scroll = True
            else:
                steps_implemented = True

    time.sleep(5)
    driver.quit()
    print('*****Done*****')

    inter_file_path = inter_file
    df_inter = pd.read_csv(inter_file_path)
    playwright_javascript_generator(df_inter, input_param)
