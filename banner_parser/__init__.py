__version__ = '0.1.0'

from pathlib import Path
import json

from .models import Banner, GachaItem

PACKS = Path('packs')
OUTPUT = Path('output')


def parse(path: Path):
    filename = path.stem
    print(filename)
    with path.open('r', encoding='utf8') as f:
        data = json.load(f)
    banner = Banner.from_data(data['data'])
    banner.save(OUTPUT / path.name)


def main():
    for fp in PACKS.glob('*v2.json'):
        parse(fp)
