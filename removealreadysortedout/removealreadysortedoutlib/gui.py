import logging
import os
import sys
from datetime import datetime

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from removealreadysortedoutlib.constants import (
    DESIGN_FILE_FORMATS,
    RAW_IMAGE_FORMATS,
    STANDARD_IMAGE_FORMATS,
    VIDEO_FORMATS,
)
from removealreadysortedoutlib.raw_converter import cleanup_temp_file, convert_raw_to_preview


class DuplicateResolverWindow(QMainWindow):
    """
    Window for resolving duplicate files with different content.
    """

    def __init__(self, source_path: str, target_path: str):
        super().__init__()
        self.source_path = source_path
        self.target_path = target_path
        self.decision = None

        # Track temporary files for cleanup
        self.temp_files = []

        # Setup UI
        self.setWindowTitle("Resolve Duplicate Files")
        self.setMinimumSize(800, 600)

        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create info panel
        self.info_panel = QFrame()
        self.info_panel.setFrameShape(QFrame.StyledPanel)
        self.info_layout = QVBoxLayout(self.info_panel)

        self.title_label = QLabel("Files with same name but different content")
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.info_layout.addWidget(self.title_label)

        self.source_label = QLabel(f"Source: {source_path}")
        self.source_label.setWordWrap(True)
        self.info_layout.addWidget(self.source_label)

        self.source_info_label = QLabel(f"Size: {os.path.getsize(source_path)} bytes")
        self.info_layout.addWidget(self.source_info_label)

        self.target_label = QLabel(f"Target: {target_path}")
        self.target_label.setWordWrap(True)
        self.info_layout.addWidget(self.target_label)

        self.target_info_label = QLabel(f"Size: {os.path.getsize(target_path)} bytes")
        self.info_layout.addWidget(self.target_info_label)

        self.main_layout.addWidget(self.info_panel)

        # Create file preview area (for images and videos)
        self.preview_frame = QFrame()
        self.preview_frame.setFrameShape(QFrame.StyledPanel)
        self.preview_layout = QHBoxLayout(self.preview_frame)

        # Source preview
        self.source_preview_layout = QVBoxLayout()
        self.source_preview_label = QLabel("Source File:")
        self.source_preview_layout.addWidget(self.source_preview_label)

        # Source image preview
        self.source_image_label = QLabel()
        self.source_image_label.setAlignment(Qt.AlignCenter)
        self.source_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.source_preview_layout.addWidget(self.source_image_label)

        # Source video preview
        self.source_video_widget = QVideoWidget()
        self.source_video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.source_video_widget.hide()
        self.source_preview_layout.addWidget(self.source_video_widget)

        self.source_media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.source_media_player.setVideoOutput(self.source_video_widget)

        # Source video controls
        self.source_video_controls = QWidget()
        self.source_video_controls.hide()
        self.source_video_controls_layout = QHBoxLayout(self.source_video_controls)

        self.source_play_button = QPushButton("Play")
        self.source_play_button.clicked.connect(lambda: self.toggle_play("source"))
        self.source_video_controls_layout.addWidget(self.source_play_button)

        self.source_stop_button = QPushButton("Stop")
        self.source_stop_button.clicked.connect(lambda: self.stop_video("source"))
        self.source_video_controls_layout.addWidget(self.source_stop_button)

        self.source_rewind_button = QPushButton("<<")
        self.source_rewind_button.clicked.connect(lambda: self.seek_video("source", -5000))
        self.source_video_controls_layout.addWidget(self.source_rewind_button)

        self.source_forward_button = QPushButton(">>")
        self.source_forward_button.clicked.connect(lambda: self.seek_video("source", 5000))
        self.source_video_controls_layout.addWidget(self.source_forward_button)

        self.source_preview_layout.addWidget(self.source_video_controls)

        # Target preview
        self.target_preview_layout = QVBoxLayout()
        self.target_preview_label = QLabel("Target File:")
        self.target_preview_layout.addWidget(self.target_preview_label)

        # Target image preview
        self.target_image_label = QLabel()
        self.target_image_label.setAlignment(Qt.AlignCenter)
        self.target_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.target_preview_layout.addWidget(self.target_image_label)

        # Target video preview
        self.target_video_widget = QVideoWidget()
        self.target_video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.target_video_widget.hide()
        self.target_preview_layout.addWidget(self.target_video_widget)

        self.target_media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.target_media_player.setVideoOutput(self.target_video_widget)

        # Target video controls
        self.target_video_controls = QWidget()
        self.target_video_controls.hide()
        self.target_video_controls_layout = QHBoxLayout(self.target_video_controls)

        self.target_play_button = QPushButton("Play")
        self.target_play_button.clicked.connect(lambda: self.toggle_play("target"))
        self.target_video_controls_layout.addWidget(self.target_play_button)

        self.target_stop_button = QPushButton("Stop")
        self.target_stop_button.clicked.connect(lambda: self.stop_video("target"))
        self.target_video_controls_layout.addWidget(self.target_stop_button)

        self.target_rewind_button = QPushButton("<<")
        self.target_rewind_button.clicked.connect(lambda: self.seek_video("target", -5000))
        self.target_video_controls_layout.addWidget(self.target_rewind_button)

        self.target_forward_button = QPushButton(">>")
        self.target_forward_button.clicked.connect(lambda: self.seek_video("target", 5000))
        self.target_video_controls_layout.addWidget(self.target_forward_button)

        self.target_preview_layout.addWidget(self.target_video_controls)

        self.preview_layout.addLayout(self.source_preview_layout)
        self.preview_layout.addLayout(self.target_preview_layout)

        self.main_layout.addWidget(self.preview_frame)

        # Try to load image previews
        self.load_previews()

        # Create decision radio buttons
        self.decision_widget = QWidget()
        self.decision_layout = QVBoxLayout(self.decision_widget)

        # Radio buttons for decision
        self.decision_group = QButtonGroup(self)

        self.decision_label = QLabel("Select decision:")
        self.decision_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.decision_layout.addWidget(self.decision_label)

        self.radio_layout = QHBoxLayout()

        self.source_radio = QRadioButton("Keep Source (replace target)")
        self.source_radio.setShortcut("S")
        self.decision_group.addButton(self.source_radio)
        self.radio_layout.addWidget(self.source_radio)

        self.target_radio = QRadioButton("Keep Target (remove source)")
        self.target_radio.setShortcut("T")
        self.decision_group.addButton(self.target_radio)
        self.radio_layout.addWidget(self.target_radio)

        self.both_radio = QRadioButton("Keep Both")
        self.both_radio.setShortcut("B")
        self.decision_group.addButton(self.both_radio)
        self.radio_layout.addWidget(self.both_radio)

        self.skip_radio = QRadioButton("Skip")
        self.skip_radio.setShortcut("K")
        self.decision_group.addButton(self.skip_radio)
        self.radio_layout.addWidget(self.skip_radio)

        self.decision_layout.addLayout(self.radio_layout)

        # Save button
        self.save_button = QPushButton("Apply Decision")
        self.save_button.setMinimumHeight(50)
        self.save_button.clicked.connect(self.save_decision)
        self.decision_layout.addWidget(self.save_button)

        self.main_layout.addWidget(self.decision_widget)

    def load_previews(self):
        """Load previews for both source and target files."""
        # Get file extensions
        source_ext = os.path.splitext(self.source_path)[1].lower()
        target_ext = os.path.splitext(self.target_path)[1].lower()

        # Combine all image formats
        image_formats = STANDARD_IMAGE_FORMATS + RAW_IMAGE_FORMATS + DESIGN_FILE_FORMATS

        # Load source preview
        if source_ext in image_formats:
            self.load_image(self.source_path, "source")
        elif source_ext in VIDEO_FORMATS:
            self.load_video(self.source_path, "source")
        else:
            self.source_image_label.setText(f"Unsupported file format: {source_ext}")

        # Load target preview
        if target_ext in image_formats:
            self.load_image(self.target_path, "target")
        elif target_ext in VIDEO_FORMATS:
            self.load_video(self.target_path, "target")
        else:
            self.target_image_label.setText(f"Unsupported file format: {target_ext}")

    def load_image(self, image_path: str, target: str):
        """Load and display an image file."""
        try:
            # Get basic file info for all formats
            file_size = os.path.getsize(image_path) // 1024
            file_date = datetime.fromtimestamp(os.path.getmtime(image_path)).strftime("%Y-%m-%d %H:%M:%S")
            file_name = os.path.basename(image_path)
            info_text = f"File: {file_name}\nSize: {file_size} KB\nDate: {file_date}"

            # Check if it's a RAW format
            ext = os.path.splitext(image_path)[1].lower()

            if ext in RAW_IMAGE_FORMATS:
                raw_info = f"RAW image: {file_name}\nSize: {file_size} KB\nDate: {file_date}"

                # Log that we're processing a RAW file
                logging.info(f"Processing RAW file ({target}): {image_path}")

                # Use the RAW converter to get a preview
                result = convert_raw_to_preview(image_path)
                if result:
                    pixmap, temp_file = result

                    # If we got a temporary file, add it to the list for cleanup
                    if temp_file:
                        self.temp_files.append(temp_file)

                    # Display the converted image
                    if target == "source":
                        self.source_image_label.setPixmap(
                            pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        )
                        self.source_image_label.show()
                        self.source_video_widget.hide()
                        self.source_video_controls.hide()
                    else:
                        self.target_image_label.setPixmap(
                            pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        )
                        self.target_image_label.show()
                        self.target_video_widget.hide()
                        self.target_video_controls.hide()
                    return

                # If RAW converter failed, try to extract basic metadata from the RAW file
                try:
                    # Read first few KB of the file to look for metadata
                    with open(image_path, "rb") as f:
                        header = f.read(8192)  # Read first 8KB

                    # Look for camera model info in the header
                    camera_model = None
                    for model_marker in [
                        b"Canon",
                        b"NIKON",
                        b"SONY",
                        b"OLYMPUS",
                        b"PENTAX",
                        b"FUJI",
                        b"LEICA",
                        b"Realme",
                    ]:
                        if model_marker in header:
                            camera_model = model_marker.decode("utf-8", errors="ignore")
                            break

                    # Try to extract dimensions if possible
                    dimensions = None
                    # Common dimension markers in RAW files
                    dimension_markers = [b"ImageWidth=", b"ImageLength=", b"Width=", b"Height="]
                    for marker in dimension_markers:
                        if marker in header:
                            pos = header.find(marker) + len(marker)
                            # Try to read a number after the marker
                            num_str = b""
                            while pos < len(header) and header[pos : pos + 1].isdigit():
                                num_str += header[pos : pos + 1]
                                pos += 1
                            if num_str:
                                try:
                                    dimension = int(num_str)
                                    if dimensions is None:
                                        dimensions = [dimension]
                                    else:
                                        dimensions.append(dimension)
                                        break  # We have width and height
                                except:
                                    pass

                    # Add metadata to the info if found
                    if camera_model:
                        raw_info += f"\nCamera: {camera_model}"
                    if dimensions and len(dimensions) >= 2:
                        raw_info += f"\nDimensions: {dimensions[0]}x{dimensions[1]}"
                except Exception as meta_e:
                    logging.debug(f"Could not extract metadata from RAW file: {meta_e}")

                # If we couldn't load a preview, just show the enhanced info
                if target == "source":
                    self.source_image_label.setText(raw_info)
                    self.source_image_label.show()
                    self.source_video_widget.hide()
                    self.source_video_controls.hide()
                else:
                    self.target_image_label.setText(raw_info)
                    self.target_image_label.show()
                    self.target_video_widget.hide()
                    self.target_video_controls.hide()
                return

            # For standard image formats, try to load with QImage first (more robust)
            # Redirect stderr to suppress warnings about corrupt JPEG data
            original_stderr = sys.stderr
            try:
                # Temporarily redirect stderr
                with open(os.devnull, "w") as devnull:
                    sys.stderr = devnull

                    # Try to load the image
                    image = QImage(image_path)

                    # Restore stderr
                    sys.stderr = original_stderr

                    if not image.isNull() and image.width() > 0 and image.height() > 0:
                        pixmap = QPixmap.fromImage(image)
                        if target == "source":
                            self.source_image_label.setPixmap(
                                pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            )
                            self.source_image_label.show()
                            self.source_video_widget.hide()
                            self.source_video_controls.hide()
                        else:
                            self.target_image_label.setPixmap(
                                pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            )
                            self.target_image_label.show()
                            self.target_video_widget.hide()
                            self.target_video_controls.hide()
                        return
            except Exception as qimage_e:
                logging.debug(f"QImage failed to load {image_path}: {qimage_e}, trying QPixmap")
            finally:
                # Make sure stderr is restored
                sys.stderr = original_stderr

            # If QImage fails, try QPixmap as fallback
            # Redirect stderr again for QPixmap
            original_stderr = sys.stderr
            try:
                # Temporarily redirect stderr
                with open(os.devnull, "w") as devnull:
                    sys.stderr = devnull

                    # Try to load with QPixmap
                    pixmap = QPixmap(image_path)

                    # Restore stderr
                    sys.stderr = original_stderr

                    if not pixmap.isNull() and pixmap.width() > 0 and pixmap.height() > 0:
                        if target == "source":
                            self.source_image_label.setPixmap(
                                pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            )
                            self.source_image_label.show()
                            self.source_video_widget.hide()
                            self.source_video_controls.hide()
                        else:
                            self.target_image_label.setPixmap(
                                pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            )
                            self.target_image_label.show()
                            self.target_video_widget.hide()
                            self.target_video_controls.hide()
                        return
            except Exception as pixmap_e:
                logging.debug(f"QPixmap failed to load {image_path}: {pixmap_e}")
            finally:
                # Make sure stderr is restored
                sys.stderr = original_stderr

            # If all image loading methods fail, show file info
            if target == "source":
                self.source_image_label.setText(f"{info_text}\n\nPreview not available")
                self.source_image_label.show()
                self.source_video_widget.hide()
                self.source_video_controls.hide()
            else:
                self.target_image_label.setText(f"{info_text}\n\nPreview not available")
                self.target_image_label.show()
                self.target_video_widget.hide()
                self.target_video_controls.hide()

        except Exception as e:
            logging.error(f"Failed to load image {image_path}: {e}")
            # Show basic file info even if loading fails
            try:
                file_size = os.path.getsize(image_path) // 1024
                file_date = datetime.fromtimestamp(os.path.getmtime(image_path)).strftime("%Y-%m-%d %H:%M:%S")
                file_name = os.path.basename(image_path)
                error_text = f"File: {file_name}\nSize: {file_size} KB\nDate: {file_date}\n\nError: {str(e)}"
            except:
                error_text = f"Error loading file: {os.path.basename(image_path)}\n{str(e)}"

            if target == "source":
                self.source_image_label.setText(error_text)
                self.source_image_label.show()
                self.source_video_widget.hide()
                self.source_video_controls.hide()
            else:
                self.target_image_label.setText(error_text)
                self.target_image_label.show()
                self.target_video_widget.hide()
                self.target_video_controls.hide()

    def load_video(self, video_path: str, target: str):
        """Load and prepare a video file for playback."""
        try:
            # Get video file info
            file_size = os.path.getsize(video_path) // 1024
            file_date = datetime.fromtimestamp(os.path.getmtime(video_path)).strftime("%Y-%m-%d %H:%M:%S")
            file_name = os.path.basename(video_path)
            video_info = f"Video: {file_name}\nSize: {file_size} KB\nDate: {file_date}"

            # Check if file exists and is accessible
            if not os.path.exists(video_path) or not os.access(video_path, os.R_OK):
                error_text = f"Video file not accessible: {file_name}"
                if target == "source":
                    self.source_image_label.setText(error_text)
                    self.source_image_label.show()
                    self.source_video_widget.hide()
                    self.source_video_controls.hide()
                else:
                    self.target_image_label.setText(error_text)
                    self.target_image_label.show()
                    self.target_video_widget.hide()
                    self.target_video_controls.hide()
                return

            # Set up media player
            if target == "source":
                # Show video info in the image label
                self.source_image_label.setText(video_info)
                self.source_image_label.show()

                # Set up video player
                try:
                    self.source_media_player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
                    self.source_video_widget.show()
                    self.source_video_controls.show()

                    # Connect media player status signals if not already connected
                    if not hasattr(self, "source_media_connected"):
                        self.source_media_player.mediaStatusChanged.connect(
                            lambda status: self.handle_media_status(status, "source")
                        )
                        self.source_media_player.error.connect(lambda error: self.handle_media_error(error, "source"))
                        self.source_media_connected = True
                except Exception as media_e:
                    logging.error(f"Failed to set up media player for {video_path}: {media_e}")
                    self.source_image_label.setText(f"{video_info}\n\nCould not initialize video player")
                    self.source_video_widget.hide()
                    self.source_video_controls.hide()
            else:
                # Show video info in the image label
                self.target_image_label.setText(video_info)
                self.target_image_label.show()

                # Set up video player
                try:
                    self.target_media_player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
                    self.target_video_widget.show()
                    self.target_video_controls.show()

                    # Connect media player status signals if not already connected
                    if not hasattr(self, "target_media_connected"):
                        self.target_media_player.mediaStatusChanged.connect(
                            lambda status: self.handle_media_status(status, "target")
                        )
                        self.target_media_player.error.connect(lambda error: self.handle_media_error(error, "target"))
                        self.target_media_connected = True
                except Exception as media_e:
                    logging.error(f"Failed to set up media player for {video_path}: {media_e}")
                    self.target_image_label.setText(f"{video_info}\n\nCould not initialize video player")
                    self.target_video_widget.hide()
                    self.target_video_controls.hide()
        except Exception as e:
            logging.error(f"Failed to load video {video_path}: {e}")
            # Show basic file info even if loading fails
            try:
                file_size = os.path.getsize(video_path) // 1024
                file_date = datetime.fromtimestamp(os.path.getmtime(video_path)).strftime("%Y-%m-%d %H:%M:%S")
                file_name = os.path.basename(video_path)
                error_text = f"Video: {file_name}\nSize: {file_size} KB\nDate: {file_date}\n\nError: {str(e)}"
            except:
                error_text = f"Error loading video: {os.path.basename(video_path)}\n{str(e)}"

            if target == "source":
                self.source_image_label.setText(error_text)
                self.source_image_label.show()
                self.source_video_widget.hide()
                self.source_video_controls.hide()
            else:
                self.target_image_label.setText(error_text)
                self.target_image_label.show()
                self.target_video_widget.hide()
                self.target_video_controls.hide()

    def handle_media_status(self, status, target: str):
        """Handle media player status changes."""
        if status == QMediaPlayer.LoadedMedia:
            # Media is loaded and ready to play
            if target == "source":
                logging.debug(f"Source video loaded: {self.source_path}")
            else:
                logging.debug(f"Target video loaded: {self.target_path}")
        elif status == QMediaPlayer.InvalidMedia:
            # Media could not be loaded
            if target == "source":
                logging.error(f"Invalid media: {self.source_path}")
                self.source_image_label.setText(f"Invalid video format: {os.path.basename(self.source_path)}")
                self.source_video_widget.hide()
                self.source_video_controls.hide()
            else:
                logging.error(f"Invalid media: {self.target_path}")
                self.target_image_label.setText(f"Invalid video format: {os.path.basename(self.target_path)}")
                self.target_video_widget.hide()
                self.target_video_controls.hide()

    def handle_media_error(self, error, target: str):
        """Handle media player errors."""
        error_messages = {
            QMediaPlayer.NoError: "No error",
            QMediaPlayer.ResourceError: "Resource error",
            QMediaPlayer.FormatError: "Format error",
            QMediaPlayer.NetworkError: "Network error",
            QMediaPlayer.AccessDeniedError: "Access denied",
            QMediaPlayer.ServiceMissingError: "Service missing",
        }

        error_text = error_messages.get(error, f"Unknown error: {error}")
        logging.error(f"Media player error for {target}: {error_text}")

        if target == "source":
            file_name = os.path.basename(self.source_path)
            self.source_image_label.setText(f"Video: {file_name}\n\nError: {error_text}")
            self.source_video_widget.hide()
            self.source_video_controls.hide()
        else:
            file_name = os.path.basename(self.target_path)
            self.target_image_label.setText(f"Video: {file_name}\n\nError: {error_text}")
            self.target_video_widget.hide()
            self.target_video_controls.hide()

    def toggle_play(self, target: str):
        """Toggle video playback between play and pause."""
        if target == "source":
            if self.source_media_player.state() == QMediaPlayer.PlayingState:
                self.source_media_player.pause()
                self.source_play_button.setText("Play")
            else:
                self.source_media_player.play()
                self.source_play_button.setText("Pause")
        else:
            if self.target_media_player.state() == QMediaPlayer.PlayingState:
                self.target_media_player.pause()
                self.target_play_button.setText("Play")
            else:
                self.target_media_player.play()
                self.target_play_button.setText("Pause")

    def stop_video(self, target: str):
        """Stop video playback and reset to beginning."""
        if target == "source":
            self.source_media_player.stop()
            self.source_play_button.setText("Play")
        else:
            self.target_media_player.stop()
            self.target_play_button.setText("Play")

    def seek_video(self, target: str, ms: int):
        """Seek forward or backward in the video."""
        if target == "source":
            current_position = self.source_media_player.position()
            self.source_media_player.setPosition(max(0, current_position + ms))
        else:
            current_position = self.target_media_player.position()
            self.target_media_player.setPosition(max(0, current_position + ms))

    def save_decision(self):
        """Save the user's decision and close the window."""
        # Stop any playing videos
        self.source_media_player.stop()
        self.target_media_player.stop()

        if self.source_radio.isChecked():
            self.decision = "source"
        elif self.target_radio.isChecked():
            self.decision = "target"
        elif self.both_radio.isChecked():
            self.decision = "both"
        elif self.skip_radio.isChecked():
            self.decision = "skip"
        else:
            # If no decision is made, default to skip
            self.decision = "skip"

        self.close()

    def closeEvent(self, event):
        """Handle window close event to ensure media players are stopped and temp files are cleaned up."""
        # Stop any playing videos
        self.source_media_player.stop()
        self.target_media_player.stop()

        # Clean up any temporary files
        for temp_file in self.temp_files:
            cleanup_temp_file(temp_file)

        event.accept()


