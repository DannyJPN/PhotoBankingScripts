import pandas as pd
import logging
import sys
from tqdm import tqdm
import time

def load_csv(filepath):
    try:
        df = pd.read_csv(filepath, na_filter=False)
        logging.info(f"CSV file loaded successfully: {filepath}")

        media_items = []
        total_rows = len(df)

        with tqdm(total=total_rows, desc="Loading CSV", unit="row") as pbar:
            for index, row in df.iterrows():
                media_items.append(row.to_dict())
                pbar.update(1)
                #time.sleep(0.01)  # Simulate time delay for each row

        logging.debug(f"First few media items: {media_items[:5]}")
        return media_items
    except Exception as e:
        logging.error(f"Error loading CSV file: {e}", exc_info=True)
        sys.exit(1)