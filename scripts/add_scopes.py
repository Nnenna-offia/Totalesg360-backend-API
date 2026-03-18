#!/usr/bin/env python3
"""Add named scopes to the activities app.

Usage:
  python ./scripts/add_scopes.py --scope NON_EMISSION:Non-Emission --scope OTHER:Other
  python ./scripts/add_scopes.py --file scopes.csv
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


def parse_scope_arg(s):
    if ':' in s:
        code, name = s.split(':', 1)
    else:
        code = s
        name = s.replace('_', ' ').title()
    return code.strip(), name.strip()


def main():
    parser = argparse.ArgumentParser(description='Add named scopes to activities')
    parser.add_argument('--scope', action='append', help='Scope in CODE:Name form; repeatable', default=[])
    parser.add_argument('--file', type=str, help='CSV file with code,name per line')
    parser.add_argument('--force', action='store_true', help='Overwrite existing scope')
    parser.add_argument('--dry-run', action='store_true', help="Don't write to DB")
    args = parser.parse_args()

    to_create = []
    for s in args.scope:
        to_create.append(parse_scope_arg(s))

    if args.file:
        p = Path(args.file)
        if not p.exists():
            print('File not found:', args.file)
            return 2
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            parts = [x.strip() for x in line.split(',')]
            if len(parts) >= 2:
                code, name = parts[0], parts[1]
            else:
                code = parts[0]
                name = code.replace('_', ' ').title()
            to_create.append((code, name))

    if not to_create:
        print('No scopes provided. Use --scope CODE:Name')
        return 1

    created = []
    skipped = []
    for code, name in to_create:
        existing = Scope.objects.filter(code=code).first()
        if existing:
            if args.force:
                print(f'Recreating scope {code} -> {name}')
                if not args.dry_run:
                    existing.name = name
                    existing.description = f'Auto-updated scope {name}'
                    existing.save()
                created.append(code)
            else:
                print(f'Skipping existing scope {code} (name={existing.name})')
                skipped.append(code)
        else:
            print(f'Creating scope {code} -> {name}')
            if not args.dry_run:
                Scope.objects.create(code=code, name=name, description=f'Auto-created scope {name}')
            created.append(code)

    print('\nSummary:')
    print(f'  Created/updated: {len(created)} ({", ".join(created) if created else "none"})')
    print(f'  Skipped: {len(skipped)} ({", ".join(skipped) if skipped else "none"})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
