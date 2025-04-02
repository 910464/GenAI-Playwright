import argparse
import json
import sys

from Code.ScriptGeneration import generate
from Code.main import crawl

parser = argparse.ArgumentParser()

# Create this function to read the configuration file.
def read_properties(file_path):
    properties = {}
    with open(file_path, "r") as file:
        for line in file:
            # Ignore comments and blank lines
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=")
                value = value.strip()
                # Convert string 'true'/'false' to boolean
                if value.lower() == 'true':
                    properties[key.strip()] = True
                elif value.lower() == 'false':
                    properties[key.strip()] = False
                else:
                    properties[key.strip()] = value  # Keep as string if not a boolean
    return properties

def process_feature_files():
    # Read configIO.properties from config folder to get the input path
    properties_file = '../Config/configIO.properties'
    config_properties = read_properties(properties_file)
    input_file_path = config_properties.get("input_path")

    # using input file path here we are reading the input file and storing it one variable
    with open(input_file_path, 'r') as file:
        csv_content = file.read()

    # reading the processing_json configuration file from config folder
    processing_json = dict(read_properties('../Config/proccessing_Json.properties'))
    processing_json['fileName'] = input_file_path


    # Store merged data into a JSON file
    with open('../Data/merged_data.json', 'w') as json_file:
        json.dump(processing_json, json_file, indent=4, sort_keys=True)

    #  Here we are passing all all the input csv content data in csv_content,
    #  input processing_json details in processing_json, Path
    if processing_json['isGenericCrawler']:
        crawl(csv_content, processing_json)
    else:
        generate(csv_content, processing_json)

    print('Done')

if __name__ == "__main__":
    process_feature_files()


# sys.exit()
