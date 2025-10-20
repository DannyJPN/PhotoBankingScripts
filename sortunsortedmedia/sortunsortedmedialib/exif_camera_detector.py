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
from shared.exif_downloader import ensure_exiftool
from sortunsortedmedialib.dji_camera_mapping import get_dji_drone_name, is_dji_camera


class EXIFCameraDetector:
    """EXIF camera detector using external EXIFtool."""
    
    def __init__(self):
        """Initialize with EXIFtool path."""
        self.exiftool_path = self._find_or_setup_exiftool()
    
    def _find_or_setup_exiftool(self) -> Optional[str]:
        """
        Get exiftool path using shared ensure_exiftool function.
        
        Returns:
            Path to exiftool.exe or None if not found
        """
        try:
            return ensure_exiftool()
        except Exception as e:
            logging.error(f"Failed to get ExifTool path: {e}")
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
        except (OSError, PermissionError, FileNotFoundError) as e:
            logging.error(f"File system error during EXIF extraction for {file_path}: {e}")
            return None
        except Exception as e:
            # Log with exception type for better debugging
            logging.error(f"Unexpected {type(e).__name__} in EXIF extraction for {file_path}: {e}", exc_info=True)
            return None
    
    def _construct_camera_name(self, make: str, model: str, software: str) -> Optional[str]:
        """
        Construct camera name from EXIF data with enhanced detection.

        Combines manufacturer information with model details, with special handling for:
        - DJI drones (uses comprehensive FC code database)
        - Samsung phones (normalizes SM- prefix)
        - Sony cameras (keeps DSC- prefix for compatibility)
        - Nikon cameras (normalizes NIKON prefix)
        - Bunaty trail cameras (detects from Software tag)

        Args:
            make: Camera manufacturer from EXIF Make tag
            model: Camera model from EXIF Model tag
            software: Software/firmware from EXIF Software tag

        Returns:
            Constructed camera name matching existing folder structure, or None

        Examples:
            >>> _construct_camera_name("DJI", "FC3582", "")
            "DJI Mini 3 Pro"
            >>> _construct_camera_name("samsung", "SM-J320FN", "")
            "Samsung J320FN"
        """
        # Clean up the strings
        make = make.replace("Corporation", "").replace("CORPORATION", "").strip()
        model = model.strip()
        software = software.strip()

        # === DJI Drones - Use comprehensive database ===
        if make.lower() == "dji":
            if model:
                # Try DJI database lookup first
                dji_name = get_dji_drone_name(model)
                if dji_name:
                    return dji_name
                # Fallback: unknown DJI model
                return f"DJI Drone ({model})"
            else:
                return "DJI Drone"

        # === Samsung - Normalize model numbers ===
        # EXIF: "SM-J320FN" → Folder: "Samsung J320FN"
        elif make.lower() in ["samsung", "samsung electronics"]:
            if model:
                # Remove SM- prefix if present
                normalized = model.replace("SM-", "").replace("sm-", "")
                return f"Samsung {normalized}"
            else:
                return "Samsung"

        # === Sony - Keep DSC prefix for compatibility ===
        # EXIF: "DSC-W810" → Folder: "Sony CyberShot W810"
        # Note: Some existing folders use "Sony CyberShot W810", others just "DSC-W810"
        elif make.lower() == "sony":
            if model:
                # Keep model as-is for Sony (DSC- prefix needed)
                if "DSC-" in model or "dsc-" in model.lower():
                    # Check if it's a CyberShot (common series)
                    return f"Sony {model}"
                return f"Sony {model}"

        # === Nikon - Normalize NIKON prefix ===
        # EXIF: "NIKON Z 50" → Folder: "Nikon Z50"
        elif make.lower() == "nikon":
            if model:
                # Remove manufacturer name from model if present
                normalized = model.replace("NIKON", "").replace("Nikon", "").strip()
                # Remove extra spaces
                normalized = " ".join(normalized.split())
                return f"Nikon {normalized}"

        # === Realme - Direct format ===
        # EXIF: "realme 8" → Folder: "Realme 8"
        elif make.lower() == "realme":
            if model:
                # Check if model already contains "Realme"
                if model.lower().startswith("realme"):
                    # Model already contains "Realme", capitalize and return as-is
                    return model[0].upper() + model[1:]
                # Otherwise prepend "Realme"
                if model[0].islower():
                    model = model[0].upper() + model[1:]
                return f"Realme {model}"




        # === Canon ===
        elif make.lower() == "canon":
            if model:
                return f"Canon {model}"

        # === Apple - iPhone/iPad ===
        elif make.lower() == "apple":
            if model:
                return f"Apple {model}"

        # === Bunaty Trail Cameras - Detect from Software tag ===
        # These cameras use generic Make/Model but specific Software strings
        # Check Bunaty BEFORE generic trail camera check
        elif "bunaty" in software.lower() or "bunaty" in make.lower() or "bunaty" in model.lower():
            # Existing folders: "Bunaty Micro 4K", "Bunaty WiFi Solar"
            if "micro" in software.lower() or "4k" in software.lower() or "bv18ad" in software.lower():
                return "Bunaty Micro 4K"
            elif "wifi" in software.lower() or "solar" in software.lower() or "rd7010wf" in model.lower():
                return "Bunaty WiFi Solar"
            else:
                return "Bunaty"

        # === Trail Camera with Bunaty model detection ===
        # Bunaty WiFi Solar uses "Trail camera" as make and "RD7010WF" as model
        elif make.lower() == "trail camera":
            if "rd7010wf" in model.lower():
                return "Bunaty WiFi Solar"
            elif model:
                # Check software for Bunaty signatures
                if "bunaty" in software.lower():
                    if "micro" in software.lower() or "4k" in software.lower():
                        return "Bunaty Micro 4K"
                    else:
                        return "Bunaty WiFi Solar"
                return f"Trail Camera {model}"

        # === Acer ===
        elif "acer" in make.lower():
            if model:
                return f"Acer {model}"
            else:
                return "Acer 10"

        # === Huawei ===
        elif make.lower() == "huawei":
            if model:
                # Normalize HUAWEI prefix
                normalized = model.replace("HUAWEI", "").replace("Huawei", "").strip()
                if normalized:
                    return f"Huawei {normalized}"
                return f"Huawei {model}"

        # === iCatch (action cameras) ===
        elif "icatch" in make.lower():
            # Check software for brand
            if "bunaty" in software.lower():
                return "Bunaty Micro 4K"
            return "iCatch Camera"

        # === Generic construction ===
        if make and model:
            # Remove duplicate manufacturer name from model
            if make.lower() in model.lower():
                return model
            else:
                return f"{make} {model}"
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