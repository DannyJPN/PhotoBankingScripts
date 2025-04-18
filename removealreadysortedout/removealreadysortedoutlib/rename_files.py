import os
import logging

def rename_files(folder_path):
    for root, _, files in os.walk(folder_path):
        for name in files:
            if name.startswith("_NIK"):
                new_name = "NIK_" + name[4:]
                old_path = os.path.join(root, name)
                new_path = os.path.join(root, new_name)
                try:
                    os.rename(old_path, new_path)
                    logging.info(f"Renamed {old_path} to {new_path}")
                except Exception as e:
                    logging.error(f"Error renaming {old_path} to {new_path}: {e}")
