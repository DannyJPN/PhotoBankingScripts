"""
Main window for batch processing of media files.
"""

import logging
import os
from typing import Any

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QAction,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from givephotobankreadymediafileslib.constants import (
    COL_CATEGORIES,
    COL_CREATE_DATE,
    COL_DESCRIPTION,
    COL_FILE,
    COL_KEYWORDS,
    COL_PATH,
    COL_TITLE,
)
from givephotobankreadymediafileslib.gui.editor_dialog import EditorDialog
from givephotobankreadymediafileslib.media_orchestrator import MediaOrchestrator


class ProcessingThread(QThread):
    """Thread for processing media files in the background."""

    # Signal emitted when processing is complete
    finished = pyqtSignal(dict)

    def __init__(self, orchestrator: MediaOrchestrator):
        """
        Initialize the processing thread.

        Args:
            orchestrator: MediaOrchestrator instance
        """
        super().__init__()
        self.orchestrator = orchestrator

    def run(self):
        """Run the processing thread."""
        try:
            # Process the file
            if hasattr(self, "file_path"):
                result = self.orchestrator.process_media_file(self.file_path)
            else:
                result = {"error": "No file path specified"}

            # Emit the finished signal with the results
            self.finished.emit(result or {})

        except Exception as e:
            logging.error(f"Error in processing thread: {e}")
            self.finished.emit({"error": str(e)})


