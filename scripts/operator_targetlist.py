"""Rank Alberta operators by inactive well count. This is the ClosureIQ target list.

Usage: python3 operator_targetlist.py [N]   (default N=25)
"""
import sys
from lib import load_inactive

def main(n=25):
    df = load_inactive()
    ranked = (df.groupby("Licensee Name")
                .size().sort_values(ascending=False))
    print(f"{len(df):,} inactive wells across {df['BA Code'].nunique():,} operators\n")
    print(f"TOP {n} OPERATORS BY INACTIVE WELL COUNT")
    for i, (name, count) in enumerate(ranked.head(n).items(), 1):
        print(f"{i:>3}. {count:>7,}  {name}")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 25)
