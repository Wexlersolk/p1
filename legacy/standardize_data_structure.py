"""Utility script to normalise the CSV directory layout.

Target layout: <exchange>/<market_type>/<symbol>/<csv files>
When CSV files are discovered directly under <exchange>/<market_type>, they are
moved into a BTC subfolder. Existing symbol folders are left untouched.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

# Root directory that stores exchange data.
DATA_ROOT = Path(__file__).resolve().parent.parent / "data_many"


def iter_market_dirs(root: Path) -> Iterable[Path]:
    for exchange_dir in root.iterdir():
        if not exchange_dir.is_dir():
            continue
        for market_dir in exchange_dir.iterdir():
            if not market_dir.is_dir():
                continue
            yield market_dir


def move_lonely_csv_to_btc(market_dir: Path) -> None:
    csv_files = [path for path in market_dir.glob("*.csv") if path.is_file()]
    if not csv_files:
        return

    btc_dir = market_dir / "BTC"
    btc_dir.mkdir(exist_ok=True)

    for csv_path in csv_files:
        target_path = btc_dir / csv_path.name
        print(f"Moving {csv_path.relative_to(DATA_ROOT)} -> {target_path.relative_to(DATA_ROOT)}")
        csv_path.rename(target_path)


def rename_files_to_timeframe(symbol_dir: Path) -> None:
    for csv_path in symbol_dir.glob("*.csv"):
        if not csv_path.is_file():
            continue

        stem = csv_path.stem
        parts = stem.split("_")
        timeframe = parts[-1] if parts else stem

        new_name = f"{timeframe}.csv"
        new_path = csv_path.with_name(new_name)

        if new_path == csv_path:
            continue

        if new_path.exists() and new_path != csv_path:
            print(f"Skipping rename, target exists: {new_path.relative_to(DATA_ROOT)}")
            continue

        print(f"Renaming {csv_path.relative_to(DATA_ROOT)} -> {new_path.relative_to(DATA_ROOT)}")
        csv_path.rename(new_path)


def main() -> None:
    if not DATA_ROOT.exists():
        raise SystemExit(f"Data root does not exist: {DATA_ROOT}")

    for market_dir in iter_market_dirs(DATA_ROOT):
        move_lonely_csv_to_btc(market_dir)
        for symbol_dir in market_dir.iterdir():
            if symbol_dir.is_dir():
                rename_files_to_timeframe(symbol_dir)


if __name__ == "__main__":
    main()
