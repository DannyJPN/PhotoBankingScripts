"""
DJI Camera Model to Drone Mapping Database.

This module provides comprehensive mapping between DJI camera models (FC codes)
and their corresponding drone/camera names. Supports single-camera drones,
multi-camera systems, and interchangeable camera platforms.

Based on research conducted October 2025 from:
- DJI Forum camera model threads
- Wikimedia Commons DJI camera database
- Adobe Camera Raw community reports
- Web EXIF analysis results
"""

from typing import Dict, List, Optional, Tuple

# Single-camera consumer/prosumer drones
# Format: FC_CODE -> Drone Name
SINGLE_CAMERA_DRONES: Dict[str, str] = {
    # Mavic Series
    "FC220": "DJI Mavic Pro",
    "FC2204": "DJI Mavic 2 Zoom",
    "L1D-20c": "DJI Mavic 2 Pro",
    "L2D-20c": "DJI Mavic 3",
    "FC2403": "DJI Mavic 2 Enterprise Advanced",

    # Mini Series
    "FC7203": "DJI Mavic Mini",
    "FC7303": "DJI Mini SE",
    "FC3582": "DJI Mini 3 Pro",
    "FC3682": "DJI Mini 3",

    # Air Series
    "FC3411": "DJI Air 2S",

    # Mavic 3 Variants
    "FC4370": "DJI Mavic 3 Pro",

    # Phantom Series
    "FC200": "DJI Phantom 2 Vision",
    "FC300C": "DJI Phantom 3",
    "FC300XW": "DJI Phantom 3 Advanced",
    "FC300S": "DJI Phantom 3 Professional",
    "FC300SE": "DJI Phantom 3 Professional V2",
    "FC300X": "DJI Phantom 3 4K",
    "FC330": "DJI Phantom 4",
    "FC6310": "DJI Phantom 4 Pro",
    "FC6310S": "DJI Phantom 4 Pro V2.0",

    # OSMO
    "FC350Z": "DJI OSMO+ Zoom",
    "HG310": "DJI OSMO Pocket",

    # Unknown/Future models (placeholders based on FC pattern analysis)
    "FC2103": "DJI Drone",
    "FC2220": "DJI Drone",
    "FC3170": "DJI Drone",
    "FC4170": "DJI Drone",
    "FC4382": "DJI Matrice",
    "FC7503": "DJI Drone",
    "FC7703": "DJI Drone",
    "FC8482": "DJI Drone",
    "FC9113": "DJI Drone",
}

# Multi-camera drones (drones with multiple distinct cameras)
# Format: FC_CODE -> Camera Description
MULTI_CAMERA_DRONES: Dict[str, str] = {
    # Air 3 has wide + telephoto cameras
    "FC8282": "DJI Air 3 Wide",
    "FC8284": "DJI Air 3 Tele",
}

# Interchangeable camera systems (Zenmuse for Inspire/Matrice)
# Format: FC_CODE -> Camera Name
INTERCHANGEABLE_CAMERAS: Dict[str, str] = {
    # Zenmuse X Series (Cinema cameras)
    "FC350": "Zenmuse X3",
    "FC550": "Zenmuse X5",
    "FC6520": "Zenmuse X5S",
    "FC6540": "Zenmuse X7",

    # Zenmuse H Series (Hybrid multi-sensor)
    "ZH20T": "Zenmuse H20T",

    # Zenmuse Survey/Mapping
    "ZenmuseP1": "Zenmuse P1",
}

# Platform compatibility for interchangeable cameras
# Format: FC_CODE -> [Compatible Platforms]
CAMERA_PLATFORMS: Dict[str, List[str]] = {
    # X Series
    "FC350": ["Inspire 1"],
    "FC550": ["Inspire 1", "Inspire 2", "Matrice 200"],
    "FC6520": ["Inspire 2", "Matrice 200"],
    "FC6540": ["Inspire 2"],

    # H Series
    "ZH20T": ["Matrice 300", "Inspire 2"],

    # Survey cameras
    "ZenmuseP1": ["Matrice 300", "Matrice 350"],
}

