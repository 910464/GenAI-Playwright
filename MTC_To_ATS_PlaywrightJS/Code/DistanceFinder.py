import rapidfuzz


# Function to find the best match for a text from df_js in df_ocr
def find_best_match(text, df):
    df['Similarity'] = df['Extracted Text'].apply(lambda df_text: rapidfuzz.fuzz.ratio(text, df_text))
    best_match = df.loc[df['Similarity'].idxmax()]
    return best_match
