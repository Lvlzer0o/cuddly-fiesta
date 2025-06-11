#!/usr/bin/env bash
set -euo pipefail

python3 -m zipapp cuddly_fiesta -p "/usr/bin/env python3" -m "cuddly_fiesta.__main__:main" -o run.py
chmod +x run.py
echo "Created single-file run.py"
