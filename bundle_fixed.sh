#!/usr/bin/env bash
set -euo pipefail

# Create a single-file executable Python application by bundling all modules
# Using zipapp without specifying a main entry point since we have __main__.py
python3 -m zipapp cuddly_fiesta -p "/usr/bin/env python3" -o run.py
chmod +x run.py
echo "Created single-file run.py"

# Alternative method (manual bundling)
OUT="run_manual.py"

# Start new run.py with a shebang
printf '#!/usr/bin/env python3\n\n' > "$OUT"

# Add imports at the top
printf 'import sys\nfrom cuddly_fiesta.__main__ import main\n\n' >> "$OUT"

# Add main entry point
printf 'if __name__ == "__main__":\n' >> "$OUT"
printf '    sys.exit(main())\n' >> "$OUT"

chmod +x "$OUT"
echo "Created manual bundle $OUT"
echo ""
echo "To run the application, use one of the following commands:"
echo "  ./run.py"
echo "  ./run_manual.py"
echo ""
echo "Or install it as a package with: pip install -e ."
echo "Then you can run: python -m cuddly_fiesta [gui|animate|baseline]"
