"""Update the find-links path in pixi.toml to point to dist/<env_name>.

Usage:
    python fix_find_links.py <env_name>
"""

import re
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        print('Usage: fix_find_links.py <env_name>')
        sys.exit(1)

    env_name = sys.argv[1]
    toml_file = Path('pixi.toml')

    try:
        content = toml_file.read_text(encoding='utf-8')
    except FileNotFoundError:
        print('Error: pixi.toml file not found.')
        sys.exit(1)

    updated_content = re.sub(
        r'find-links\s*=\s*\[\s*\{[^}]*path\s*=\s*["\'][^"\']*["\'][^}]*\}\s*\]',
        f'find-links = [{{ path = "dist/{env_name}" }}]',
        content,
    )

    toml_file.write_text(updated_content, encoding='utf-8')


if __name__ == '__main__':
    main()
