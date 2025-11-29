"""
Unified progress tracking for multi-stage processing.

This module provides a unified progress tracking system that displays both overall
progress and per-bank progress, eliminating redundant progress bars and improving UX.
"""

import logging
from typing import Dict, List, Optional
from tqdm import tqdm


class UnifiedProgressTracker:
    """Unified progress tracking for multi-stage processing."""

    def __init__(self, banks: List[str], records_per_bank: Dict[str, int]):
        """
        Initialize progress tracker.

        Args:
            banks: List of bank names to process
            records_per_bank: Dictionary mapping bank name to record count
        """
        self.banks = banks
        self.records_per_bank = records_per_bank
        self.total_records = sum(records_per_bank.values())
        self.processed_records = 0
        self.current_bank_index = 0

        # Create main progress bar
        self.main_pbar = tqdm(
            total=self.total_records,
            desc="Processing all banks",
            unit="files",
            position=0
        )

        # Current bank progress bar (will be updated)
        self.current_bank_pbar: Optional[tqdm] = None

        logging.info(f"Starting processing of {self.total_records} files across {len(banks)} banks")

    def start_bank(self, bank_name: str) -> None:
        """
        Start processing a new bank.

        Args:
            bank_name: Name of the bank to start processing
        """
        if self.current_bank_pbar:
            self.current_bank_pbar.close()

        bank_record_count = self.records_per_bank[bank_name]
        bank_position = self.current_bank_index + 1

        self.current_bank_pbar = tqdm(
            total=bank_record_count,
            desc=f"[{bank_position}/{len(self.banks)}] {bank_name}",
            unit="files",
            position=1,
            leave=False
        )

        logging.info(f"Starting bank {bank_name} ({bank_record_count} files)")
        self.current_bank_index += 1

    def update_progress(self, files_processed: int = 1) -> None:
        """
        Update progress for current bank and overall.

        Args:
            files_processed: Number of files processed in this update
        """
        self.main_pbar.update(files_processed)
        if self.current_bank_pbar:
            self.current_bank_pbar.update(files_processed)
        self.processed_records += files_processed

    def finish_bank(self) -> None:
        """Finish processing current bank."""
        if self.current_bank_pbar:
            self.current_bank_pbar.close()
            self.current_bank_pbar = None

    def finish_all(self) -> None:
        """Finish all processing."""
        if self.current_bank_pbar:
            self.current_bank_pbar.close()
        self.main_pbar.close()

        logging.info(f"Completed processing {self.processed_records} files")

    def get_summary(self) -> str:
        """
        Get processing summary.

        Returns:
            Summary string with completion statistics
        """
        completion_rate = (self.processed_records / self.total_records) * 100 if self.total_records > 0 else 0
        return f"Processed {self.processed_records}/{self.total_records} files ({completion_rate:.1f}%)"
