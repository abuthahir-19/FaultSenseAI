#!/usr/bin/env python3
"""Run this once to populate ChromaDB from the CSV."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.utils.logger import setup_logger
from backend.app.rag.ingestion import IngestionPipeline
from backend.app.config import get_settings

setup_logger()


def main():
    settings = get_settings()
    pipeline = IngestionPipeline(settings)
    count = pipeline.ingest_csv(settings.DATA_PATH)
    print(f"\nIngestion complete. {count} documents indexed into ChromaDB.")


if __name__ == "__main__":
    main()
