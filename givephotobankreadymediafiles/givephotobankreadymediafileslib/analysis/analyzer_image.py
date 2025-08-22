"""
Image analyzer module for extracting features and detecting objects in images.
"""

import logging
from typing import Any

import numpy as np

from givephotobankreadymediafileslib.analysis.coco_utils import download_coco_categories, get_coco_categories

# Try to import optional dependencies
try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV not available. Some image analysis features will be limited.")

try:
    import torch
    import torchvision

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available. Neural network-based analysis will be disabled.")


def load_coco_categories():
    """
    Load COCO categories using the coco_utils module.
    Returns a list of category names.
    """
    return get_coco_categories()


class ImageAnalyzer:
    """Class for analyzing images and extracting features."""

    def __init__(self, models_dir: str | None = None):
        """
        Initialize the image analyzer.

        Args:
            models_dir: Directory containing pre-trained models
        """
        self.models_dir = models_dir
        self.models = {}
        self.device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"

        # Try to download the latest COCO categories at startup
        try:
            download_coco_categories()
        except Exception as e:
            logging.warning(f"Failed to download COCO categories at startup: {e}")

        # Initialize models if dependencies are available
        if TORCH_AVAILABLE:
            self._init_models()

        logging.debug(f"ImageAnalyzer initialized (device: {self.device})")

    def _init_models(self):
        """Initialize pre-trained models for image analysis."""
        try:
            # Load ResNet feature extractor
            self.models["feature_extractor"] = torchvision.models.resnet50(pretrained=True)
            self.models["feature_extractor"].eval()
            self.models["feature_extractor"] = self.models["feature_extractor"].to(self.device)

            # Load object detection model (COCO)
            self.models["object_detector"] = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
            self.models["object_detector"].eval()
            self.models["object_detector"] = self.models["object_detector"].to(self.device)

            # Load COCO class names from file or download them
            self.coco_classes = load_coco_categories()

            # Preprocessing transforms
            self.preprocess = torchvision.transforms.Compose(
                [
                    torchvision.transforms.ToPILImage(),
                    torchvision.transforms.Resize(256),
                    torchvision.transforms.CenterCrop(224),
                    torchvision.transforms.ToTensor(),
                    torchvision.transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ]
            )

            logging.info("Successfully loaded pre-trained models for image analysis")

        except Exception as e:
            logging.error(f"Error initializing models: {e}")
            self.models = {}

    def extract_features(self, image: np.ndarray) -> np.ndarray | None:
        """
        Extract feature vector from an image using a pre-trained CNN.

        Args:
            image: Input image as numpy array (RGB)

        Returns:
            Feature vector as numpy array or None if extraction fails
        """
        if not TORCH_AVAILABLE or "feature_extractor" not in self.models:
            logging.warning("Feature extraction unavailable: PyTorch or model not loaded")
            return None

        try:
            # Preprocess the image
            img_tensor = self.preprocess(image)
            img_tensor = img_tensor.unsqueeze(0).to(self.device)

            # Extract features (before the final FC layer)
            with torch.no_grad():
                # Remove the final FC layer to get features
                features = torch.nn.Sequential(*list(self.models["feature_extractor"].children())[:-1])(img_tensor)
                features = features.squeeze().cpu().numpy()

            return features

        except Exception as e:
            logging.error(f"Error extracting features: {e}")
            return None

    def detect_objects(self, image: np.ndarray, confidence_threshold: float = 0.5) -> list[dict[str, Any]]:
        """
        Detect objects in an image using a pre-trained object detection model.

        Args:
            image: Input image as numpy array (RGB)
            confidence_threshold: Minimum confidence score for detections

        Returns:
            List of detected objects with class, confidence, and bounding box
        """
        if not TORCH_AVAILABLE or "object_detector" not in self.models:
            logging.warning("Object detection unavailable: PyTorch or model not loaded")
            return []

        try:
            # Convert numpy array to tensor
            img_tensor = torch.from_numpy(image.transpose((2, 0, 1))).float().div(255.0)
            img_tensor = img_tensor.unsqueeze(0).to(self.device)

            # Run object detection
            with torch.no_grad():
                detections = self.models["object_detector"](img_tensor)[0]

            # Process detections
            objects = []
            for i in range(len(detections["boxes"])):
                confidence = detections["scores"][i].item()
                if confidence >= confidence_threshold:
                    box = detections["boxes"][i].cpu().numpy().astype(int)
                    class_idx = detections["labels"][i].item()
                    class_name = self.coco_classes[class_idx - 1]  # COCO classes are 1-indexed

                    objects.append(
                        {"class": class_name, "confidence": confidence, "box": box.tolist()}  # [x1, y1, x2, y2]
                    )

            return objects

        except Exception as e:
            logging.error(f"Error detecting objects: {e}")
            return []

    def analyze_colors(self, image: np.ndarray, num_colors: int = 5) -> list[dict[str, Any]]:
        """
        Analyze the dominant colors in an image.

        Args:
            image: Input image as numpy array (RGB)
            num_colors: Number of dominant colors to extract

        Returns:
            List of dominant colors with RGB values and percentage
        """
        if not CV2_AVAILABLE:
            logging.warning("Color analysis unavailable: OpenCV not loaded")
            return []

        try:
            # Reshape the image to be a list of pixels
            pixels = image.reshape(-1, 3).astype(np.float32)

            # Define criteria and apply kmeans
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
            _, labels, centers = cv2.kmeans(pixels, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

            # Count labels to find percentages
            counts = np.bincount(labels.flatten())
            percentages = counts / len(labels) * 100

            # Sort colors by percentage
            colors = []
            for i in range(num_colors):
                colors.append({"rgb": centers[i].astype(int).tolist(), "percentage": float(percentages[i])})

            # Sort by percentage (descending)
            colors.sort(key=lambda x: x["percentage"], reverse=True)

            return colors

        except Exception as e:
            logging.error(f"Error analyzing colors: {e}")
            return []

    def analyze_composition(self, image: np.ndarray) -> dict[str, Any]:
        """
        Analyze the composition of an image (brightness, contrast, etc.).

        Args:
            image: Input image as numpy array (RGB)

        Returns:
            Dictionary with composition metrics
        """
        if not CV2_AVAILABLE:
            logging.warning("Composition analysis unavailable: OpenCV not loaded")
            return {}

        try:
            # Convert to grayscale for some analyses
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

            # Calculate brightness (mean pixel value)
            brightness = np.mean(gray)

            # Calculate contrast (standard deviation of pixel values)
            contrast = np.std(gray)

            # Calculate sharpness (variance of Laplacian)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = np.var(laplacian)

            # Calculate color diversity (standard deviation across channels)
            color_diversity = np.mean([np.std(image[:, :, i]) for i in range(3)])

            return {
                "brightness": float(brightness),
                "contrast": float(contrast),
                "sharpness": float(sharpness),
                "color_diversity": float(color_diversity),
            }

        except Exception as e:
            logging.error(f"Error analyzing composition: {e}")
            return {}

    def analyze_image(self, image: np.ndarray) -> dict[str, Any]:
        """
        Perform comprehensive analysis of an image.

        Args:
            image: Input image as numpy array (RGB)

        Returns:
            Dictionary with analysis results
        """
        results = {}

        # Extract features
        features = self.extract_features(image)
        if features is not None:
            results["features"] = features

        # Detect objects
        objects = self.detect_objects(image)
        if objects:
            results["objects"] = objects

            # Extract object classes for easier access
            results["object_classes"] = [obj["class"] for obj in objects]

            # Count objects by class
            class_counts = {}
            for obj in objects:
                class_name = obj["class"]
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
            results["object_counts"] = class_counts

        # Analyze colors
        colors = self.analyze_colors(image)
        if colors:
            results["colors"] = colors

        # Analyze composition
        composition = self.analyze_composition(image)
        if composition:
            results["composition"] = composition

        return results
