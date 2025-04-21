"""
Main window for batch processing of media files.
"""
import os
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QComboBox, QPushButton, QGroupBox, QScrollArea,
    QWidget, QSplitter, QListWidget, QListWidgetItem, QMessageBox,
    QCheckBox, QProgressBar, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QStatusBar, QAction, QMenu, QToolBar
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon

from core.orchestrator import Orchestrator
from core.constants import (
    COL_FILE, COL_TITLE, COL_DESCRIPTION, COL_PREP_DATE, 
    COL_WIDTH, COL_HEIGHT, COL_RESOLUTION, COL_KEYWORDS,
    COL_CATEGORIES, COL_CREATE_DATE, COL_ORIGINAL, COL_PATH,
    COL_STATUS_PREFIX, STATUS_UNPROCESSED, STATUS_PROCESSED,
    ORIGINAL_YES
)
from gui.editor_dialog import EditorDialog


class ProcessingThread(QThread):
    """Thread for processing media files in the background."""
    
    # Signal emitted when processing is complete
    finished = pyqtSignal(dict)
    
    def __init__(self, orchestrator: Orchestrator):
        """
        Initialize the processing thread.
        
        Args:
            orchestrator: Orchestrator instance
        """
        super().__init__()
        self.orchestrator = orchestrator
    
    def run(self):
        """Run the processing thread."""
        try:
            # Process the next record
            result = self.orchestrator.process_next_record()
            
            # Emit the finished signal with the results
            self.finished.emit(result or {})
            
        except Exception as e:
            logging.error(f"Error in processing thread: {e}")
            self.finished.emit({})


