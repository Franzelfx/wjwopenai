import os
import zipfile
import argparse
import shutil

def extract_xml_from_zips(input_dir, output_dir):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Iterate through all files in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.zip'):
            zip_file_path = os.path.join(input_dir, filename)
            print(f'Extracting {zip_file_path}...')

            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                # Extract all files to a temporary directory
                temp_dir = os.path.join(input_dir, 'temp')
                os.makedirs(temp_dir, exist_ok=True)
                zip_ref.extractall(temp_dir)

                # Move all XML files to the output directory
                for extracted_file in os.listdir(temp_dir):
                    if extracted_file.endswith('.xml'):
                        src_file = os.path.join(temp_dir, extracted_file)
                        dest_file = os.path.join(output_dir, extracted_file)
                        print(f'Copying {src_file} to {dest_file}...')
                        shutil.copy(src_file, dest_file)

                # Clean up the temporary directory
                for extracted_file in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, extracted_file))
                os.rmdir(temp_dir)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Extract XML files from ZIP files.')
    parser.add_argument('-i', '--input', required=True, help='Input directory containing ZIP files.')
    parser.add_argument('-o', '--output', required=True, help='Output directory for XML files.')

    args = parser.parse_args()

    extract_xml_from_zips(args.input, args.output)

if __name__ == '__main__':
    main()
