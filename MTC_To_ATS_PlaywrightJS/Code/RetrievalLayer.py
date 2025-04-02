import re
from typing import Set, List, Any

import pandas as pd
from langchain.schema import Document
from pandas import DataFrame

from Code.ChromaDBConnector import ChromaDBConnector

CRAFT_FRAMEWORK_PATH = "../Data"


def concatenate_columns(row):
    return f"\n{row['action']} {row['object']}"


def retrieve_exist_code(page_name, page_data):
    db = ChromaDBConnector(f"{CRAFT_FRAMEWORK_PATH}/embed_data_gen/code")
    db2 = ChromaDBConnector(f"{CRAFT_FRAMEWORK_PATH}/embed_data_gen/csv")

    details = page_data.apply(concatenate_columns, axis=1)
    try:

        exist_page_name = page_name + 'Page'
        exist_page = db.get_doc_by_id(exist_page_name)
        missing_methods = pd.DataFrame(columns=page_data.columns.tolist())
        print("missing_methods\n", missing_methods)
        exist_page_code = ""

        if len(exist_page['documents']) != 0:
            exist_page_code = exist_page['documents'][0]

        # Iterate through rows in the DataFrame
        previous_index = -1
        method_start_index = -1
        for index, row in page_data.iterrows():

            if str(row['failure']).startswith("Invalid action"):
                missing_methods = missing_methods.append(row, ignore_index=True)
                continue

            found_method = False  # Flag to check if the method is found in the Java class code
            already_in_missing_df = False

            method_content = ""
            # if action is Select and data is available
            if row['action'] == "Select" and not pd.isna(row['data']):
                method_content = db2.retrieval(
                    f"Get method details for '{row['action']} {row['object']} {row['data']}'", 3)
            else:
                method_content = db2.retrieval(
                    f"Get method details for '{row['action']} {row['object']}'", 3)

            for i in range(len(method_content)):

                print("method_content[i]\n", method_content[i])
                pattern = r'Class:\s*(\w+)'
                class_name = re.search(pattern, method_content[i].page_content).group(1)
                if class_name == exist_page_name:
                    curr_method = method_content[i].page_content

                    pattern = r'Method:\s*(public void )*(\w+)\((.*?)\)'
                    match = re.search(pattern, curr_method)

                    method_name = match.group(2)
                    # arguments of the method present in current document retreived from db2(vectorDB)
                    method_arguments = match.group(3).split(',')

                    # case when xpath is not present for current row
                    if pd.isna(row[row['Locator']]):
                        method_pattern = f"public void {row['action'].lower()}(\w*)\((.*?)\) {{"
                    # case when xpath is present for current row
                    else:
                        x_path = re.escape(row[row['Locator']])
                        method_pattern = f" (\w+) = By.\w+\(\"{x_path}\"\)"

                    match = re.search(method_pattern, exist_page_code)

                    if match:

                        conclusive_match = True

                        # comparing method signature in case xpath is not present for current row
                        if pd.isna(row[row['Locator']]):

                            method_name = row['action'].lower()+match.group(1)
                            method_start_index = match.start()
                            haveSameSignature = True
                            # arguments of the method present in java code generated from db (vectorDB)
                            code_method_arguments = match.group(2).split(',')

                            # comparing method signature of method in java code and method in retreived document
                            # to check if both methods have same number of arguments
                            if len(method_arguments) == len(code_method_arguments):

                                # to compare the data type of each argument in above methods
                                for i in range(len(method_arguments)):
                                    if method_arguments[i].split(' ')[0] != code_method_arguments[i].split(' ')[0]:
                                        haveSameSignature = False
                            else:
                                haveSameSignature = False

                            if haveSameSignature:
                                conclusive_match = True
                            else:
                                conclusive_match = False

                        # if xpath is present then we compare the xpath variable used inside the method
                        else:
                            xpathMatch = False
                            xpath_variable = match.group(1)
                            print("xpath_variable = "+xpath_variable)
                            pattern = re.compile(
                                r"\bpublic\s+void\s+(\w+)\s*\(([^)]*)\)\s*{[^}]*" + xpath_variable + "[^}]*}", re.DOTALL
                            )

                            xpath_pattern_match = pattern.search(exist_page_code)

                            if xpath_pattern_match:
                                method_name = xpath_pattern_match.group(1)
                                print("method_name under xpath_pattern_match = "+method_name)
                                xpathMatch = True
                                method_start_index = xpath_pattern_match.start()

                            if xpathMatch:
                                conclusive_match = True
                            else:
                                conclusive_match = False

                        if conclusive_match:
                            page_data.at[index, 'method_name'] = method_name
                            print(f"Method '{method_name}' found in Java class code at index {method_start_index}")
                            found_method = True

                    if found_method:
                        break  # Exit the loop for method_content

            if not found_method:
                print(f"Method for '{row}' 'not found in Java class code")
                # If method is missing, add it to the missing_methods_df
                missing_methods = missing_methods.append(row, ignore_index=True)

        return missing_methods, exist_page_code, page_data
    except Exception as e:
        print(e)
        return page_data, "", page_data


