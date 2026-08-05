#!/usr/bin/env python3
from pathlib import Path
from scripts.core.candidate_validation import write_validation_queue

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    result = write_validation_queue(root)
    print(f"Published {result['candidate_count']} advisory validation candidates.")
