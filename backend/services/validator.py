import os
import json
import re
from typing import Dict, Any, Optional
from loguru import logger

class JSONValidator:
    @staticmethod
    def decode_unicode_in_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dekodiert rekursiv Unicode-Escape-Sequenzen in den JSON-Daten zu tatsächlichen Zeichen.
        :param json_data: Die zu dekodierenden JSON-Daten (als Dictionary).
        :return: Dekodierte JSON-Daten mit allen zu Zeichen konvertierten Unicode-Sequenzen.
        """
        if isinstance(json_data, dict):
            return {key: JSONValidator.decode_unicode_in_json(value) for key, value in json_data.items()}
        elif isinstance(json_data, list):
            return [JSONValidator.decode_unicode_in_json(element) for element in json_data]
        elif isinstance(json_data, str):
            try:
                # Korrekte Dekodierung von Unicode-Escapes in UTF-8
                return json_data.encode('utf-8').decode('utf-8')
            except UnicodeDecodeError:
                # Falls die Dekodierung fehlschlägt, wird der String unverändert zurückgegeben
                return json_data
        else:
            return json_data

    @staticmethod
    def try_decode_content(content: bytes) -> str:
        """
        Versucht, den Inhalt mit utf-8 zu dekodieren, fällt auf ISO-8859-1 zurück, wenn utf-8 fehlschlägt.
        :param content: Der zu dekodierende Inhalt.
        :return: Der dekodierte String.
        """
        if content is None:
            logger.error("Kein Inhalt zum Dekodieren bereitgestellt.")
            return ""

        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            logger.warning("UTF-8-Dekodierung fehlgeschlagen, versuche ISO-8859-1")
            return content.decode('ISO-8859-1')

    @staticmethod
    def save_cleaned_json(output_dir: str, filename: str, content: Optional[bytes], success: bool = True) -> str:
        """
        Speichert den bereinigten JSON-Inhalt.
        :param output_dir: Das Basisverzeichnis für Ausgabedateien.
        :param filename: Der Name der zu speichernden Datei.
        :param content: Der zu speichernde JSON-Inhalt.
        :param success: Ein Flag, das angibt, ob die Datei im Erfolg- oder Fehlschlagverzeichnis gespeichert wird.
        :return: Der Pfad zur gespeicherten JSON-Datei.
        """
        if content is None:
            logger.error(f"JSON für {filename} kann nicht gespeichert werden. Kein Inhalt bereitgestellt.")
            return ""

        decoded_content = JSONValidator.try_decode_content(content)
        cleaned_content = JSONValidator.clean_json_content(decoded_content)

        sub_dir = "success" if success else "fail"
        full_output_dir = os.path.join(output_dir, sub_dir)
        os.makedirs(full_output_dir, exist_ok=True)

        try:
            # Versucht, den bereinigten JSON-Inhalt zu dekodieren
            json_data = json.loads(cleaned_content)
            
            # Add the "Scan" (filename) to the JSON content
            json_data['Scan'] = filename
            
            decoded_json_data = JSONValidator.decode_unicode_in_json(json_data)
            output_path = os.path.join(full_output_dir, f"{filename}.json")
            
            # Speichert als JSON
            with open(output_path, "w", encoding="utf-8") as json_file:
                json.dump(decoded_json_data, json_file, indent=4, ensure_ascii=False)
                
            logger.info(f"JSON-Datei gespeichert unter {output_path}")
            return output_path

        except json.JSONDecodeError as e:
            logger.error(f"Fehler beim Dekodieren des JSON für {filename}: {str(e)}")
            
            # Speichert den Originalinhalt im Fehlschlagverzeichnis
            fail_output_path = os.path.join(full_output_dir, f"{filename}_invalid.json")
            with open(fail_output_path, "w", encoding="utf-8") as json_file:
                json_file.write(cleaned_content)
                
            logger.info(f"Ungültiger JSON-Inhalt in der Datei gespeichert: {fail_output_path}")
            return fail_output_path
