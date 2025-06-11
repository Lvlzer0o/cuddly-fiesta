#!/usr/bin/env bash
set -euo pipefail

out="cuddly_fiesta.pyz"
python -m zipapp cuddly_fiesta -p "/usr/bin/env python3" -m "cuddly_fiesta.__main__:main" -o "$out"
echo "Created $out"
