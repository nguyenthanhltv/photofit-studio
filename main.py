"""Entry point for Batch ID Photo Processor."""

import sys
import os

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config_manager import ConfigManager
from src.utils import setup_logging
from ui.main_window import MainWindow

def main():
    setup_logging(log_file="logs/processor.log")

    config_manager = ConfigManager()
    app = MainWindow(config_manager)
    app.mainloop()

if __name__ == "__main__":
    main()