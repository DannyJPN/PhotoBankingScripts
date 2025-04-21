"""
Media loader module for detecting and loading different types of media files.
"""
import os
import logging
from typing import Dict, Any, Optional, Tuple
import mimetypes
from PIL import Image
import cv2
import numpy as np

from core.constants import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, VECTOR_EXTENSIONS

class MediaLoader:
    """Class for loading and processing different types of media files."""
    
    def __init__(self):
        """Initialize the media loader."""
        # Initialize mimetypes
        mimetypes.init()
        logging.debug("MediaLoader initialized")
    
    def get_media_type(self, file_path: str) -> str:
        """
        Determine the type of media file.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            str: One of 'image', 'video', 'vector', or 'unknown'
        """
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return "unknown"
        
        # Check by extension first
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in IMAGE_EXTENSIONS:
            return "image"
        elif ext in VIDEO_EXTENSIONS:
            return "video"
        elif ext in VECTOR_EXTENSIONS:
            return "vector"
        
        # If extension check fails, try to determine by content
        try:
            mime_type = mimetypes.guess_type(file_path)[0]
            if mime_type:
                if mime_type.startswith('image'):
                    return "image"
                elif mime_type.startswith('video'):
                    return "video"
                elif mime_type in ['application/postscript', 'image/svg+xml']:
                    return "vector"
        except Exception as e:
            logging.error(f"Error determining mime type for {file_path}: {e}")
        
        return "unknown"
    
    def load_image(self, file_path: str) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        """
        Load an image file and extract basic metadata.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Tuple containing:
                - numpy array of the image (or None if loading fails)
                - dictionary of metadata (width, height, etc.)
        """
        metadata = {}
        image = None
        
        try:
            # Try loading with PIL first for metadata
            with Image.open(file_path) as img:
                metadata['width'] = img.width
                metadata['height'] = img.height
                metadata['format'] = img.format
                metadata['mode'] = img.mode
                
                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = {
                        ExifTags.TAGS[k]: v
                        for k, v in img._getexif().items()
                        if k in ExifTags.TAGS
                    }
                    metadata['exif'] = exif
            
            # Load with OpenCV for processing
            image = cv2.imread(file_path)
            if image is not None:
                # Convert from BGR to RGB
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
        except Exception as e:
            logging.error(f"Error loading image {file_path}: {e}")
            return None, {'error': str(e)}
        
        return image, metadata
    
    def load_video(self, file_path: str, sample_rate: int = 1) -> Tuple[Optional[list], Dict[str, Any]]:
        """
        Load a video file and extract frames and metadata.
        
        Args:
            file_path: Path to the video file
            sample_rate: Number of frames to extract per second
            
        Returns:
            Tuple containing:
                - list of sampled frames as numpy arrays (or None if loading fails)
                - dictionary of metadata (width, height, fps, duration, etc.)
        """
        metadata = {}
        frames = []
        
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                logging.error(f"Could not open video file: {file_path}")
                return None, {'error': 'Could not open video file'}
            
            # Extract metadata
            metadata['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            metadata['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            metadata['fps'] = cap.get(cv2.CAP_PROP_FPS)
            metadata['frame_count'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            metadata['duration'] = metadata['frame_count'] / metadata['fps'] if metadata['fps'] > 0 else 0
            
            # Calculate frame sampling
            if sample_rate > 0 and metadata['fps'] > 0:
                frame_interval = int(metadata['fps'] / sample_rate)
                if frame_interval < 1:
                    frame_interval = 1
            else:
                frame_interval = 30  # Default: 1 frame every 30 frames
            
            # Extract frames
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    # Convert from BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(frame_rgb)
                
                frame_count += 1
            
            cap.release()
            
        except Exception as e:
            logging.error(f"Error loading video {file_path}: {e}")
            return None, {'error': str(e)}
        
        return frames, metadata
    
    def load_vector(self, file_path: str) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        """
        Load a vector file by rasterizing it and extract metadata.
        
        Args:
            file_path: Path to the vector file
            
        Returns:
            Tuple containing:
                - rasterized image as numpy array (or None if loading fails)
                - dictionary of metadata
        """
        metadata = {'original_format': os.path.splitext(file_path)[1].lower()}
        image = None
        
        try:
            # For SVG files, we can use cairosvg to rasterize
            if file_path.lower().endswith('.svg'):
                try:
                    import cairosvg
                    import io
                    from PIL import Image
                    
                    # Rasterize SVG to PNG in memory
                    png_data = cairosvg.svg2png(url=file_path, output_width=1024, output_height=1024)
                    
                    # Convert PNG data to numpy array
                    pil_img = Image.open(io.BytesIO(png_data))
                    image = np.array(pil_img)
                    
                    metadata['width'] = pil_img.width
                    metadata['height'] = pil_img.height
                    
                except ImportError:
                    logging.warning("cairosvg not installed. Cannot rasterize SVG files.")
                    return None, {'error': 'cairosvg not installed'}
            
            # For EPS and AI files, we might need external tools like Inkscape
            elif file_path.lower().endswith(('.eps', '.ai')):
                logging.warning(f"Rasterization of {os.path.splitext(file_path)[1]} files not implemented yet")
                return None, {'error': 'Rasterization not implemented for this format'}
            
        except Exception as e:
            logging.error(f"Error loading vector file {file_path}: {e}")
            return None, {'error': str(e)}
        
        return image, metadata
    
    def load_media(self, file_path: str) -> Tuple[Any, Dict[str, Any], str]:
        """
        Load a media file and return its content and metadata.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            Tuple containing:
                - media content (image array, video frames, etc.)
                - dictionary of metadata
                - media type string ('image', 'video', 'vector', 'unknown')
        """
        media_type = self.get_media_type(file_path)
        
        if media_type == "image":
            content, metadata = self.load_image(file_path)
        elif media_type == "video":
            content, metadata = self.load_video(file_path)
        elif media_type == "vector":
            content, metadata = self.load_vector(file_path)
        else:
            logging.warning(f"Unsupported media type for file: {file_path}")
            return None, {'error': 'Unsupported media type'}, 'unknown'
        
        # Add file path and type to metadata
        metadata['file_path'] = file_path
        metadata['file_name'] = os.path.basename(file_path)
        metadata['media_type'] = media_type
        
        return content, metadata, media_type
