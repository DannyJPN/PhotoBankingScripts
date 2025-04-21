"""
Editor dialog for editing metadata of a single media file.
"""
import os
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QComboBox, QPushButton, QGroupBox, QScrollArea,
    QWidget, QSplitter, QListWidget, QListWidgetItem, QMessageBox,
    QCheckBox, QProgressBar, QFileDialog, QGridLayout
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon

from core.media_loader import MediaLoader
from core.analyzer_image import ImageAnalyzer
from core.analyzer_video import VideoAnalyzer
from core.metadata_generator import MetadataGenerator
from core.llm_client import LLMClientFactory
from core.orchestrator import Orchestrator


class MediaPreviewWidget(QWidget):
    """Widget for displaying a preview of the media file."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        """Initialize the UI."""
        self.layout = QVBoxLayout(self)
        
        # Preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        
        # Info label
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        
        self.layout.addWidget(self.preview_label)
        self.layout.addWidget(self.info_label)
    
    def set_image(self, image_path: str):
        """
        Set the image to display.
        
        Args:
            image_path: Path to the image file
        """
        if not os.path.exists(image_path):
            self.preview_label.setText("Image not found")
            return
        
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.preview_label.setText("Failed to load image")
            return
        
        # Scale the pixmap to fit the label while maintaining aspect ratio
        pixmap = pixmap.scaled(
            self.preview_label.width(), 
            self.preview_label.height(),
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        self.preview_label.setPixmap(pixmap)
        
        # Set info text
        file_size = os.path.getsize(image_path) / (1024 * 1024)  # MB
        file_name = os.path.basename(image_path)
        self.info_label.setText(f"{file_name}\n{pixmap.width()}x{pixmap.height()} px\n{file_size:.2f} MB")
    
    def set_video(self, video_path: str):
        """
        Set the video to display (first frame).
        
        Args:
            video_path: Path to the video file
        """
        if not os.path.exists(video_path):
            self.preview_label.setText("Video not found")
            return
        
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.preview_label.setText("Failed to open video")
                return
            
            ret, frame = cap.read()
            if not ret:
                self.preview_label.setText("Failed to read video frame")
                return
            
            # Convert from BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create QImage from numpy array
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            # Create pixmap from QImage
            pixmap = QPixmap.fromImage(q_img)
            
            # Scale the pixmap
            pixmap = pixmap.scaled(
                self.preview_label.width(), 
                self.preview_label.height(),
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self.preview_label.setPixmap(pixmap)
            
            # Set info text
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            file_name = os.path.basename(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            self.info_label.setText(
                f"{file_name}\n"
                f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} px\n"
                f"{fps:.2f} fps, {duration:.2f} sec\n"
                f"{file_size:.2f} MB"
            )
            
            cap.release()
            
        except Exception as e:
            self.preview_label.setText(f"Error: {str(e)}")
    
    def set_media(self, media_path: str):
        """
        Set the media to display.
        
        Args:
            media_path: Path to the media file
        """
        if not os.path.exists(media_path):
            self.preview_label.setText("File not found")
            return
        
        # Determine file type by extension
        ext = os.path.splitext(media_path)[1].lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']:
            self.set_image(media_path)
        elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.mkv']:
            self.set_video(media_path)
        else:
            self.preview_label.setText(f"Unsupported file type: {ext}")


class KeywordsWidget(QWidget):
    """Widget for editing keywords."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        """Initialize the UI."""
        self.layout = QVBoxLayout(self)
        
        # Keywords list
        self.keywords_list = QListWidget()
        self.keywords_list.setSelectionMode(QListWidget.ExtendedSelection)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self.add_keyword)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_keywords)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_keywords)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.clear_btn)
        
        # Add keyword input
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("Enter new keyword")
        self.keyword_input.returnPressed.connect(self.add_keyword)
        
        self.layout.addWidget(QLabel("Keywords:"))
        self.layout.addWidget(self.keywords_list)
        self.layout.addWidget(self.keyword_input)
        self.layout.addLayout(btn_layout)
    
    def add_keyword(self):
        """Add a new keyword to the list."""
        keyword = self.keyword_input.text().strip()
        if keyword:
            # Check if keyword already exists
            items = [self.keywords_list.item(i).text() for i in range(self.keywords_list.count())]
            if keyword not in items:
                self.keywords_list.addItem(keyword)
                self.keyword_input.clear()
    
    def remove_keywords(self):
        """Remove selected keywords from the list."""
        selected_items = self.keywords_list.selectedItems()
        for item in selected_items:
            self.keywords_list.takeItem(self.keywords_list.row(item))
    
    def clear_keywords(self):
        """Clear all keywords from the list."""
        self.keywords_list.clear()
    
    def get_keywords(self) -> List[str]:
        """
        Get the list of keywords.
        
        Returns:
            List of keyword strings
        """
        return [self.keywords_list.item(i).text() for i in range(self.keywords_list.count())]
    
    def set_keywords(self, keywords: List[str]):
        """
        Set the list of keywords.
        
        Args:
            keywords: List of keyword strings
        """
        self.keywords_list.clear()
        for keyword in keywords:
            if keyword.strip():
                self.keywords_list.addItem(keyword.strip())


class CategoriesWidget(QWidget):
    """Widget for selecting categories for different photobanks."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.categories = {}  # Dict mapping photobank names to lists of categories
        self.initUI()
    
    def initUI(self):
        """Initialize the UI."""
        self.layout = QGridLayout(self)
        
        # We'll add photobank comboboxes dynamically
        self.photobank_combos = {}
        
        self.layout.addWidget(QLabel("No categories loaded"), 0, 0)
    
    def set_categories(self, categories: Dict[str, List[str]]):
        """
        Set the available categories for each photobank.
        
        Args:
            categories: Dictionary mapping photobank names to lists of categories
        """
        self.categories = categories
        
        # Clear existing widgets
        for i in reversed(range(self.layout.count())): 
            self.layout.itemAt(i).widget().setParent(None)
        
        # Add a combobox for each photobank
        row = 0
        for photobank, cats in self.categories.items():
            label = QLabel(f"{photobank}:")
            combo = QComboBox()
            combo.addItems([""] + cats)  # Empty option first
            
            self.layout.addWidget(label, row, 0)
            self.layout.addWidget(combo, row, 1)
            
            self.photobank_combos[photobank] = combo
            row += 1
    
    def get_selected_categories(self) -> Dict[str, str]:
        """
        Get the selected categories for each photobank.
        
        Returns:
            Dictionary mapping photobank names to selected category strings
        """
        selected = {}
        for photobank, combo in self.photobank_combos.items():
            category = combo.currentText()
            if category:
                selected[photobank] = category
        return selected
    
    def set_selected_categories(self, selected_categories: Dict[str, List[str]]):
        """
        Set the selected categories for each photobank.
        
        Args:
            selected_categories: Dictionary mapping photobank names to lists of selected categories
        """
        for photobank, categories in selected_categories.items():
            if photobank in self.photobank_combos and categories:
                # Find the first category in the list that exists in the combobox
                for category in categories:
                    index = self.photobank_combos[photobank].findText(category)
                    if index >= 0:
                        self.photobank_combos[photobank].setCurrentIndex(index)
                        break


