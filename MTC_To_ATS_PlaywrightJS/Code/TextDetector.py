import pandas as pd
from collections import Counter
from Code.TextDetection import fullpageOCR
from Code.WebElementDetailer import fullpageJS
from Code.DistanceFinder import find_best_match


def calculate_max_ratio_count(coordinate_proportions):
    # Initialize counters for each column
    counters = {
        'Proportion Top Left x': Counter(),
        'Proportion Top Left y': Counter(),
        'Proportion Bottom Right x': Counter(),
        'Proportion Bottom Right y': Counter()
    }
    for item in coordinate_proportions:
        for key, value in item.items():
            counters[key][value] += 1

    # Find the max occurring values for each proportion
    max_top_left_x = counters['Proportion Top Left x'].most_common(1)[0][0]
    max_top_left_y = counters['Proportion Top Left y'].most_common(1)[0][0]
    max_bottom_right_x = counters['Proportion Bottom Right x'].most_common(1)[0][0]
    max_bottom_right_y = counters['Proportion Bottom Right y'].most_common(1)[0][0]

    ratio_topleft = (max_top_left_x, max_top_left_y)
    ratio_bottomright = (max_bottom_right_x, max_bottom_right_y)

    return ratio_topleft, ratio_bottomright


def get_text_elements(driver, url):

    # run OCR and JS to create individual pandas dataframes
    driver.get(url)
    ocr_df = fullpageOCR(driver)
    js_df = fullpageJS(driver)
    merged_results = []
    coordinate_proportions = []

    for _, ocr_row in ocr_df.iterrows():

        match = find_best_match(ocr_row['Extracted Text'], js_df)
        PropRatio_TopLeft = (round(ocr_row['Top Left'][0] / match['Top Left'][0], 2),
                             round(ocr_row['Top Left'][1] / match['Top Left'][1], 2))
        PropRatio_BottomRight = (round(ocr_row['Bottom Right'][0] / match['Bottom Right'][0], 2),
                                 round(ocr_row['Bottom Right'][1] / match['Bottom Right'][1], 2))

        merged_results.append({
            'OCR Extracted Text': ocr_row['Extracted Text'],
            'OCR Top Left': ocr_row['Top Left'],
            'OCR Bottom Right': ocr_row['Bottom Right'],
            'JS Extracted Text': match['Extracted Text'],
            'JS Extracted XPath': match['Extracted Xpath'],
            'JS Top Left': match['Top Left'],
            'JS Bottom Right': match['Bottom Right'],
            'JS Common Parent Elements': match['Common Parent Elements'],
            'Similarity': match['Similarity']
        })
        coordinate_proportions.append({
            'Proportion Top Left x': PropRatio_TopLeft[0],
            'Proportion Top Left y': PropRatio_TopLeft[1],
            'Proportion Bottom Right x': PropRatio_BottomRight[0],
            'Proportion Bottom Right y': PropRatio_BottomRight[1]
        })

    # Convert the list of dictionaries to a dataframe
    final_df = pd.DataFrame(merged_results)
    final_df.to_csv("../Data/Output.csv", index=False)

    ratio_topleft, ratio_bottomright = calculate_max_ratio_count(coordinate_proportions)

    return ratio_topleft, ratio_bottomright
