import requests
import gspread
import time
import subprocess
import hashlib
import re
import json
import csv
import numpy as np
from datetime import datetime, timedelta
import os
import zipfile
import shutil
import pandas as pd


def extract_zip_file(source: str, extract_folder: str) -> str:
    """Extracts a ZIP file from a URL or local path."""

    zip_path = "temp.zip" if source.startswith("http") else source

    if source.startswith("http"):  # Download ZIP if source is a URL
        try:
            with requests.get(source, stream=True) as r:
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    f.write(r.content)
        except requests.RequestException as e:
            raise ValueError(f"Error downloading ZIP file: {e}")

    if os.path.isfile(extract_folder):  # Prevent extracting into a file
        raise ValueError(f"'{extract_folder}' is a file, not a directory.")

    os.makedirs(extract_folder, exist_ok=True)  # Ensure directory exists

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_folder)
    except zipfile.BadZipFile:
        raise ValueError(
            f"Failed to extract ZIP file: {zip_path} is not a valid ZIP archive.")

    if source.startswith("http"):
        os.remove(zip_path)  # Cleanup downloaded ZIP

    return extract_folder

def fetch_answer(task_id, question, file_path):
    # if task_id == 'GA1.1': extract from excel
    # if task_id == 'GA1.2': extract from excel
    if task_id=='GA1.3':
        answer=GA1_3(file_path)
    if task_id=='GA1.4':
        answer = GA1_4(question)
    if task_id == 'GA1.5':
        answer = GA1_5(question)
    # if task_id == 'GA1.6': extract from excel
    if task_id == 'GA1.7':
        answer = GA1_7(question)
    if task_id == 'GA1.8':
        answer = GA1_8(question,file_path)
    if task_id == 'GA1.9':
        answer = GA1_9(question)
    if task_id == 'GA1.10':
        answer = GA1_10(file_path)
    # if task_id == 'GA1.11': extract from excel
    if task_id == 'GA1.12':
        answer = GA1_12(question, file_path)
    return answer

def GA1_3(file_path):
    try:
        # Run Prettier and capture output
        prettier_cmd = ["npx", "-y", "prettier@3.4.2", file_path]
        formatted_output = subprocess.run(
            prettier_cmd, capture_output=True, text=True, check=True).stdout

        # Compute SHA-256 hash
        hash_value = hashlib.sha256(formatted_output.encode()).hexdigest()

        return hash_value
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

def GA1_4(question):
    sum_seq_pattern = r"SUM\(ARRAY_CONSTRAIN\(SEQUENCE\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*(\d+)\)\)"
    if match := re.search(sum_seq_pattern, question):
        rows, cols, start, step, begin, end = map(int, match.groups())
    if begin > 0:begin=begin-1
    answer = int(np.sum(np.arange(start, start + cols * step, step)[begin:end]))
    return answer

def GA1_4_old():
    sheet_url = "https://docs.google.com/spreadsheets/d/1-A4hSDwAyJWD848AAKi2S178W2HU7klu7JozwclE8kQ/edit"
    sheet_id = "1-A4hSDwAyJWD848AAKi2S178W2HU7klu7JozwclE8kQ"
    sheet_name="Sheet1"
    cell = "A1"
    formula = "=SUM(ARRAY_CONSTRAIN(SEQUENCE(100, 100, 6, 10), 1, 10))"
    return True

def GA1_5(question):
    sum_take_sortby_pattern = r"SUM\(TAKE\(SORTBY\(\{([\d,]+)\},\s*\{([\d,]+)\}\),\s*(\d+),\s*(\d+)\)\)"
    if match := re.search(sum_take_sortby_pattern, question):
        numbers = list(map(int, match.group(1).split(',')))
        sort_order = list(map(int, match.group(2).split(',')))
        begin, end = map(int, [match.group(3), match.group(4)])
    if begin > 0:
        begin = begin-1
    sorted_numbers = [x for _, x in sorted(zip(sort_order, numbers))]
    answer = sum(sorted_numbers[begin:end])
    return answer
    