def retrieve_reusable_code(data: DataFrame, csv_store: ChromaDBConnector, component_type="pages",
                           component_name="LandingPage") -> set[Any]:
    methods = set()
    missing_methods = pd.DataFrame(columns=data.columns.tolist())
    for index, row in data.iterrows():
        relevant_implementation = list()
        if str(row['failure']).startswith("Invalid action"):
            continue

        try:
            if pd.notna(row['action']) and pd.notna(row['object']) and pd.notna(row['data']) and pd.isna(row['Condition']) and pd.isna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details to '{row['action']}' '{row['data']}' from '{row['object']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                ]
                )
            elif pd.notna(row['action']) and pd.notna(row['object']) and pd.isna(row['data']) and pd.isna(row['Condition']) and pd.isna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details to '{row['action']}' '{row['object']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                    ]
                )
            elif pd.notna(row['action']) and pd.isna(row['object']) and pd.isna(row['data']) and pd.isna(row['Condition']) and pd.isna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details to '{row['action']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                    ]
                )
            elif pd.isna(row['action']) and pd.notna(row['object']) and pd.notna(row['data']) and pd.isna(row['Condition']) and pd.isna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details send '{row['data']}' to '{row['object']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                    ]
                )
            elif pd.isna(row['action']) and pd.notna(row['object']) and pd.isna(row['data']) and pd.isna(row['Condition']) and pd.isna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details to get '{row['action']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                    ]
                )
            elif pd.isna(row['action']) and pd.isna(row['object']) and pd.notna(row['data']) and pd.isna(row['Condition']) and pd.isna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details to get '{row['data']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                    ]
                )
            elif pd.notna(row['action']) and pd.notna(row['object']) and pd.notna(row['data']) and pd.notna(row['Condition']) and pd.notna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details to '{row['action']}' '{row['data']}' from '{row['object']}' and validate '{row['Condition']}' with '{row['Condition_Value']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                ]
                )
            elif pd.notna(row['action']) and pd.notna(row['object']) and pd.isna(row['data']) and pd.notna(row['Condition']) and pd.notna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details to '{row['action']}' from '{row['object']}' and validate '{row['Condition']}' with '{row['Condition_Value']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                ]
                )
            elif pd.notna(row['action']) and pd.isna(row['object']) and pd.notna(row['data']) and pd.notna(row['Condition']) and pd.notna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details to '{row['action']}' '{row['data']}' and validate '{row['Condition']}' with '{row['Condition_Value']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                ]
                )
            elif pd.isna(row['action']) and pd.notna(row['object']) and pd.notna(row['data']) and pd.notna(row['Condition']) and pd.notna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details send '{row['data']}' to '{row['object']}' and validate '{row['Condition']}' with '{row['Condition_Value']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                ]
                )
            elif pd.isna(row['action']) and pd.notna(row['object']) and pd.isna(row['data']) and pd.notna(row['Condition']) and pd.notna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details to get '{row['action']}' and validate '{row['Condition']}' with '{row['Condition_Value']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                ]
                )
            elif pd.isna(row['action']) and pd.isna(row['object']) and pd.notna(row['data']) and pd.notna(row['Condition']) and pd.notna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details to get '{row['data']}' and validate '{row['Condition']}' with '{row['Condition_Value']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                ]
                )
            elif pd.notna(row['action']) and pd.isna(row['object']) and pd.isna(row['data']) and pd.notna(row['Condition']) and pd.notna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details to '{row['action']}' and validate '{row['Condition']}' with '{row['Condition_Value']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                ]
                )
            elif pd.isna(row['action']) and pd.isna(row['object']) and pd.isna(row['data']) and pd.notna(row['Condition']) and pd.notna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details to validate '{row['Condition']}' with '{row['Condition_Value']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                ]
                )
            elif pd.isna(row['action']) and pd.isna(row['object']) and pd.isna(row['data']) and pd.notna(row['Condition']) and pd.isna(row['Condition_Value']):
                relevant_implementation.extend([
                    doc.page_content for doc in csv_store.retrieve_filtered(
                    f"Get method details to validate '{row['Condition']}' from class '{component_name}'",
                    3,
                    filters={"$and": [{"component type": component_type}, {"component name": component_name}]})
                ]
                )
        except Exception as e:
            print(f"Error in retrieving reusable code for {row}: ", e)

        if not relevant_implementation:
            missing_methods = missing_methods.append(row, ignore_index=True)
        else:
            methods.update(relevant_implementation)
    return methods
