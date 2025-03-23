import jellyfish
import pandas as pd
import numpy as np
from datetime import datetime
import re
import gzip
from collections import defaultdict
from fuzzywuzzy import process  # type: ignore
import pycountry  # type: ignore
import json
import os
from PIL import Image, ImageDraw
import base64


def get_country_code(country_name: str) -> str:
    """Retrieve the standardized country code from various country name variations."""
    normalized_name = re.sub(r'[^A-Za-z]', '', country_name).upper()
    for country in pycountry.countries:
        names = {country.name, country.alpha_2, country.alpha_3}
        if hasattr(country, 'official_name'):
            names.add(country.official_name)
        if hasattr(country, 'common_name'):
            names.add(country.common_name)
        if normalized_name in {re.sub(r'[^A-Za-z]', '', name).upper() for name in names}:
            return country.alpha_2
    return "Unknown"  # Default value if not found


def parse_date(date):
    for fmt in ("%m-%d-%Y", "%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(date), fmt).date()
        except ValueError:
            continue
    return None


# Standardized country names mapping
COUNTRY_MAPPING = {
    "USA": "US", "U.S.A": "US", "United States": "US",
    "India": "IN", "IND": "IN", "Bharat": "IN",
    "UK": "GB", "U.K": "GB", "United Kingdom": "GB", "Britain": "GB",
    "France": "FR", "Fra": "FR", "FRA": "FR",
    "Brazil": "BR", "BRA": "BR", "BRAZIL": "BR", "BRASIL": "BR",
    "UAE": "AE", "U.A.E": "AE", "United Arab Emirates": "AE",
}


def GA5_1(question, file_path):
    match = re.search(
        r'What is the total margin for transactions before ([A-Za-z]{3} [A-Za-z]{3} \d{2} \d{4} \d{2}:\d{2}:\d{2} GMT[+\-]\d{4}) \(India Standard Time\) for ([A-Za-z]+) sold in ([A-Za-z]+)', question, re.IGNORECASE)
    filter_date = datetime.strptime(match.group(
        1), "%a %b %d %Y %H:%M:%S GMT%z").replace(tzinfo=None).date() if match else None
    target_product = match.group(2) if match else None
    target_country = get_country_code(match.group(3)) if match else None
    print(filter_date, target_product, target_country)

    # Load Excel file
    df = pd.read_excel(file_path)
    df['Customer Name'] = df['Customer Name'].str.strip()
    df['Country'] = df['Country'].str.strip().apply(get_country_code)
    # df["Country"] = df["Country"].str.strip().replace(COUNTRY_MAPPING)

    df['Date'] = df['Date'].apply(parse_date)
    # df["Date"] = pd.to_datetime(df["Date"], errors='coerce')

    df["Product"] = df["Product/Code"].str.split('/').str[0]

    # Clean and convert Sales and Cost
    df['Sales'] = df['Sales'].astype(str).str.replace(
        "USD", "").str.strip().astype(float)
    df['Cost'] = df['Cost'].astype(str).str.replace(
        "USD", "").str.strip().replace("", np.nan).astype(float)
    df['Cost'].fillna(df['Sales'] * 0.5, inplace=True)
    df['TransactionID'] = df['TransactionID'].astype(str).str.strip()

    # Filter the data
    filtered_df = df[(df["Date"] <= filter_date) &
                     (df["Product"] == target_product) &
                     (df["Country"] == target_country)]

    # Calculate total sales, total cost, and total margin
    total_sales = filtered_df["Sales"].sum()
    total_cost = filtered_df["Cost"].sum()
    total_margin = (total_sales - total_cost) / \
        total_sales if total_sales > 0 else 0
    print(total_margin, total_cost, total_sales)
    return total_margin

# Example usage
# file_path = "sales_data.xlsx"
# margin = GA5_1("What is the total margin for transactions before Sun Dec 10 2023 09:38:05 GMT+0530 (India Standard Time) for Epsilon sold in IN (which may be spelt in different ways)?", file_path)
# print("Total Margin:", margin)


def GA5_2(question, file_path):
    names, ids = set(), set()
    id_pattern = re.compile(r'[^A-Za-z0-9]+')
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            if not (line := line.strip()):
                continue
            parts = line.rsplit('-', 1)
            if len(parts) > 1:
                names.add(parts[0].strip())
                ids.add(id_pattern.sub("", parts[1].split('Marks')[0]).strip())
    print(len(names), len(ids))
    return len(ids)

# Example usage
# file_path = "student_data.txt"
# num_unique_students = GA5_2("How many unique students are there in the file?"file_path)
# print("Number of unique students:", num_unique_students)


def GA5_3(question, file_path):
    match = re.search(
        r'What is the number of successful (\w+) requests for pages under (/[a-zA-Z0-9_/]+) from (\d+):00 until before (\d+):00 on (\w+)days?', question, re.IGNORECASE)

    request_type, target_section, start_hour, end_hour, target_weekday = match.groups()
    target_weekday = target_weekday.capitalize()+"day"
    success_match = re.search(
        r'status codes between (\d+) and (\d+)', question, re.IGNORECASE)

    status_min = int(success_match.group(1)) if success_match else 200
    status_max = int(success_match.group(2)) if success_match else 299
    print(start_hour, end_hour, request_type, status_min,
          status_max, target_section, target_weekday)
    successful_requests = 0

    with gzip.open(file_path, 'rt', encoding='utf-8') as file:
        line_count = 0
        for line in file:
            line_count += 1
            parts = line.split()

            if len(parts) < 9:
                print("Malformed line:", line)
                continue  # Skip malformed lines

            time_part = parts[3].strip('[]')
            request_method, url, _ = parts[5:8]
            request_method = request_method.replace('"', '').upper()
            status_code = int(parts[8])
            log_time = datetime.strptime(time_part, "%d/%b/%Y:%H:%M:%S")
            log_time = log_time.astimezone()  # Convert timezone if needed
            request_weekday = log_time.strftime('%A')

            status_min, status_max = int(status_min), int(status_max)
            start_hour, end_hour = int(start_hour), int(end_hour)
            if (status_min <= status_code <= status_max and request_method == request_type
               and url.startswith(target_section)
               and start_hour <= log_time.hour < end_hour and request_weekday == target_weekday
                ):
                successful_requests += 1

    return successful_requests

# Example usage
# file_path = "log_data.gz"
# num_successful_requests = GA5_3("What is the number of successful GET requests for pages under /hindi/ from 3:00 until before 8:00 on Wednesdays?", file_path)
# print("Number of successful requests:", num_successful_requests)


def GA5_4(question, file_path):
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', question)
    target_date = datetime.strptime(date_match.group(
        1), "%Y-%m-%d").date() if date_match else None
    ip_bandwidth = defaultdict(int)
    log_pattern = re.search(
        r'Across all requests under ([a-zA-Z0-9]+)/ on', question)
    language_pattern = str("/"+log_pattern.group(1)+"/")
    print(language_pattern, target_date)
    with gzip.open(file_path, 'rt', encoding='utf-8') as file:
        line_count = 0
        for line in file:
            line_count += 1
            parts = line.split()
            ip_address = parts[0]
            time_part = parts[3].strip('[]')
            request_method, url, _ = parts[5:8]
            log_time = datetime.strptime(time_part, "%d/%b/%Y:%H:%M:%S")
            log_time = log_time.astimezone()  # Convert timezone if needed
            size = int(parts[9]) if parts[9].isdigit() else 0
            if (url.startswith(language_pattern) and log_time.date() == target_date):
                ip_bandwidth[ip_address] += int(size)
                # print(ip_address, time_part, url, size)
    top_ip = max(ip_bandwidth, key=ip_bandwidth.get, default=None)
    top_bandwidth = ip_bandwidth[top_ip] if top_ip else 0
    return top_bandwidth

# Example usage
# file_path = "log_data.gz"
# top_ip, top_bandwidth = GA5_4("Across all requests under malayalammp3/ on 2024-05-15, how many bytes did the top IP address (by volume of downloads) download?", file_path)
# print("Top IP address:", top_ip)
# print("Top bandwidth:", top_bandwidth)


def get_best_matches(target, choices, threshold=0.85):
    """Find all matches for target in choices with Jaro-Winkler similarity >= threshold."""
    target = target.lower()
    matches = [c for c in choices if jellyfish.jaro_winkler_similarity(
        target, c.lower()) >= threshold]
    return matches


def GA5_5(question, file_path):
    df = pd.read_json(file_path)

    match = re.search(
        r'How many units of ([A-Za-z\s]+) were sold in ([A-Za-z\s]+) on transactions with at least (\d+) units\?',
        question
    )
    if not match:
        raise ValueError("Invalid question format")

    target_product, target_city, min_sales = match.group(1).strip(
    ).lower(), match.group(2).strip().lower(), int(match.group(3))

    if not {"product", "city", "sales"}.issubset(df.columns):
        raise KeyError(
            "Missing one or more required columns: 'product', 'city', 'sales'")

    df["product"] = df["product"].str.lower()
    df["city"] = df["city"].str.lower()

    unique_cities = df["city"].unique()
    similar_cities = get_best_matches(
        target_city, unique_cities, threshold=0.85)
    print(similar_cities)

    if not similar_cities:
        return 0  # No matching cities found

    # Filter data for matching cities
    filtered_df = df[
        (df["product"] == target_product) &
        (df["sales"] >= min_sales) &
        (df["city"].isin(similar_cities))
    ]

    return int(filtered_df["sales"].sum())

# Example usage
# file_path = "sales_data.csv"
# total_sales = GA5_5("How many units of Shirt were sold in Istanbul on transactions with at least 131 units?", file_path)
# print("Total sales:", total_sales)


def fix_sales_value(sales):
    """Try to convert sales value to a float or default to 0 if invalid."""
    if isinstance(sales, (int, float)):
        return float(sales)  # Already valid

    if isinstance(sales, str):
        sales = sales.strip()  # Remove spaces
        if re.match(r"^\d+(\.\d+)?$", sales):  # Check if it's a valid number
            return float(sales)

    return 0.0  # Default for invalid values


def load_and_fix_sales_data(file_path):
    """Load JSON Lines (jsonl) sales data, fix invalid entries, and return cleaned data."""
    cleaned_data = []

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for idx, line in enumerate(file, start=1):
                try:
                    entry = json.loads(line.strip())  # Parse each JSON line

                    # Ensure 'sales' field exists, fix if needed
                    if "sales" in entry:
                        entry["sales"] = fix_sales_value(
                            entry["sales"])  # Fix invalid sales
                        cleaned_data.append(entry)
                    else:
                        print(
                            f"Line {idx}: Missing 'sales' field, adding default 0.0")
                        entry["sales"] = 0.0
                        cleaned_data.append(entry)

                except json.JSONDecodeError:
                    # print(
                    #     f"Line {idx}: Corrupt JSON, skipping -> {line.strip()}")
                    line = line.strip().replace("{", "").split(",")[:-1]
                    line = json.dumps({k.strip('"'): int(v) if v.isdigit() else v.strip(
                        '"') for k, v in (item.split(":", 1) for item in line)})
                    # print("Fixed",line)
                    cleaned_data.append(json.loads(line.strip()))

    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        return []

    return cleaned_data


def GA5_6(question, file_path):
    sales_data = load_and_fix_sales_data(file_path)
    sales = int(sum(entry["sales"] for entry in sales_data))
    return sales

# Example usage
# file_path = "sales_data.jsonl"
# total_sales = GA5_6("Download the data from q-parse-partial-json.jsonl. What is the total sales value?", file_path)
# print("Total sales:", total_sales)


def count_keys_json(data, key_word):
    count = 0
    if isinstance(data, dict):
        for key, value in data.items():
            if key == key_word:
                count += 1
            count += count_keys_json(value, key_word)
    elif isinstance(data, list):
        for item in data:
            count += count_keys_json(item, key_word)
    return count


def GA5_7(question, file_path):
    key = re.search(r'How many times does (\w+) appear as a key?', question).group(1)
    print(key)
    with open(file_path, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    count = count_keys_json(json_data, key)
    return count

# Example usage
# file_path = "q-extract-nested-json-keys.json"
# key_count = GA5_7("Download the data from q-extract-nested-json-keys.json. How many times does DX appear as a key?", file_path)
# print("Key count:", key_count)


def GA5_8(question):
    match1 = re.search(
        r"Write a DuckDB SQL query to find all posts IDs after (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z) with at least (\d+)", question)
    match2 = re.search(
        r" with (\d+) useful stars, sorted. The result should be a table with a single column called post_id, and the relevant post IDs should be sorted in ascending order.", question)
    datetime, comments,stars = match1.group(1), match1.group(2), match2.group(1)
    print(datetime, comments,stars)

    sql_query = f"""SELECT DISTINCT post_id FROM (SELECT timestamp, post_id, UNNEST (comments->'$[*].stars.useful') AS useful FROM social_media) AS temp
WHERE useful >= {stars}.0 AND timestamp > '{datetime}'
ORDER BY post_id ASC
"""
    return sql_query.replace("\n", " ")

# Example usage
# sql_query = GA5_8("Write a DuckDB SQL query to find all posts IDs after 2025-01-21T14: 36:47.099Z with at least 1 comment with 5 useful stars, sorted. The result should be a table with a single column called post_id, and the relevant post IDs should be sorted in ascending order.", file_path)
# print("Key count:", key_count)


def GA5_10(mapping_text, file_path):
    """
    Reconstructs an image from scrambled pieces using a given mapping.
    
    Args:
        mapping_text (str): The mapping information as a string.
        file_path (str): The path to the scrambled image file.
    
    Returns:
        str: Base64-encoded string of the reconstructed image.
    """

    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Load the scrambled image
    scrambled_image = Image.open(file_path)

    # Image parameters
    grid_size = 5  # 5x5 grid
    piece_size = scrambled_image.width // grid_size  # Assuming square image

    # Regex pattern to extract mapping data
    pattern = re.compile(r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)")
    mapping = [tuple(map(int, match))
               for match in pattern.findall(mapping_text)]

    # Create a blank image for reconstruction
    reconstructed_image = Image.new(
        "RGB", (scrambled_image.width, scrambled_image.height))

    # Rearrange pieces based on the mapping
    for original_row, original_col, scrambled_row, scrambled_col in mapping:
        # Extract piece from scrambled image
        scrambled_x = scrambled_col * piece_size
        scrambled_y = scrambled_row * piece_size
        piece = scrambled_image.crop(
            (scrambled_x, scrambled_y, scrambled_x + piece_size, scrambled_y + piece_size))

        # Place in correct position in the reconstructed image
        original_x = original_col * piece_size
        original_y = original_row * piece_size
        reconstructed_image.paste(piece, (original_x, original_y))

    # Save the reconstructed image
    output_filename = "ga5_q10_reconstructed_image.png"
    reconstructed_image.save(output_filename)

    # Show the reconstructed image
    reconstructed_image.show()

    # Get absolute path
    new_image_path = os.path.abspath(output_filename)
    print(f"Reconstructed image saved at: {new_image_path}")

    # Convert to Base64
    with open(new_image_path, 'rb') as f:
        binary_data = f.read()
        image_b64 = base64.b64encode(binary_data).decode()

    return image_b64