def GA1_7(question):
    weekday_count_pattern = r"How many (\w+)s are there in the date range (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})\?"
    if match := re.search(weekday_count_pattern, question):
        weekday_str, start_date, end_date = match.groups()
        weekdays = {"Monday": 0, "Tuesday": 1, "Wednesday": 2,
                    "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
        if weekday_str in weekdays:
            start, end = datetime.strptime(start_date, "%Y-%m-%d"), datetime.strptime(end_date, "%Y-%m-%d")
            answer = sum(1 for i in range((end - start).days + 1) if (start +
                         timedelta(days=i)).weekday() == weekdays[weekday_str])
    return answer

def GA1_8(question,zip_file):
    file_download_pattern = r"which has a single (.+\.csv) file inside\."
    if match := re.search(file_download_pattern, question):
        csv_filename = match.group(1)
        extract_folder = extract_zip_file(os.path.join(os.getcwd(), zip_file), zip_file[:-4])
        csv_file_path = os.path.join(extract_folder, csv_filename)
        # Read CSV file
        df = pd.read_csv(csv_file_path)
        answer = df["answer"].iloc[0] if "answer" in df.columns else "Column not found"
        # Cleanup extracted files
        shutil.rmtree(extract_folder, ignore_errors=True)
    return answer

def GA1_9(question):
    json_pattern = r"\[.*?\]|\{.*?\}"
    sort_pattern = r"Sort this JSON array of objects by the value of the (\w+) field.*?tie, sort by the (\w+) field"

    json_match = re.search(json_pattern, question, re.DOTALL)
    sort_match = re.search(sort_pattern, question, re.DOTALL)

    if json_match and sort_match:
        try:
            json_data = json.loads(json_match.group())
            sort_keys = [sort_match.group(1), sort_match.group(2)]
            # print(sort_keys)
            if isinstance(json_data, list) and all(isinstance(d, dict) for d in json_data):
                sorted_data = sorted(json_data, key=lambda x: tuple(
                    x.get(k) for k in sort_keys))
                return json.dumps(sorted_data, separators=(",", ":"))
            else:
                return json.dumps(json_data, separators=(",", ":"))

        except json.JSONDecodeError:
            return None

    return None

def GA1_10(file_path):
    data = {}
    # Check if file exists
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' not found.")
        return "File not found"
    # Read and process the file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    data[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error reading file: {e}")
        return "Error reading file"
    # Convert data to JSON
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    # Calculate the hash of the JSON string
    json_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    return json_hash

def GA1_12(question, zip_path):
    # Regex patterns
    file_pattern = r"(\w+\.\w+):\s*(?:CSV file|Tab-separated file) encoded in ([\w-]+)"
    symbol_pattern = r"where the symbol matches ((?:[\w\d]+|\W)(?:\s*OR\s*(?:[\w\d]+|\W))*)"

    # Extract file encodings
    files = {match.group(1): match.group(2)
             for match in re.finditer(file_pattern, question)}

    # Extract symbols
    symbols_match = re.search(symbol_pattern, question)
    target_symbols = set(symbols_match.group(
        1).split(" OR ")) if symbols_match else set()

    total_sum = 0
    # Extract ZIP
    extract_folder = extract_zip_file(zip_path, zip_path[:-4])
    print(extract_folder)
    # Process extracted files
    for file_name, encoding in files.items():
        encoding = encoding.lower()
        if 'cp-' in encoding:
            encoding = encoding.replace('cp-', 'cp')
        target_symbols = list(target_symbols)
        print(file_name, encoding, target_symbols)
        file_path = os.path.join(extract_folder, file_name)
        if file_name.endswith(".csv"):
            with open(file_path, mode='r', encoding=encoding) as file:
                reader = csv.reader(file)
                for row in reader:
                    symbol, value = row
                    if symbol in target_symbols:
                        total_sum += float(value)
        elif file_name.endswith(".txt"):
            with open(file_path, mode='r', encoding=encoding) as file:
                for line in file:
                    symbol, value = line.strip().split('\t')
                    if symbol in target_symbols:
                        total_sum += float(value)
    return total_sum
