"""
Video analyzer module for extracting features and analyzing video content.
"""

import logging
from typing import Any

import numpy as np

from givephotobankreadymediafileslib.analysis.analyzer_image import ImageAnalyzer

# Try to import optional dependencies
try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV not available. Video analysis features will be limited.")

try:
    import torch
    import torchvision

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available. Neural network-based video analysis will be disabled.")


class VideoAnalyzer:
    """Class for analyzing videos and extracting features."""

    def __init__(self, models_dir: str | None = None):
        """
        Initialize the video analyzer.

        Args:
            models_dir: Directory containing pre-trained models
        """
        self.models_dir = models_dir
        self.models = {}
        self.device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"

        # Initialize image analyzer for frame-level analysis
        self.image_analyzer = ImageAnalyzer(models_dir)

        # Initialize models if dependencies are available
        if TORCH_AVAILABLE:
            self._init_models()

        logging.debug(f"VideoAnalyzer initialized (device: {self.device})")

    def _init_models(self):
        """Initialize pre-trained models for video analysis."""
        try:
            # For now, we'll rely on frame-by-frame analysis using the ImageAnalyzer
            # In a more advanced implementation, we could add video-specific models here
            # such as action recognition models
            pass

        except Exception as e:
            logging.error(f"Error initializing video models: {e}")
            self.models = {}

    def analyze_frames(self, frames: list[np.ndarray], sample_rate: int = 1) -> list[dict[str, Any]]:
        """
        Analyze individual frames from a video.

        Args:
            frames: List of video frames as numpy arrays
            sample_rate: Rate at which to sample frames for analysis

        Returns:
            List of analysis results for each sampled frame
        """
        frame_results = []

        # Sample frames at the specified rate
        sampled_frames = frames[:: max(1, len(frames) // (sample_rate * 10))]

        # Limit to a reasonable number of frames to analyze
        max_frames = min(10, len(sampled_frames))
        sampled_frames = sampled_frames[:max_frames]

        logging.info(f"Analyzing {len(sampled_frames)} frames from video")

        # Analyze each sampled frame
        for i, frame in enumerate(sampled_frames):
            logging.debug(f"Analyzing frame {i+1}/{len(sampled_frames)}")
            frame_analysis = self.image_analyzer.analyze_image(frame)
            frame_results.append({"frame_index": i, "analysis": frame_analysis})

        return frame_results

    def analyze_motion(self, frames: list[np.ndarray]) -> dict[str, Any]:
        """
        Analyze motion patterns in a video.

        Args:
            frames: List of video frames as numpy arrays

        Returns:
            Dictionary with motion analysis results
        """
        if not CV2_AVAILABLE or len(frames) < 2:
            logging.warning("Motion analysis unavailable: OpenCV not loaded or insufficient frames")
            return {}

        try:
            # Convert frames to grayscale
            gray_frames = [cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) for frame in frames]

            # Calculate optical flow between consecutive frames
            flow_magnitudes = []
            for i in range(len(gray_frames) - 1):
                flow = cv2.calcOpticalFlowFarneback(
                    gray_frames[i],
                    gray_frames[i + 1],
                    None,
                    pyr_scale=0.5,
                    levels=3,
                    winsize=15,
                    iterations=3,
                    poly_n=5,
                    poly_sigma=1.2,
                    flags=0,
                )

                # Calculate magnitude of flow vectors
                magnitude = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
                flow_magnitudes.append(np.mean(magnitude))

            # Calculate motion metrics
            avg_motion = np.mean(flow_magnitudes) if flow_magnitudes else 0
            max_motion = np.max(flow_magnitudes) if flow_magnitudes else 0
            motion_variance = np.var(flow_magnitudes) if flow_magnitudes else 0

            return {
                "average_motion": float(avg_motion),
                "max_motion": float(max_motion),
                "motion_variance": float(motion_variance),
                "is_static": avg_motion < 1.0,  # Threshold for static vs. dynamic content
            }

        except Exception as e:
            logging.error(f"Error analyzing motion: {e}")
            return {}

    def detect_scene_changes(self, frames: list[np.ndarray], threshold: float = 30.0) -> list[int]:
        """
        Detect scene changes in a video.

        Args:
            frames: List of video frames as numpy arrays
            threshold: Threshold for scene change detection

        Returns:
            List of frame indices where scene changes occur
        """
        if not CV2_AVAILABLE or len(frames) < 2:
            logging.warning("Scene change detection unavailable: OpenCV not loaded or insufficient frames")
            return []

        try:
            # Convert frames to grayscale
            gray_frames = [cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) for frame in frames]

            # Calculate frame differences
            diffs = []
            for i in range(len(gray_frames) - 1):
                diff = cv2.absdiff(gray_frames[i], gray_frames[i + 1])
                diffs.append(np.mean(diff))

            # Detect scene changes based on threshold
            scene_changes = [i + 1 for i, diff in enumerate(diffs) if diff > threshold]

            return scene_changes

        except Exception as e:
            logging.error(f"Error detecting scene changes: {e}")
            return []

    def aggregate_frame_analyses(self, frame_results: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Aggregate analysis results from multiple frames.

        Args:
            frame_results: List of frame analysis results

        Returns:
            Dictionary with aggregated analysis results
        """
        if not frame_results:
            return {}

        # Collect all detected objects across frames
        all_objects = []
        for result in frame_results:
            if "analysis" in result and "objects" in result["analysis"]:
                all_objects.extend(result["analysis"]["objects"])

        # Count object occurrences
        object_counts = {}
        for obj in all_objects:
            class_name = obj["class"]
            object_counts[class_name] = object_counts.get(class_name, 0) + 1

        # Sort by frequency
        sorted_objects = sorted(object_counts.items(), key=lambda x: x[1], reverse=True)

        # Aggregate composition metrics
        composition_metrics = {}
        for metric in ["brightness", "contrast", "sharpness", "color_diversity"]:
            values = [
                result["analysis"]["composition"][metric]
                for result in frame_results
                if "analysis" in result
                and "composition" in result["analysis"]
                and metric in result["analysis"]["composition"]
            ]
            if values:
                composition_metrics[f"avg_{metric}"] = float(np.mean(values))
                composition_metrics[f"std_{metric}"] = float(np.std(values))

        return {
            "object_frequencies": dict(sorted_objects),
            "top_objects": [obj[0] for obj in sorted_objects[:5]] if sorted_objects else [],
            "composition": composition_metrics,
        }

    def analyze_video(self, frames: list[np.ndarray]) -> dict[str, Any]:
        """
        Perform comprehensive analysis of a video.

        Args:
            frames: List of video frames as numpy arrays

        Returns:
            Dictionary with analysis results
        """
        results = {}

        # Analyze individual frames
        frame_results = self.analyze_frames(frames)
        results["frame_analyses"] = frame_results

        # Analyze motion
        motion_analysis = self.analyze_motion(frames)
        if motion_analysis:
            results["motion"] = motion_analysis

        # Detect scene changes
        scene_changes = self.detect_scene_changes(frames)
        if scene_changes:
            results["scene_changes"] = scene_changes
            results["scene_count"] = len(scene_changes) + 1

        # Aggregate frame analyses
        aggregated = self.aggregate_frame_analyses(frame_results)
        if aggregated:
            results["aggregated"] = aggregated

        return results
