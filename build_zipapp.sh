#!/usr/bin/env bash
set -euo pipefail

# Create a Python zipapp (executable archive) from the cuddly_fiesta package
out="cuddly_fiesta.pyz"
python3 -m zipapp cuddly_fiesta -p "/usr/bin/env python3" -m "cuddly_fiesta.__main__:main" -o "$out"
echo "Created $out"

# Alternative simple version (no shebang)
python3 -m zipapp cuddly_fiesta -m 'cuddly_fiesta.__main__:main' -o cuddly_fiesta_simple.pyz
echo "Created cuddly_fiesta_simple.pyz"
