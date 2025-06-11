#!/usr/bin/env bash
set -euo pipefail

# Create a single-file executable Python application by bundling all modules
python3 -m zipapp cuddly_fiesta -p "/usr/bin/env python3" -m "cuddly_fiesta.__main__:main" -o run.py
chmod +x run.py
echo "Created single-file run.py"

# Alternative method (manual bundling)
OUT="run_manual.py"

# Start new run.py with a shebang
printf '#!/usr/bin/env python3\n\n' > "$OUT"

# Concatenate each module in the package
for module in cuddly_fiesta/*.py; do
  name=$(basename "$module")
  [[ "$name" == "__init__.py" ]] && continue
  
  echo "# ==== $name ====" >> "$OUT"
  # Remove any existing shebang and trailing CLI sections
  sed '/^#!\/usr\/bin\/env/d' "$module" | sed '/if __name__ == "__main__":/,$d' >> "$OUT"
  echo -e "\n" >> "$OUT"
done

# Add main entry point
echo "if __name__ == \"__main__\":" >> "$OUT"
echo "    main()" >> "$OUT"

chmod +x "$OUT"
echo "Created manual bundle $OUT"