# Integrated multi-sensor enterprise drones (built-in, non-replaceable cameras)
# Format: Model Code -> Drone Name
INTEGRATED_ENTERPRISE: Dict[str, str] = {
    "M3E": "DJI Mavic 3 Enterprise",
    "M3T": "DJI Mavic 3 Thermal",
    "M3M": "DJI Mavic 3 Multispectral",
    "M30T": "DJI Matrice 30T",
}

# Action cameras (AC series)
ACTION_CAMERAS: Dict[str, str] = {
    "AC002": "DJI Action",
    "AC003": "DJI Action",
    "AC004": "DJI Action",
}


def get_dji_drone_name(camera_model: str) -> Optional[str]:
    """
    Get drone/camera name from DJI camera model code.

    Args:
        camera_model: EXIF Model tag value (e.g., "FC3582", "ZH20T", "M3T")

    Returns:
        Human-readable drone/camera name or None if not found

    Examples:
        >>> get_dji_drone_name("FC3582")
        "DJI Mini 3 Pro"
        >>> get_dji_drone_name("FC6520")
        "DJI Inspire 2 + Zenmuse X5S"
        >>> get_dji_drone_name("FC8282")
        "DJI Air 3 Wide"
    """
    if not camera_model:
        return None

    # Check single-camera drones
    if camera_model in SINGLE_CAMERA_DRONES:
        return SINGLE_CAMERA_DRONES[camera_model]

    # Check multi-camera drones
    if camera_model in MULTI_CAMERA_DRONES:
        return MULTI_CAMERA_DRONES[camera_model]

    # Check interchangeable cameras
    if camera_model in INTERCHANGEABLE_CAMERAS:
        camera_name = INTERCHANGEABLE_CAMERAS[camera_model]
        platforms = CAMERA_PLATFORMS.get(camera_model, [])
        if platforms:
            # Use primary platform (first in list)
            return f"DJI {platforms[0]} + {camera_name}"
        return f"DJI {camera_name}"

    # Check integrated enterprise
    if camera_model in INTEGRATED_ENTERPRISE:
        return INTEGRATED_ENTERPRISE[camera_model]

    # Check action cameras
    if camera_model in ACTION_CAMERAS:
        return ACTION_CAMERAS[camera_model]

    return None


def get_dji_camera_info(camera_model: str) -> Optional[Tuple[str, str, bool]]:
    """
    Get detailed information about DJI camera model.

    Args:
        camera_model: EXIF Model tag value

    Returns:
        Tuple of (drone_name, camera_type, is_interchangeable) or None
        camera_type: "single", "multi", "interchangeable", "integrated", "action"

    Examples:
        >>> get_dji_camera_info("FC3582")
        ("DJI Mini 3 Pro", "single", False)
        >>> get_dji_camera_info("FC6520")
        ("DJI Inspire 2 + Zenmuse X5S", "interchangeable", True)
    """
    if not camera_model:
        return None

    if camera_model in SINGLE_CAMERA_DRONES:
        return (SINGLE_CAMERA_DRONES[camera_model], "single", False)

    if camera_model in MULTI_CAMERA_DRONES:
        return (MULTI_CAMERA_DRONES[camera_model], "multi", False)

    if camera_model in INTERCHANGEABLE_CAMERAS:
        camera_name = INTERCHANGEABLE_CAMERAS[camera_model]
        platforms = CAMERA_PLATFORMS.get(camera_model, [])
        if platforms:
            full_name = f"DJI {platforms[0]} + {camera_name}"
        else:
            full_name = f"DJI {camera_name}"
        return (full_name, "interchangeable", True)

    if camera_model in INTEGRATED_ENTERPRISE:
        return (INTEGRATED_ENTERPRISE[camera_model], "integrated", False)

    if camera_model in ACTION_CAMERAS:
        return (ACTION_CAMERAS[camera_model], "action", False)

    return None


def is_dji_camera(camera_model: str) -> bool:
    """
    Check if camera model is a known DJI camera.

    Args:
        camera_model: EXIF Model tag value

    Returns:
        True if camera model is in DJI database
    """
    return get_dji_drone_name(camera_model) is not None