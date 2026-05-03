from copy import deepcopy

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connections, transaction


class Command(BaseCommand):
    help = (
        "Reset local demo and ESG master data in an FK-safe way (via flush), "
        "with optional superuser preservation. Migrations are kept."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="default",
            help="Database alias to reset (default: default)",
        )
        parser.add_argument(
            "--keep-superusers",
            action="store_true",
            default=False,
            help="Preserve and restore superusers after reset (default: disabled)",
        )
        parser.add_argument(
            "--drop-superusers",
            action="store_true",
            help="Explicitly remove all users including superusers.",
        )

    def _snapshot_superusers(self, using):
        User = get_user_model()

        field_names = [
            f.attname
            for f in User._meta.concrete_fields
            if not getattr(f, "auto_created", False)
        ]

        superusers = list(User.objects.using(using).filter(is_superuser=True))
        rows = [deepcopy(dict(u.__dict__)) for u in superusers]

        # Keep only model concrete fields for safe restore.
        for row in rows:
            for key in list(row.keys()):
                if key not in field_names:
                    del row[key]

        groups_map = {
            str(u.pk): list(u.groups.values_list("id", flat=True)) for u in superusers
        }
        perms_map = {
            str(u.pk): list(u.user_permissions.values_list("id", flat=True)) for u in superusers
        }

        return rows, groups_map, perms_map

    def _restore_superusers(self, using, rows, groups_map, perms_map):
        if not rows:
            return 0

        User = get_user_model()
        restored = 0

        with transaction.atomic(using=using):
            for row in rows:
                obj = User(**row)
                obj.save(using=using, force_insert=True)
                restored += 1

                user_groups = groups_map.get(str(obj.pk), [])
                user_perms = perms_map.get(str(obj.pk), [])

                if user_groups:
                    valid_groups = Group.objects.using(using).filter(id__in=user_groups)
                    obj.groups.set(valid_groups)

                if user_perms:
                    valid_perms = Permission.objects.using(using).filter(id__in=user_perms)
                    obj.user_permissions.set(valid_perms)

        return restored

    def _fallback_truncate_demo_tables(self, using, keep_superusers):
        """Fallback reset path when Django flush cannot run.

        Truncates only existing tables relevant to demo data and uses CASCADE
        to avoid FK ordering issues.
        """
        connection = connections[using]
        existing = set(connection.introspection.table_names())

        prefixes = [
            "organizations_",
            "activities_",
            "targets_",
            "reports_",
            "dashboard_",
            "esg_scoring_",
            "indicators_",
        ]
        exact_tables = {
            "submissions_activitysubmission",
            "submissions_reportingperiod",
            "submissions_datasubmission",
            "emissions_calculatedemission",
            "compliance_framework_readiness",
            "compliance_gap_priority",
            "compliance_recommendation",
            "compliance_framework_requirement",
            "compliance_indicator_framework_mapping",
        }

        if not keep_superusers:
            exact_tables.update(
                {
                    "accounts_user",
                    "accounts_user_groups",
                    "accounts_user_user_permissions",
                    "accounts_refresh_token",
                    "accounts_emailverification",
                    "accounts_passwordreset",
                }
            )

        tables = []
        for table in sorted(existing):
            if table in exact_tables or any(table.startswith(p) for p in prefixes):
                tables.append(table)

        if not tables:
            return 0, False

        sql_list = connection.ops.sql_flush(
            style=no_style(),
            tables=tables,
            reset_sequences=True,
            allow_cascade=True,
        )
        with connection.cursor() as cursor, transaction.atomic(using=using):
            for statement in sql_list:
                cursor.execute(statement)

        accounts_wiped = "accounts_user" in tables
        return len(tables), accounts_wiped

    def handle(self, *args, **options):
        using = options["database"]
        keep_superusers = bool(options["keep_superusers"])
        if bool(options["drop_superusers"]):
            keep_superusers = False

        self.stdout.write(self.style.WARNING("Starting demo data reset..."))
        self.stdout.write(f"Database alias: {using}")

        rows = []
        groups_map = {}
        perms_map = {}

        if keep_superusers:
            rows, groups_map, perms_map = self._snapshot_superusers(using)
            self.stdout.write(f"Superusers captured for restore: {len(rows)}")
        else:
            self.stdout.write("All users (including superusers) will be removed.")

        # Flush is FK-safe and keeps migrations intact.
        users_wiped = False
        try:
            call_command(
                "flush",
                database=using,
                interactive=False,
                verbosity=options.get("verbosity", 1),
            )
            self.stdout.write("Primary reset path: Django flush")
            users_wiped = True
        except CommandError as exc:
            self.stdout.write(
                self.style.WARNING(
                    f"Flush failed ({exc}). Falling back to table-level truncate."
                )
            )
            table_count, users_wiped = self._fallback_truncate_demo_tables(using, keep_superusers)
            self.stdout.write(f"Fallback reset path truncated tables: {table_count}")

        restored = 0
        if keep_superusers and rows and users_wiped:
            restored = self._restore_superusers(using, rows, groups_map, perms_map)

        self.stdout.write(self.style.SUCCESS("Demo data reset complete."))
        self.stdout.write("Migrations were not removed.")
        self.stdout.write(f"Superusers restored: {restored}")