def resolve_duplicate_gui(source_path: str, target_path: str) -> str:
    """
    Show a GUI to resolve duplicate files with different content.

    Args:
        source_path: Path to the source file
        target_path: Path to the target file

    Returns:
        String indicating the decision:
        - "source": Keep source file (replace target)
        - "target": Keep target file (remove source)
        - "both": Keep both files
        - "skip": Skip this comparison
    """
    try:
        # Check if files exist
        if not os.path.exists(source_path):
            logging.error(f"Source file does not exist: {source_path}")
            return "skip"
        if not os.path.exists(target_path):
            logging.error(f"Target file does not exist: {target_path}")
            return "skip"

        # Check if either file is a RAW format
        source_ext = os.path.splitext(source_path)[1].lower()
        target_ext = os.path.splitext(target_path)[1].lower()
        raw_formats = [
            ".dng",
            ".nef",
            ".raw",
            ".cr2",
            ".arw",
            ".orf",
            ".rw2",
            ".srw",
            ".pef",
            ".raf",
            ".x3f",
            ".crw",
            ".erf",
            ".sr2",
            ".kdc",
            ".dcr",
            ".mrw",
            ".3fr",
            ".mef",
            ".mos",
            ".nrw",
            ".rwl",
            ".iiq",
        ]

        is_raw = source_ext in raw_formats or target_ext in raw_formats
        if is_raw:
            logging.info(f"RAW file detected: {source_path if source_ext in raw_formats else target_path}")

        # Suppress TIFF warnings that might appear when loading RAW files
        # This is done by redirecting stderr temporarily
        original_stderr = sys.stderr
        try:
            # Create a temporary file to capture stderr
            with open(os.devnull, "w") as devnull:
                sys.stderr = devnull

                # Create and show the GUI
                app = QApplication.instance() or QApplication(sys.argv)
                window = DuplicateResolverWindow(source_path, target_path)
                window.show()

                # Restore stderr before entering the event loop
                sys.stderr = original_stderr

                app.exec_()

                # Return the user's decision
                return window.decision or "skip"
        finally:
            # Make sure stderr is restored even if an exception occurs
            sys.stderr = original_stderr
    except Exception as e:
        logging.error(f"Error in GUI: {e}")
        return "skip"
