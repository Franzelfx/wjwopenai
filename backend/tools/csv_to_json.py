import os
import csv
import json
from loguru import logger

# Function to convert a single CSV file to JSON
def csv_to_json(csv_file, output_json_folder):
    try:
        # Create output JSON file path
        base_name = os.path.basename(csv_file)
        json_file = os.path.join(output_json_folder, base_name.replace(".csv", ".json"))

        # Read the CSV file and convert to JSON
        with open(csv_file, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            rows = list(csv_reader)

        # Write JSON data
        with open(json_file, mode='w', encoding='utf-8') as json_f:
            json.dump(rows, json_f, indent=4)

        logger.info(f"Successfully converted {csv_file} to {json_file}")
    except Exception as e:
        logger.error(f"Failed to convert {csv_file} to JSON: {str(e)}")

# Function to process all CSV files in a folder
def process_folder(csv_folder, json_folder):
    # Ensure the JSON folder exists
    if not os.path.exists(json_folder):
        os.makedirs(json_folder)

    # Get list of all CSV files in the folder
    csv_files = [f for f in os.listdir(csv_folder) if f.endswith(".csv")]
    
    if not csv_files:
        logger.warning(f"No CSV files found in the directory {csv_folder}.")
        return

    for csv_file in csv_files:
        csv_path = os.path.join(csv_folder, csv_file)
        csv_to_json(csv_path, json_folder)

# Main entry point
if __name__ == "__main__":
    # Define the folder paths
    csv_folder = "./geodata"   # Folder containing the CSV files
    json_folder = "./geodata/json"     # Folder where JSON files will be saved

    logger.info(f"Processing all CSV files in {csv_folder} and saving JSON to {json_folder}")
    process_folder(csv_folder, json_folder)
