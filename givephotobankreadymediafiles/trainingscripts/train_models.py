#!/usr/bin/env python
"""
Train Models - Script for training neural network models on collected metadata.
"""
import os
import sys
import argparse
import logging
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.logging_config import setup_logging
from shared.file_operations import ensure_directory
from core.trainer import Trainer


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train neural network models on collected metadata."
    )
    parser.add_argument("--training_data_dir", type=str, default="../data/training",
                        help="Directory containing training data")
    parser.add_argument("--models_dir", type=str, default="../data/models",
                        help="Directory for saving trained models")
    parser.add_argument("--log_dir", type=str, default="../logs",
                        help="Directory for log files")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--model", type=str, choices=["all", "tags", "title", "description"],
                        default="all", help="Which model to train")
    
    return parser.parse_args()


def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    ensure_directory(args.log_dir)
    log_file = os.path.join(args.log_dir, "train_models.log")
    setup_logging(debug=args.debug, log_file=log_file)
    
    # Log startup
    logging.info("Starting train_models.py")
    
    # Ensure directories exist
    ensure_directory(args.training_data_dir)
    ensure_directory(args.models_dir)
    
    # Initialize trainer
    trainer = Trainer(
        training_data_dir=args.training_data_dir,
        models_dir=args.models_dir
    )
    
    # Train models
    if args.model == "all":
        results = trainer.train_all_models()
        
        # Log results
        for model, success in results.items():
            if success:
                logging.info(f"Successfully trained {model}")
            else:
                logging.error(f"Failed to train {model}")
        
        # Return success if all models were trained successfully
        return 0 if all(results.values()) else 1
    
    elif args.model == "tags":
        # Load training data
        training_data = trainer.load_training_data()
        
        if not training_data:
            logging.error("No training data available")
            return 1
        
        # Prepare data and train model
        features, keywords = trainer.prepare_tag_training_data(training_data)
        if features and keywords:
            success = trainer.train_tag_model(features, keywords)
            return 0 if success else 1
        else:
            logging.error("Failed to prepare training data")
            return 1
    
    elif args.model == "title":
        # Load training data
        training_data = trainer.load_training_data()
        
        if not training_data:
            logging.error("No training data available")
            return 1
        
        # Prepare data and train model
        features, titles = trainer.prepare_title_training_data(training_data)
        if features and titles:
            success = trainer.train_title_model(features, titles)
            return 0 if success else 1
        else:
            logging.error("Failed to prepare training data")
            return 1
    
    elif args.model == "description":
        # Load training data
        training_data = trainer.load_training_data()
        
        if not training_data:
            logging.error("No training data available")
            return 1
        
        # Prepare data and train model
        features, descriptions = trainer.prepare_description_training_data(training_data)
        if features and descriptions:
            success = trainer.train_description_model(features, descriptions)
            return 0 if success else 1
        else:
            logging.error("Failed to prepare training data")
            return 1
    
    else:
        logging.error(f"Unknown model: {args.model}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
