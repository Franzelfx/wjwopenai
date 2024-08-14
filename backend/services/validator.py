import os
import json
from typing import Dict, Any
from loguru import logger
from pathlib import Path
import re
import io
import csv

class JSONValidator:
    @staticmethod
    def clean_json_content(content: str) -> str:
        """
        Cleans the JSON content by removing unnecessary characters, such as code block markers.
        :param content: The JSON string to be cleaned.
        :return: A cleaned JSON string.
        """
        # Remove common JSON code block markers (like ```json ... ```)
        content = re.sub(r'```json\s*|\s*```', '', content)

        # Trim leading and trailing whitespace
        content = content.strip()

        return content

    @staticmethod
    def decode_unicode_in_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively decode Unicode escape sequences in the JSON data to actual characters.
        :param json_data: The JSON data (as a dictionary) to decode.
        :return: Decoded JSON data with all Unicode sequences converted to characters.
        """
        if isinstance(json_data, dict):
            return {key: JSONValidator.decode_unicode_in_json(value) for key, value in json_data.items()}
        elif isinstance(json_data, list):
            return [JSONValidator.decode_unicode_in_json(element) for element in json_data]
        elif isinstance(json_data, str):
            return json_data.encode().decode('unicode_escape')
        else:
            return json_data

    @staticmethod
    def is_valid_json(content: str) -> bool:
        """
        Validates if the given content is a valid JSON string after cleaning.
        :param content: The string to be validated as JSON.
        :return: True if valid JSON, False otherwise.
        """
        try:
            cleaned_content = JSONValidator.clean_json_content(content)
            json.loads(cleaned_content)
            return True
        except ValueError as e:
            logger.error(f"Invalid JSON content: {str(e)}")
            return False

    @staticmethod
    def json_to_csv(json_data: Dict[str, Any]) -> str:
        """
        Converts JSON data to a CSV string.
        :param json_data: The JSON data (as a dictionary) to convert to CSV.
        :return: A string representing the CSV content.
        """
        # Create an in-memory text stream
        output = io.StringIO()
        csv_writer = csv.writer(output)

        # Assume that the JSON data is a dictionary with a consistent structure
        if isinstance(json_data, list):
            # If the JSON data is a list, assume it's a list of dictionaries
            headers = json_data[0].keys()
            csv_writer.writerow(headers)
            for entry in json_data:
                csv_writer.writerow(entry.values())
        elif isinstance(json_data, dict):
            # If it's a dictionary, write keys as headers and values as a single row
            headers = json_data.keys()
            csv_writer.writerow(headers)
            csv_writer.writerow(json_data.values())
        else:
            raise ValueError("Unsupported JSON format for CSV conversion")

        # Get the CSV content as a string
        csv_content = output.getvalue()
        output.close()

        return csv_content

    @staticmethod
    def save_cleaned_json(output_dir: str, filename: str, content: str, convert_to_csv=False):
        """
        Saves the cleaned JSON content or converts it to CSV before saving.
        :param output_dir: The base directory for output files.
        :param filename: The name of the file to save.
        :param content: The JSON content to be saved.
        :param convert_to_csv: A flag to convert JSON content to CSV before saving.
        """
        cleaned_content = JSONValidator.clean_json_content(content)
        
        # Convert the cleaned content back to a dictionary to save it as a JSON file
        json_data = json.loads(cleaned_content)

        # Decode any Unicode escape sequences in the JSON data
        decoded_json_data = JSONValidator.decode_unicode_in_json(json_data)

        # Determine the directory to save the cleaned JSON or CSV
        full_output_dir = os.path.join(output_dir, "success")
        os.makedirs(full_output_dir, exist_ok=True)
        
        if convert_to_csv:
            # Convert to CSV
            csv_content = JSONValidator.json_to_csv(decoded_json_data)
            output_path = os.path.join(full_output_dir, f"{filename}.csv")
            with open(output_path, "w", encoding="utf-8") as csv_file:
                csv_file.write(csv_content)
        else:
            # Save as JSON
            output_path = os.path.join(full_output_dir, f"{filename}.json")
            with open(output_path, "w", encoding="utf-8") as json_file:
                json.dump(decoded_json_data, json_file, indent=4, ensure_ascii=False)
        
        logger.info(f"File saved to {output_path}")