class MainWindow(QMainWindow):
    """Main window for batch processing of media files."""

    def __init__(
        self, media_csv_path: str, categories_csv_path: str, training_data_dir: str, available_models=None, parent=None
    ):
        """
        Initialize the main window.

        Args:
            media_csv_path: Path to the CSV file with media records
            categories_csv_path: Path to the CSV file with photobank categories
            training_data_dir: Directory for storing training data
            available_models: Dictionary of available models by type
            parent: Parent widget
        """
        super().__init__(parent)

        # Save paths for later use
        self.media_csv_path = media_csv_path
        self.categories_csv_path = categories_csv_path
        self.training_data_dir = training_data_dir
        self.models_dir = os.path.join(os.path.dirname(training_data_dir), "models")

        # Define available metadata generators based on available models
        self.available_generators = []

        # Add neural network generators if available
        if available_models and "neural_networks" in available_models and available_models["neural_networks"]:
            self.available_generators.append({"name": "Neural Network", "type": "neural", "model_id": "default"})

        # Add local LLM generators if available
        if available_models and "local_llm" in available_models and available_models["local_llm"]:
            for model_id in available_models["local_llm"]:
                provider, model_name = model_id.split("/", 1)
                self.available_generators.append(
                    {"name": f"Local LLM ({provider}/{model_name})", "type": "local_llm", "model_id": model_id}
                )

        # Add online LLM generators if available
        if available_models and "online_llm" in available_models and available_models["online_llm"]:
            for model_id in available_models["online_llm"]:
                provider, model_name = model_id.split("/", 1)
                self.available_generators.append(
                    {"name": f"Online LLM ({provider}/{model_name})", "type": "online_llm", "model_id": model_id}
                )

        # If no generators are available, add a default one
        if not self.available_generators:
            self.available_generators.append(
                {"name": "Neural Network (Default)", "type": "neural", "model_id": "default"}
            )

        # Initialize orchestrator with default generator
        self.orchestrator = MediaOrchestrator(
            media_csv_path=media_csv_path,
            categories_csv_path=categories_csv_path,
            training_data_dir=training_data_dir,
            models_dir=self.models_dir,
            generator_type="neural",  # Default to neural network
        )

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

        # Generator selection
        generator_layout = QHBoxLayout()

        generator_layout.addWidget(QLabel("AI Model:"))

        self.generator_combo = QComboBox()
        for generator in self.available_generators:
            self.generator_combo.addItem(
                generator["name"], {"type": generator["type"], "model_id": generator["model_id"]}
            )

        generator_layout.addWidget(self.generator_combo)
        generator_layout.addStretch()

        main_layout.addLayout(generator_layout)

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

    def check_generators_availability(self):
        """
        Check the availability of all metadata generators and update the UI accordingly.
        """
        # Check if data is loaded
        if not self.orchestrator.data_loaded:
            if not self.orchestrator.load_data():
                QMessageBox.warning(
                    self,
                    "Data Loading Error",
                    "Failed to load necessary data from CSV files. \n\n"
                    "Please check that the following files exist and are accessible:\n"
                    f"- Media CSV: {self.media_csv_path}\n"
                    f"- Categories CSV: {self.categories_csv_path}",
                )
                return False

        # Initialize generators
        if not self.orchestrator.generators_initialized:
            if not self.orchestrator.initialize_generators():
                QMessageBox.warning(
                    self,
                    "Generator Initialization Error",
                    "Failed to initialize metadata generators.\n\n"
                    "Please check that the selected generator is available.",
                )
                return False

        return True

    def loadRecords(self):
        """Load media records from the CSV file."""
        # Check if orchestrator has loaded data
        if not self.orchestrator.data_loaded:
            if not self.orchestrator.load_data():
                QMessageBox.warning(
                    self,
                    "Data Loading Error",
                    "Failed to load media records from CSV file.\n\n"
                    f"Please check that the file exists and is accessible:\n"
                    f"- Media CSV: {self.media_csv_path}",
                )
                return

        # Get records from orchestrator
        self.records = self.orchestrator.media_data

        if not self.records:
            self.status_bar.showMessage("No media records found")
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
        self.status_bar.showMessage(f"Loaded {len(self.records)} media records")

        # Check generators availability
        self.check_generators_availability()

    def update_metadata_generator(self):
        """Update the metadata generator based on the selected option."""
        current_data = self.generator_combo.currentData()
        if not current_data:
            return

        generator_type = current_data.get("type", "neural")
        model_id = current_data.get("model_id", "default")

        # Create a new orchestrator with the selected generator
        self.orchestrator = MediaOrchestrator(
            media_csv_path=self.media_csv_path,
            categories_csv_path=self.categories_csv_path,
            training_data_dir=self.training_data_dir,
            models_dir=self.models_dir,
            generator_type=generator_type,
            model_name=model_id,
        )

        # Check if the selected generator is available
        if not self.check_generators_availability():
            # If not available, show warning and revert to neural network generator
            self.orchestrator = MediaOrchestrator(
                media_csv_path=self.media_csv_path,
                categories_csv_path=self.categories_csv_path,
                training_data_dir=self.training_data_dir,
                models_dir=self.models_dir,
                generator_type="neural",
            )

            # Update combo box selection
            for i in range(self.generator_combo.count()):
                data = self.generator_combo.itemData(i)
                if data and data.get("type") == "neural":
                    self.generator_combo.setCurrentIndex(i)
                    break

    def set_processing_state(self, processing: bool):
        """
        Set the UI state during processing.

        Args:
            processing: True if processing, False otherwise
        """
        self.progress_bar.setVisible(processing)
        self.process_btn.setEnabled(not processing)
        self.edit_btn.setEnabled(not processing)
        self.generator_combo.setEnabled(not processing)

    def processNext(self):
        """Process the selected record."""
        # Get selected row
        selected_rows = self.records_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a record to process.")
            return

        row_index = selected_rows[0].row()
        if row_index < 0 or row_index >= len(self.records):
            return

        # Get file path
        record = self.records[row_index]
        file_path = record.get(COL_PATH, "")

        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"File not found: {file_path}")
            return

        # Update metadata generator
        self.update_metadata_generator()

        # Check if generators are available
        if not self.check_generators_availability():
            return

        self.set_processing_state(True)

        # Create and start the processing thread
        self.processing_thread = ProcessingThread(self.orchestrator)
        self.processing_thread.file_path = file_path
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.start()

    def on_processing_finished(self, result: dict[str, Any]):
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
            self, "Success", f"Successfully processed file: {result.get('record', {}).get(COL_FILE, '')}"
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
            parent=self,
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
            f"Training data: {self.training_data_dir}",
        )

    def trainModels(self):
        """Train neural network models."""
        # In a real implementation, this would start the training process
        QMessageBox.information(
            self,
            "Train Models",
            "Model training would be started here.\n\n"
            "This would use the training data to incrementally train the neural networks.",
        )
