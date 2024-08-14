import os
import json
from typing import Dict, Any
from loguru import logger
import re
from typing import Optional

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
    def try_decode_content(content: bytes) -> str:
        """
        Tries to decode content using utf-8, falls back to ISO-8859-1 if utf-8 fails.
        :param content: The content to be decoded.
        :return: The decoded string.
        """
        if content is None:
            logger.error("No content provided to decode.")
            return ""

        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            logger.warning("UTF-8 decoding failed, trying ISO-8859-1")
            return content.decode('ISO-8859-1')

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
    def save_cleaned_json(output_dir: str, filename: str, content: Optional[bytes], success: bool = True) -> str:
        """
        Saves the cleaned JSON content.
        :param output_dir: The base directory for output files.
        :param filename: The name of the file to save.
        :param content: The JSON content to be saved.
        :param success: A flag to indicate if the file is to be saved in the success or fail directory.
        :return: The path to the saved JSON file.
        """
        if content is None:
            logger.error(f"Cannot save JSON for {filename}. No content provided.")
            return ""

        decoded_content = JSONValidator.try_decode_content(content)
        cleaned_content = JSONValidator.clean_json_content(decoded_content)
        
        # Decode any Unicode escape sequences in the JSON data
        try:
            json_data = json.loads(cleaned_content)
            decoded_json_data = JSONValidator.decode_unicode_in_json(json_data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON for {filename}: {str(e)}")
            return ""

        # Determine the directory to save the cleaned JSON
        sub_dir = "success" if success else "fail"
        full_output_dir = os.path.join(output_dir, sub_dir)
        os.makedirs(full_output_dir, exist_ok=True)

        # Save as JSON
        output_path = os.path.join(full_output_dir, f"{filename}.json")
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(decoded_json_data, json_file, indent=4, ensure_ascii=False)
        
        logger.info(f"JSON file saved to {output_path}")
        return output_path
