#!/usr/bin/env bash
set -euo pipefail

OUT="run.py"

# Start new run.py with a shebang
printf '#!/usr/bin/env python3\n\n' > "$OUT"

# Concatenate each module in the package
for module in cuddly_fiesta/*.py; do
    name=$(basename "$module")
    [[ "$name" == "__init__.py" ]] && continue
    echo "# ===== $name =====" >> "$OUT"
    # Remove any existing shebang and trailing CLI sections
    sed '/^#!\/usr\/bin\/env/d' "$module" | sed '/if __name__ == .__main__.:/,$d' >> "$OUT"
    echo -e "\n" >> "$OUT"
done

echo 'if __name__ == "__main__":' >> "$OUT"
echo '    main()' >> "$OUT"

chmod +x "$OUT"

