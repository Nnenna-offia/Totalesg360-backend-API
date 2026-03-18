#!/usr/bin/env python3
"""Create Scope records for activities.

Creates Scope objects with codes from --start to --end (inclusive).
Defaults: --start 1 --end 3

Examples:
  python ./scripts/create_scopes.py
  python ./scripts/create_scopes.py --start 1 --end 5 --force
  python ./scripts/create_scopes.py --start 10 --end 12 --dry-run
"""
import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR))

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

import django
django.setup()

from activities.models.scope import Scope


def main():
    parser = argparse.ArgumentParser(description='Create Scope rows for activities')
    parser.add_argument('--start', type=int, default=1, help='Start integer (inclusive)')
    parser.add_argument('--end', type=int, default=3, help='End integer (inclusive)')
    parser.add_argument('--force', action='store_true', help='Recreate existing scopes')
    parser.add_argument('--dry-run', action='store_true', help="Don't write to DB; just print actions")
    args = parser.parse_args()

    if args.start > args.end:
        print('Error: --start must be <= --end')
        return 1

    created = []
    skipped = []
    for n in range(args.start, args.end + 1):
        code = str(n)
        name = f"Scope {n}"
        description = f"Auto-created scope {n}"
        existing = Scope.objects.filter(code=code).first()
        if existing:
            if args.force:
                print(f"Recreating existing Scope code={code}")
                if not args.dry_run:
                    existing.name = name
                    existing.description = description
                    existing.save()
                created.append(code)
            else:
                print(f"Skipping existing Scope code={code}")
                skipped.append(code)
        else:
            print(f"Creating Scope code={code} name={name}")
            if not args.dry_run:
                Scope.objects.create(code=code, name=name, description=description)
            created.append(code)

    print('\nSummary:')
    print(f"  Created/updated: {len(created)} ({', '.join(created) if created else 'none'})")
    print(f"  Skipped: {len(skipped)} ({', '.join(skipped) if skipped else 'none'})")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
