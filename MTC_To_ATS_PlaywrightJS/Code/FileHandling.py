import glob
import os
import zipfile
import io
from typing import List


def create_zip(source_folder, zip_file_name):

    with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_folder)
                zipf.write(file_path, arcname=arcname)

def write_code_to_file(content, base_dir, file_dir, file_name):

    # Create the full directory path
    full_dir = os.path.join(base_dir, file_dir)

    # Check if the directory exists, and if not, create it
    if not os.path.exists(full_dir):
        os.makedirs(full_dir)

    # Create the full file path
    full_path = os.path.join(full_dir, file_name)

    # Write the content to the file
    with open(full_path, "w") as file:
        file.write(content)


def create_zip_archive(files_data):
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename, file_content in files_data:
            zipf.writestr(filename, file_content)

    zip_buffer.seek(0)  # Reset the buffer position to the beginning
    return zip_buffer

def get_filenames(path: str, extension: str) -> List[str]:
    """
    Looks up for all the files in a directory with specific extension.
    Parameters:
        path (str): Path to the directory
        extension (str): File extension to look for
    Returns:
        List of file names without file extension
    """
    files = glob.glob(os.path.join(path, '*.' + extension))
    filenames_without_extension = [os.path.splitext(os.path.basename(file))[0] for file in files]
    return filenames_without_extension

def apply_java_naming_convention(page_name: str) -> str:
    """
    Applies Java naming convention to a page name.
    Parameters:
        page_name (str): Name of the page
    Returns:
        str: Page name with Java naming convention
    """
    page_name = page_name.capitalize()

    def capitalize_tokens(tokens: List[str], delimeter: str):
        name = ""
        for token in tokens:
            name+=token.replace(delimeter, "").capitalize()
        return name

    def suffix_validator(name: str):
        if name.lower().endswith("page"):
            return name
        else:
            return name+"Page"

    if "-" in page_name:
        tokens = page_name.split("-")
        name = capitalize_tokens(tokens, "-")
        return suffix_validator(name)
    elif " " in page_name:
        tokens = page_name.split(" ")
        name = capitalize_tokens(tokens, " ")
        return suffix_validator(name)
    elif "_" in page_name:
        tokens = page_name.split("_")
        name = capitalize_tokens(tokens, "_")
        return suffix_validator(name)
    elif "." in page_name:
        tokens = page_name.split(".")
        name = capitalize_tokens(tokens, ".")
        return suffix_validator(name)

    return suffix_validator(page_name)