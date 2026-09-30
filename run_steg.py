#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"src"))
from steg.cli import main
raise SystemExit(main())
