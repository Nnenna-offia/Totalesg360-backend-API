from django.core.management.base import BaseCommand
from django.db import transaction

from roles.models import Role, RoleCapability
from roles.models import Capability


class Command(BaseCommand):
    help = "Grant all existing capabilities to a role (default: org_owner)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--role",
            dest="role_code",
            default="org_owner",
            help="Role code to grant capabilities to (default: org_owner)",
        )

    def handle(self, *args, **options):
        role_code = options.get("role_code")
        try:
            role = Role.objects.get(code=role_code)
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Role with code '{role_code}' not found"))
            return

        caps = Capability.objects.all()
        created = 0
        updated = 0
        with transaction.atomic():
            for cap in caps:
                rc, was_created = RoleCapability.objects.get_or_create(
                    role=role, capability=cap, defaults={"is_active": True}
                )
                if was_created:
                    created += 1
                else:
                    if not rc.is_active:
                        rc.is_active = True
                        rc.save(update_fields=["is_active"])
                        updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Granted {created} new capabilities and updated {updated} existing ones for role '{role_code}'"
        ))
