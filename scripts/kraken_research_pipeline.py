#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from core.walk_forward_lab import run_walk_forward
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 p=argparse.ArgumentParser(description='V30.1 Kraken training/Q1 walk-forward research pipeline')
 p.add_argument('--training-dir',required=True,type=Path)
 p.add_argument('--validation-dir',required=True,type=Path)
 a=p.parse_args(); print(json.dumps(run_walk_forward(ROOT,a.training_dir,a.validation_dir),indent=2))
