import webbrowser
import csv
import os

def load_banks_from_csv(file_path):
    banks = {}
    try:
        with open(file_path, mode='r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                banks[row['BankName']] = row['URL']
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return banks

def main():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the full path to the CSV file
    csv_file_path = os.path.join(script_dir, 'bank_urls.csv')

    banks = load_banks_from_csv(csv_file_path)

    for name, url in banks.items():
        try:
            webbrowser.open_new_tab(url)
            print(f"Opened {name} login page.")
        except Exception as e:
            print(f"Failed to open {name} login page. Error: {e}")

if __name__ == "__main__":
    main()