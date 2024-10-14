import os
import csv
import xml.etree.ElementTree as ET
from pyproj import Proj, transform
import googlemaps
import argparse
import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from loguru import logger

# Initialize Google Maps API client with your API key
API_KEY = 'AIzaSyAds3RDkbxYNJYAfpYaVlKKe5cwiX28w5g'
gmaps = googlemaps.Client(key=API_KEY)

# Set up a retry strategy for handling potential network issues
retry_strategy = Retry(
    total=5,  # Retry up to 5 times
    backoff_factor=1,  # Wait 1 second between retries
    status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
    allowed_methods=["GET"]  # Retry only on GET requests
)

# Configure HTTP session with retry strategy
http_adapter = HTTPAdapter(max_retries=retry_strategy)
gmaps.session.mount("https://", http_adapter)
gmaps.session.mount("http://", http_adapter)

# Function to reverse geocode with retries
def reverse_geocode(lat, lon):
    try:
        reverse_geocode_result = gmaps.reverse_geocode((lat, lon))
        if reverse_geocode_result:
            return reverse_geocode_result[0]
        return None
    except Exception as e:
        logger.error(f"Error during reverse geocoding: {e}")
        return None

# Function to parse the XML and extract coordinates
def parse_gml_file(gml_file):
    try:
        tree = ET.parse(gml_file)
        root = tree.getroot()

        namespaces = {
            'gml': 'http://www.opengis.net/gml/3.2'
        }
        
        # Find all gml:posList entries which contain coordinates
        pos_lists = root.findall('.//gml:posList', namespaces)

        # For each posList, extract Easting and Northing
        coordinates = []
        for pos_list in pos_lists:
            easting, northing = map(float, pos_list.text.strip().split()[:2])
            coordinates.append((easting, northing))

        return coordinates
    except ET.ParseError as e:
        logger.error(f"Error parsing GML file {gml_file}: {e}")
        return []

# Function to convert UTM to WGS84
def convert_utm_to_wgs84(easting, northing, zone=32):
    proj_utm = Proj(proj='utm', zone=zone, ellps='WGS84')
    proj_latlon = Proj(proj='latlong', datum='WGS84')
    
    lon, lat = transform(proj_utm, proj_latlon, easting, northing)
    return lat, lon

# Function to get the last processed row from the CSV
def get_last_processed_row(csv_file):
    if not os.path.exists(csv_file):
        return 0  # If file doesn't exist, start from the beginning

    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        return sum(1 for row in file) - 1  # Subtract header row

# Function to generate a unique CSV filename with timestamp
def generate_csv_filename(gml_file):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.splitext(gml_file)[0] + f'_geocoded_results_{timestamp}.csv'

# Function to process a single file
def process_file(gml_file):
    logger.info(f"Processing file: {gml_file}")
    
    # Parse the coordinates from the GML file
    coordinates = parse_gml_file(gml_file)

    # Generate a unique output CSV file name
    output_file = generate_csv_filename(gml_file)

    # Get the last processed row in the CSV (no overwrite behavior)
    last_processed_row = get_last_processed_row(output_file)
    logger.info(f"Last processed row: {last_processed_row + 1} (starting from index)")

    # Open the CSV file for writing (append mode)
    with open(output_file, mode='a', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file)

        # If this is a new file, write the header
        if last_processed_row == 0:
            csv_writer.writerow(['Easting', 'Northing', 'Latitude', 'Longitude', 'Address', 'City', 'Country'])
        
        # Log the total number of coordinates to process and the starting row
        total_coordinates = len(coordinates)
        logger.info(f"Total coordinates to process: {total_coordinates}")
        logger.info(f"Starting from row: {last_processed_row + 1}")
        
        # Dealay for 5 seconds before starting the processing
        logger.info("Waiting for 5 seconds before starting the processing...")

        # Loop through all coordinates and reverse geocode them starting from last processed row
        for idx, (easting, northing) in enumerate(coordinates):
            if idx < last_processed_row:
                continue  # Skip rows that were already processed

            logger.info(f"Processing row {idx + 1}: UTM-Koordinaten: Easting={easting}, Northing={northing}")
            
            # Convert UTM to WGS84
            lat, lon = convert_utm_to_wgs84(easting, northing)
            logger.info(f"WGS84-Koordinaten: Latitude={lat}, Longitude={lon}")
            
            # Reverse geocode with retry mechanism
            location_data = reverse_geocode(lat, lon)
            if location_data:
                address = location_data.get('formatted_address', 'N/A')
                city = next((comp['long_name'] for comp in location_data['address_components'] if 'locality' in comp['types']), 'N/A')
                country = next((comp['long_name'] for comp in location_data['address_components'] if 'country' in comp['types']), 'N/A')
            else:
                address = city = country = 'N/A'
            
            # Write the data to CSV
            csv_writer.writerow([easting, northing, lat, lon, address, city, country])

            logger.info(f"Address: {address}, City: {city}, Country: {country}\n")

    logger.info(f"Results saved to {output_file}")

# Function to process all XML files in the directory
def process_all_files_in_directory(directory):
    # Iterate over all XML files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            gml_file_path = os.path.join(directory, filename)
            process_file(gml_file_path)

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Parse GML files and reverse geocode coordinates.')
    parser.add_argument('-d', '--directory', help='Directory containing GML files', required=False)
    parser.add_argument('-f', '--file', help='Path to a single GML file', required=False)
    args = parser.parse_args()

    # Check if directory or file is provided
    if args.directory:
        if os.path.isdir(args.directory):
            process_all_files_in_directory(args.directory)
        else:
            logger.error(f"Invalid directory path: {args.directory}. Please provide a valid directory.")
    elif args.file and os.path.isfile(args.file):
        # Process a single file
        process_file(args.file)
    else:
        logger.error(f"Invalid input. Please provide either a GML file using -f or a directory using -d.")
