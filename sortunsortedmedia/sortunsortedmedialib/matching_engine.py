"""
Matching engine for finding unmatched media files.
"""

import os
import logging
from typing import Dict, List, Set
from collections import defaultdict

from shared.file_operations import list_files
from sortunsortedmedialib.media_classifier import is_edited, strip_edit_tags

def build_match_dict(unsorted_files: List[str], target_files: List[str], is_edited: bool = False) -> Dict[str, List[str]]:
    """
    Builds a dictionary mapping source files to matching target files.
    
    Args:
        unsorted_files: List of paths to unsorted files
        target_files: List of paths to target files
        is_edited: Whether to consider edited files
        
    Returns:
        Dictionary mapping source file paths to lists of matching target file paths
    """
    match_dict: Dict[str, List[str]] = defaultdict(list)
    
    # Extract basenames from target files for faster matching
    target_basenames = {}
    for target_path in target_files:
        basename = os.path.basename(target_path)
        if is_edited:
            basename = strip_edit_tags(basename)
        target_basenames[basename] = target_path
    
    # Match unsorted files to target files
    for source_path in unsorted_files:
        source_basename = os.path.basename(source_path)
        if is_edited:
            source_basename = strip_edit_tags(source_basename)
        
        # Check for exact match
        if source_basename in target_basenames:
            match_dict[source_path].append(target_basenames[source_basename])
            logging.debug(f"Matched {source_path} to {target_basenames[source_basename]}")
    
    logging.info(f"Built match dictionary with {len(match_dict)} entries")
    return match_dict

def get_unmatched_sources(match_dict: Dict[str, List[str]]) -> List[str]:
    """
    Returns a list of source files that have no matches in the target directory.
    
    Args:
        match_dict: Dictionary mapping source file paths to lists of matching target file paths
        
    Returns:
        List of unmatched source file paths
    """
    unmatched = [source for source, matches in match_dict.items() if not matches]
    logging.info(f"Found {len(unmatched)} unmatched files")
    return unmatched

def find_unmatched_media(unsorted_folder: str, target_folder: str) -> Dict[str, List[str]]:
    """
    Finds media files in the unsorted folder that don't exist in the target folder.
    
    Args:
        unsorted_folder: Path to the folder with unsorted media
        target_folder: Path to the target folder
        
    Returns:
        Dictionary with three keys: 'unedited_jpg', 'unedited_other', 'edited',
        each mapping to a list of unmatched file paths
    """
    # List all files in both folders
    unsorted_files = list_files(unsorted_folder, recursive=True)
    target_files = list_files(target_folder, recursive=True)
    
    # Separate files by type
    unedited_jpg = []
    unedited_other = []
    edited_files = []
    
    for file_path in unsorted_files:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if is_edited(file_path):
            edited_files.append(file_path)
        elif ext in ['.jpg', '.jpeg']:
            unedited_jpg.append(file_path)
        else:
            unedited_other.append(file_path)
    
    # Build match dictionaries for each type
    unedited_jpg_dict = build_match_dict(unedited_jpg, target_files)
    unedited_other_dict = build_match_dict(unedited_other, target_files)
    edited_dict = build_match_dict(edited_files, target_files, is_edited=True)
    
    # Get unmatched files
    unmatched = {
        'unedited_jpg': get_unmatched_sources(unedited_jpg_dict),
        'unedited_other': get_unmatched_sources(unedited_other_dict),
        'edited': get_unmatched_sources(edited_dict)
    }
    
    logging.info(f"Found {len(unmatched['unedited_jpg'])} unmatched JPGs, "
                f"{len(unmatched['unedited_other'])} unmatched other files, "
                f"{len(unmatched['edited'])} unmatched edited files")
    
    return unmatched
