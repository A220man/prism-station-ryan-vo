#!/bin/bash
cd /var/lib/alan-portfolio/workspaces/ryan/prism-station-ryan-vo/backend
python -m pytest tests/test_main.py -v 2>&1