class MainWindow(QMainWindow):
    """Main window for batch processing of media files."""
    
    def __init__(self, media_csv_path: str, categories_csv_path: str, 
                 training_data_dir: str, parent=None):
        """
        Initialize the main window.
        
        Args:
            media_csv_path: Path to the CSV file with media records
            categories_csv_path: Path to the CSV file with photobank categories
            training_data_dir: Directory for storing training data
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.media_csv_path = media_csv_path
        self.categories_csv_path = categories_csv_path
        self.training_data_dir = training_data_dir
        
        # Initialize orchestrator
        self.orchestrator = Orchestrator(
            media_csv_path=media_csv_path,
            categories_csv_path=categories_csv_path,
            training_data_dir=training_data_dir,
            llm_client_type="local"  # Default to local
        )
        
        # Load available LLM clients
        self.available_llm_clients = self.orchestrator.get_available_llm_clients()
        
        self.initUI()
        self.loadRecords()
    
    def initUI(self):
        """Initialize the UI."""
        self.setWindowTitle("Photobank Media Processor")
        self.resize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.loadRecords)
        toolbar.addAction(refresh_action)
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.showSettings)
        toolbar.addAction(settings_action)
        
        # Train models action
        train_action = QAction("Train Models", self)
        train_action.triggered.connect(self.trainModels)
        toolbar.addAction(train_action)
        
        # LLM selection
        llm_layout = QHBoxLayout()
        
        llm_layout.addWidget(QLabel("AI Model:"))
        
        self.llm_combo = QComboBox()
        for client in self.available_llm_clients:
            self.llm_combo.addItem(
                client['name'], 
                {'type': client['type'], 'model_id': client['model_id']}
            )
        
        llm_layout.addWidget(self.llm_combo)
        llm_layout.addStretch()
        
        main_layout.addLayout(llm_layout)
        
        # Records table
        self.records_table = QTableWidget()
        self.records_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.records_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.records_table.setAlternatingRowColors(True)
        self.records_table.doubleClicked.connect(self.editRecord)
        
        main_layout.addWidget(self.records_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.process_btn = QPushButton("Process Next")
        self.process_btn.clicked.connect(self.processNext)
        
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.editSelected)
        
        buttons_layout.addWidget(self.process_btn)
        buttons_layout.addWidget(self.edit_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
    
    def loadRecords(self):
        """Load media records from the CSV file."""
        # Get unprocessed records
        self.records = self.orchestrator.get_unprocessed_records()
        
        if not self.records:
            self.status_bar.showMessage("No unprocessed records found")
            self.records_table.setRowCount(0)
            self.records_table.setColumnCount(0)
            return
        
        # Set up table
        columns = ["File", "Title", "Description", "Keywords", "Categories", "Date Created"]
        self.records_table.setColumnCount(len(columns))
        self.records_table.setHorizontalHeaderLabels(columns)
        
        # Fill table
        self.records_table.setRowCount(len(self.records))
        for row, record in enumerate(self.records):
            self.records_table.setItem(row, 0, QTableWidgetItem(record.get(COL_FILE, "")))
            self.records_table.setItem(row, 1, QTableWidgetItem(record.get(COL_TITLE, "")))
            self.records_table.setItem(row, 2, QTableWidgetItem(record.get(COL_DESCRIPTION, "")))
            self.records_table.setItem(row, 3, QTableWidgetItem(record.get(COL_KEYWORDS, "")))
            self.records_table.setItem(row, 4, QTableWidgetItem(record.get(COL_CATEGORIES, "")))
            self.records_table.setItem(row, 5, QTableWidgetItem(record.get(COL_CREATE_DATE, "")))
        
        # Resize columns to content
        self.records_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Update status
        self.status_bar.showMessage(f"Loaded {len(self.records)} unprocessed records")
    
    def update_llm_client(self):
        """Update the LLM client based on the selected option."""
        current_data = self.llm_combo.currentData()
        if not current_data:
            return
        
        client_type = current_data.get('type', 'local')
        model_id = current_data.get('model_id', '')
        
        self.orchestrator.set_llm_client(client_type, model_id)
    
    def set_processing_state(self, processing: bool):
        """
        Set the UI state during processing.
        
        Args:
            processing: True if processing, False otherwise
        """
        self.progress_bar.setVisible(processing)
        self.process_btn.setEnabled(not processing)
        self.edit_btn.setEnabled(not processing)
        self.llm_combo.setEnabled(not processing)
    
    def processNext(self):
        """Process the next unprocessed record."""
        self.update_llm_client()
        self.set_processing_state(True)
        
        # Create and start the processing thread
        self.processing_thread = ProcessingThread(self.orchestrator)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.start()
    
    def on_processing_finished(self, result: Dict[str, Any]):
        """
        Handle the processing result.
        
        Args:
            result: Processing result dictionary
        """
        self.set_processing_state(False)
        
        if not result:
            QMessageBox.warning(self, "Error", "Failed to process record")
            return
        
        # Reload records
        self.loadRecords()
        
        # Show success message
        QMessageBox.information(
            self, 
            "Success", 
            f"Successfully processed file: {result.get('record', {}).get(COL_FILE, '')}"
        )
    
    def editRecord(self, index):
        """
        Edit the record at the given index.
        
        Args:
            index: Table index of the record to edit
        """
        row = index.row()
        if row < 0 or row >= len(self.records):
            return
        
        record = self.records[row]
        file_path = record.get(COL_PATH)
        
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", f"File not found: {file_path}")
            return
        
        # Open editor dialog
        dialog = EditorDialog(
            file_path=file_path,
            record=record,
            categories_file=self.categories_csv_path,
            training_data_dir=self.training_data_dir,
            parent=self
        )
        
        if dialog.exec_():
            # Reload records
            self.loadRecords()
    
    def editSelected(self):
        """Edit the selected record."""
        selected_rows = self.records_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "No record selected")
            return
        
        # Get the first selected row
        row = selected_rows[0].row()
        self.editRecord(self.records_table.model().index(row, 0))
    
    def showSettings(self):
        """Show settings dialog."""
        # In a real implementation, this would open a settings dialog
        QMessageBox.information(
            self, 
            "Settings", 
            "Settings dialog would be shown here.\n\n"
            f"Media CSV: {self.media_csv_path}\n"
            f"Categories CSV: {self.categories_csv_path}\n"
            f"Training data: {self.training_data_dir}"
        )
    
    def trainModels(self):
        """Train neural network models."""
        # In a real implementation, this would start the training process
        QMessageBox.information(
            self, 
            "Train Models", 
            "Model training would be started here.\n\n"
            "This would use the training data to incrementally train the neural networks."
        )
