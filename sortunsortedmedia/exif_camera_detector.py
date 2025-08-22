"""
EXIF camera detection using external EXIFtool.
Provides maximum format support for all media types including RAW, videos, audio, etc.
"""

import os
import subprocess
import json
import logging
import shutil
from typing import Optional, Dict, Any


class EXIFCameraDetector:
    """EXIF camera detector using external EXIFtool."""
    
    def __init__(self):
        """Initialize with EXIFtool path."""
        self.exiftool_path = self._find_or_setup_exiftool()
    
    def _find_or_setup_exiftool(self) -> Optional[str]:
        """
        Find exiftool.exe in F:/Dropbox/exiftool-12.30 directory.
        Fixed path, no downloading or searching.
        
        Returns:
            Path to exiftool.exe or None if not found
        """
        # Fixed path to ExifTool 12.30
        exif_dir = "F:/Dropbox/exiftool-12.30"
        
        if not os.path.exists(exif_dir):
            logging.warning(f"ExifTool directory not found: {exif_dir}")
            return None
            
        # Try to find exiftool.exe
        exiftool_exe = os.path.join(exif_dir, "exiftool.exe")
        if os.path.exists(exiftool_exe):
            logging.info(f"Found exiftool.exe at: {exiftool_exe}")
            return exiftool_exe
        
        # Try to find exiftool(-k).exe and rename it (remove -k from name)
        exiftool_k = os.path.join(exif_dir, "exiftool(-k).exe")
        if os.path.exists(exiftool_k):
            try:
                # Rename the file to remove (-k) from the name
                os.rename(exiftool_k, exiftool_exe)
                logging.info(f"Renamed {exiftool_k} to {exiftool_exe}")
                return exiftool_exe
            except (OSError, PermissionError) as e:
                logging.warning(f"Could not rename exiftool(-k).exe to exiftool.exe: {e}")
                # Try to use the original file directly
                return exiftool_k
        
        logging.warning("ExifTool not found in the specified directory")
        return None
    
    def get_camera_from_exif(self, file_path: str) -> Optional[str]:
        """
        Extract camera information from EXIF data.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            Camera name or None if not detected
        """
        if not self.exiftool_path or not os.path.exists(file_path):
            return None
            
        try:
            # Run EXIFtool to get camera information
            cmd = [
                self.exiftool_path,
                "-j",  # JSON output
                "-Make",
                "-Model", 
                "-Software",
                "-Creator",
                "-Artist",
                "-Copyright",
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                logging.debug(f"EXIFtool failed for {file_path}: {result.stderr}")
                return None
            
            # Parse JSON output
            exif_data = json.loads(result.stdout)
            if not exif_data:
                return None
                
            metadata = exif_data[0]  # First (and only) file
            
            # Try to construct camera name from Make and Model
            make = metadata.get("Make", "").strip()
            model = metadata.get("Model", "").strip()
            software = metadata.get("Software", "").strip()
            
            camera_name = self._construct_camera_name(make, model, software)
            
            if camera_name:
                logging.info(f"EXIF detected camera for {file_path}: {camera_name}")
                return camera_name
            
            return None
            
        except subprocess.TimeoutExpired:
            logging.warning(f"EXIFtool timeout for {file_path}")
            return None
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError) as e:
            logging.debug(f"EXIF extraction failed for {file_path}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in EXIF extraction for {file_path}: {e}")
            return None
    
    def _construct_camera_name(self, make: str, model: str, software: str) -> Optional[str]:
        """
        Construct camera name from EXIF data.
        
        Args:
            make: Camera manufacturer
            model: Camera model
            software: Software used
            
        Returns:
            Constructed camera name or None
        """
        # Clean up the strings
        make = make.replace("Corporation", "").replace("CORPORATION", "").strip()
        model = model.strip()
        software = software.strip()
        
        # Special handling for known manufacturers
        if make.lower() in ["samsung", "samsung electronics"]:
            if model:
                return f"Samsung {model}"
                
        elif make.lower() in ["realme"]:
            if model:
                return f"Realme {model}"
                
        elif make.lower() in ["nikon"]:
            if model:
                return f"Nikon {model}"
                
        elif make.lower() in ["sony"]:
            if model:
                return f"Sony {model}"
                
        elif make.lower() in ["dji"]:
            if model:
                return f"DJI {model}"
            else:
                return "DJI Drone"
                
        elif make.lower() in ["canon"]:
            if model:
                return f"Canon {model}"
                
        elif "bunaty" in software.lower() or "bunaty" in make.lower() or "bunaty" in model.lower():
            if "micro" in model.lower() or "4k" in model.lower():
                return "Bunaty Micro 4K"
            elif "wifi" in model.lower() or "solar" in model.lower():
                return "Bunaty WiFi Solar"
            else:
                return "Bunaty"
                
        elif "acer" in make.lower():
            if model:
                return f"Acer {model}"
            else:
                return "Acer 10"
        
        # Generic construction
        if make and model:
            # Remove duplicate words
            if make.lower() not in model.lower():
                return f"{make} {model}"
            else:
                return model
        elif model:
            return model
        elif make:
            return make
            
        return None


# Global instance
_detector = EXIFCameraDetector()


def detect_camera_from_exif(file_path: str) -> Optional[str]:
    """
    Convenience function to detect camera from EXIF data.
    
    Args:
        file_path: Path to the media file
        
    Returns:
        Camera name or None if not detected
    """
    return _detector.get_camera_from_exif(file_path)


def combine_regex_and_exif_detection(file_path: str, regex_camera: Optional[str]) -> str:
    """
    Combine regex and EXIF detection with conflict resolution.
    
    Args:
        file_path: Path to the media file
        regex_camera: Camera detected by regex patterns
        
    Returns:
        Final camera name
    """
    exif_camera = detect_camera_from_exif(file_path)
    
    # If both methods agree or only one detected something
    if not regex_camera and not exif_camera:
        return "Unknown"
    elif not regex_camera:
        return exif_camera
    elif not exif_camera:
        return regex_camera
    elif regex_camera == exif_camera:
        return regex_camera
    else:
        # Conflict - prefer EXIF data as it's more reliable
        logging.info(f"Camera detection conflict for {file_path}: regex='{regex_camera}', exif='{exif_camera}' - using EXIF")
        return exif_camera