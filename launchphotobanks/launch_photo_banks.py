#!/usr/bin/env python
"""
Launch Photo Banks - Simple script to open photobank login pages in browser.

This script reads bank URLs from a CSV file and opens them in new browser tabs.
"""
import csv
import os
import webbrowser
from typing import Dict


def load_banks_from_csv(file_path: str) -> Dict[str, str]:
    """Load bank names and URLs from CSV file.

    :param file_path: Cesta k CSV souboru s bankami
    :type file_path: str
    :returns: Slovník s názvy bank a jejich URL
    :rtype: Dict[str, str]
    """
    banks: Dict[str, str] = {}
    try:
        with open(file_path, mode="r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                banks[row["BankName"]] = row["URL"]
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return banks


def main() -> None:
    """Main function to launch photobank login pages.

    :returns: None
    :rtype: None
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(script_dir, "bank_urls.csv")

    banks = load_banks_from_csv(csv_file_path)

    for name, url in banks.items():
        try:
            webbrowser.open_new_tab(url)
            print(f"Opened {name} login page.")
        except Exception as e:
            print(f"Failed to open {name} login page. Error: {e}")


if __name__ == "__main__":
    main()