class ProcessingThread(QThread):
    """Thread for processing media files in the background."""
    
    # Signal emitted when processing is complete
    finished = pyqtSignal(dict)
    
    def __init__(self, orchestrator: Orchestrator, file_path: str):
        """
        Initialize the processing thread.
        
        Args:
            orchestrator: Orchestrator instance
            file_path: Path to the media file to process
        """
        super().__init__()
        self.orchestrator = orchestrator
        self.file_path = file_path
    
    def run(self):
        """Run the processing thread."""
        try:
            # Process the media file
            metadata = self.orchestrator.process_media_file(self.file_path)
            
            # Emit the finished signal with the results
            self.finished.emit(metadata)
            
        except Exception as e:
            logging.error(f"Error in processing thread: {e}")
            self.finished.emit({})


class EditorDialog(QDialog):
    """Dialog for editing metadata of a single media file."""
    
    # Signal emitted when metadata is saved
    metadata_saved = pyqtSignal(dict)
    
    def __init__(self, file_path: str, record: Dict[str, str] = None, 
                 categories_file: str = None, training_data_dir: str = None,
                 parent=None):
        """
        Initialize the editor dialog.
        
        Args:
            file_path: Path to the media file
            record: Media record dictionary (optional)
            categories_file: Path to the categories CSV file
            training_data_dir: Directory for storing training data
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.file_path = file_path
        self.record = record or {}
        self.categories_file = categories_file
        self.training_data_dir = training_data_dir
        
        # Initialize components
        self.media_loader = MediaLoader()
        self.metadata_generator = MetadataGenerator(
            categories_file=categories_file,
            training_data_dir=training_data_dir
        )
        
        # Initialize orchestrator
        self.orchestrator = Orchestrator(
            media_csv_path="",  # Not needed for single file processing
            categories_csv_path=categories_file,
            training_data_dir=training_data_dir,
            llm_client_type="local"  # Default to local
        )
        
        # Load available LLM clients
        self.available_llm_clients = self.orchestrator.get_available_llm_clients()
        
        self.initUI()
        self.loadMedia()
    
    def initUI(self):
        """Initialize the UI."""
        self.setWindowTitle("Metadata Editor")
        self.resize(1000, 800)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Splitter for preview and metadata
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Preview
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.preview_widget = MediaPreviewWidget()
        left_layout.addWidget(self.preview_widget)
        
        # LLM selection
        llm_group = QGroupBox("AI Model Selection")
        llm_layout = QVBoxLayout(llm_group)
        
        self.llm_combo = QComboBox()
        for client in self.available_llm_clients:
            self.llm_combo.addItem(
                client['name'], 
                {'type': client['type'], 'model_id': client['model_id']}
            )
        
        llm_layout.addWidget(QLabel("Select AI Model:"))
        llm_layout.addWidget(self.llm_combo)
        
        # Generate buttons
        gen_layout = QHBoxLayout()
        
        self.gen_title_btn = QPushButton("Generate Title")
        self.gen_title_btn.clicked.connect(self.generate_title)
        
        self.gen_desc_btn = QPushButton("Generate Description")
        self.gen_desc_btn.clicked.connect(self.generate_description)
        
        self.gen_keywords_btn = QPushButton("Generate Keywords")
        self.gen_keywords_btn.clicked.connect(self.generate_keywords)
        
        self.gen_all_btn = QPushButton("Generate All")
        self.gen_all_btn.clicked.connect(self.generate_all)
        
        gen_layout.addWidget(self.gen_title_btn)
        gen_layout.addWidget(self.gen_desc_btn)
        gen_layout.addWidget(self.gen_keywords_btn)
        gen_layout.addWidget(self.gen_all_btn)
        
        llm_layout.addLayout(gen_layout)
        left_layout.addWidget(llm_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        # Right side - Metadata
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Title
        title_layout = QVBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit()
        title_layout.addWidget(self.title_edit)
        right_layout.addLayout(title_layout)
        
        # Description
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setAcceptRichText(False)
        desc_layout.addWidget(self.desc_edit)
        right_layout.addLayout(desc_layout)
        
        # Keywords
        self.keywords_widget = KeywordsWidget()
        right_layout.addWidget(self.keywords_widget)
        
        # Categories
        categories_group = QGroupBox("Categories")
        categories_layout = QVBoxLayout(categories_group)
        
        self.categories_widget = CategoriesWidget()
        categories_layout.addWidget(self.categories_widget)
        
        right_layout.addWidget(categories_group)
        
        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_metadata)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Load categories
        if self.categories_file:
            categories = self.metadata_generator._load_categories()
            self.categories_widget.set_categories(categories)
    
    def loadMedia(self):
        """Load the media file and display it."""
        if not os.path.exists(self.file_path):
            QMessageBox.critical(self, "Error", f"File not found: {self.file_path}")
            return
        
        # Display the media
        self.preview_widget.set_media(self.file_path)
        
        # Load existing metadata from record
        if self.record:
            self.title_edit.setText(self.record.get("Název", ""))
            self.desc_edit.setText(self.record.get("Popis", ""))
            
            # Keywords
            keywords_str = self.record.get("Klíčová slova", "")
            if keywords_str:
                keywords = [kw.strip() for kw in keywords_str.split(",")]
                self.keywords_widget.set_keywords(keywords)
            
            # Categories
            categories_str = self.record.get("Kategorie", "")
            if categories_str:
                categories = [cat.strip() for cat in categories_str.split(",")]
                
                # Create a dictionary mapping each photobank to the categories
                selected_categories = {}
                for photobank in self.metadata_generator.categories:
                    selected_categories[photobank] = categories
                
                self.categories_widget.set_selected_categories(selected_categories)
    
    def set_processing_state(self, processing: bool):
        """
        Set the UI state during processing.
        
        Args:
            processing: True if processing, False otherwise
        """
        self.progress_bar.setVisible(processing)
        self.gen_title_btn.setEnabled(not processing)
        self.gen_desc_btn.setEnabled(not processing)
        self.gen_keywords_btn.setEnabled(not processing)
        self.gen_all_btn.setEnabled(not processing)
        self.save_btn.setEnabled(not processing)
        self.llm_combo.setEnabled(not processing)
    
    def update_llm_client(self):
        """Update the LLM client based on the selected option."""
        current_data = self.llm_combo.currentData()
        if not current_data:
            return
        
        client_type = current_data.get('type', 'local')
        model_id = current_data.get('model_id', '')
        
        self.orchestrator.set_llm_client(client_type, model_id)
    
    def generate_title(self):
        """Generate a title for the media file."""
        self.update_llm_client()
        self.set_processing_state(True)
        
        # Create and start the processing thread
        self.processing_thread = ProcessingThread(self.orchestrator, self.file_path)
        self.processing_thread.finished.connect(self.on_title_generated)
        self.processing_thread.start()
    
    def on_title_generated(self, metadata: Dict[str, Any]):
        """
        Handle the generated title.
        
        Args:
            metadata: Generated metadata dictionary
        """
        self.set_processing_state(False)
        
        if not metadata or 'title' not in metadata:
            QMessageBox.warning(self, "Error", "Failed to generate title")
            return
        
        self.title_edit.setText(metadata['title'])
    
    def generate_description(self):
        """Generate a description for the media file."""
        self.update_llm_client()
        self.set_processing_state(True)
        
        # Create and start the processing thread
        self.processing_thread = ProcessingThread(self.orchestrator, self.file_path)
        self.processing_thread.finished.connect(self.on_description_generated)
        self.processing_thread.start()
    
    def on_description_generated(self, metadata: Dict[str, Any]):
        """
        Handle the generated description.
        
        Args:
            metadata: Generated metadata dictionary
        """
        self.set_processing_state(False)
        
        if not metadata or 'description' not in metadata:
            QMessageBox.warning(self, "Error", "Failed to generate description")
            return
        
        self.desc_edit.setText(metadata['description'])
    
    def generate_keywords(self):
        """Generate keywords for the media file."""
        self.update_llm_client()
        self.set_processing_state(True)
        
        # Create and start the processing thread
        self.processing_thread = ProcessingThread(self.orchestrator, self.file_path)
        self.processing_thread.finished.connect(self.on_keywords_generated)
        self.processing_thread.start()
    
    def on_keywords_generated(self, metadata: Dict[str, Any]):
        """
        Handle the generated keywords.
        
        Args:
            metadata: Generated metadata dictionary
        """
        self.set_processing_state(False)
        
        if not metadata or 'keywords' not in metadata:
            QMessageBox.warning(self, "Error", "Failed to generate keywords")
            return
        
        self.keywords_widget.set_keywords(metadata['keywords'])
    
    def generate_all(self):
        """Generate all metadata for the media file."""
        self.update_llm_client()
        self.set_processing_state(True)
        
        # Create and start the processing thread
        self.processing_thread = ProcessingThread(self.orchestrator, self.file_path)
        self.processing_thread.finished.connect(self.on_all_generated)
        self.processing_thread.start()
    
    def on_all_generated(self, metadata: Dict[str, Any]):
        """
        Handle all generated metadata.
        
        Args:
            metadata: Generated metadata dictionary
        """
        self.set_processing_state(False)
        
        if not metadata:
            QMessageBox.warning(self, "Error", "Failed to generate metadata")
            return
        
        # Update UI with generated metadata
        if 'title' in metadata:
            self.title_edit.setText(metadata['title'])
        
        if 'description' in metadata:
            self.desc_edit.setText(metadata['description'])
        
        if 'keywords' in metadata:
            self.keywords_widget.set_keywords(metadata['keywords'])
        
        if 'categories' in metadata:
            self.categories_widget.set_selected_categories(metadata['categories'])
    
    def save_metadata(self):
        """Save the metadata."""
        # Collect metadata from UI
        metadata = {
            'title': self.title_edit.text(),
            'description': self.desc_edit.toPlainText(),
            'keywords': self.keywords_widget.get_keywords(),
            'categories': self.categories_widget.get_selected_categories()
        }
        
        # Save training data
        if self.training_data_dir:
            # Create a simple analysis dict for training
            analysis = {
                'metadata': {
                    'file_path': self.file_path,
                    'file_name': os.path.basename(self.file_path)
                }
            }
            
            self.metadata_generator.save_training_data(self.file_path, analysis, metadata)
        
        # Emit the saved signal
        self.metadata_saved.emit(metadata)
        
        # Accept the dialog
        self.accept()
