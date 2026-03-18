from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from roles.models.capability import Capability
from roles.models.role_capability import RoleCapability
from roles.models import Role
from organizations.models import Organization
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = (
        "Ensure 'org.manage' capability exists and assign it to a role.\n"
        "Usage examples:\n"
        "  python manage.py grant_org_manage --org <org_id_or_slug> --username alice\n"
        "  python manage.py grant_org_manage --org <org_id> --role admin\n"
    )

    def add_arguments(self, parser):
        parser.add_argument("--org", dest="org", required=True, help="Organization id, slug, or name")
        parser.add_argument("--username", dest="username", help="Username (optional) to infer role from membership")
        parser.add_argument("--email", dest="email", help="Email (optional) to infer role from membership")
        parser.add_argument("--role", dest="role_code", help="Role code to grant capability to (optional)")
        parser.add_argument("--activate", action="store_true", dest="activate", help="Ensure RoleCapability is set active")

    def handle(self, *args, **options):
        org_q = options.get("org")
        username = options.get("username")
        email = options.get("email")
        role_code = options.get("role_code")
        activate = options.get("activate")

        org = Organization.objects.filter(id=org_q).first()
        if not org:
            org = Organization.objects.filter(slug=org_q).first() if hasattr(Organization, "slug") else None
        if not org:
            org = Organization.objects.filter(name__iexact=org_q).first()
        if not org:
            raise CommandError(f"Organization not found for '{org_q}'")

        # ensure capability
        cap, created = Capability.objects.get_or_create(code="org.manage", defaults={"name": "Manage Organization", "description": "Full org-level management"})
        if created:
            self.stdout.write(self.style.SUCCESS("Created Capability 'org.manage'."))
        else:
            self.stdout.write("Capability 'org.manage' already exists.")

        role = None
        User = get_user_model()
        membership_role = None

        if role_code:
            role = Role.objects.filter(code=role_code).first()
            if not role:
                raise CommandError(f"Role with code '{role_code}' not found")
            self.stdout.write(f"Found role '{role.code}'.")
        else:
            user = None
            if username:
                user = User.objects.filter(username=username).first()
            elif email:
                user = User.objects.filter(email__iexact=email).first()

            if user:
                # find membership for org
                membership = user.memberships.filter(organization=org).select_related("role").first()
                if not membership:
                    raise CommandError("User has no membership for the specified organization")
                membership_role = membership.role
                role = membership_role
                self.stdout.write(f"Using role '{role.code}' from user's membership.")
            else:
                raise CommandError("Either --role or --username/--email must be provided to determine target role")

        # create mapping
        with transaction.atomic():
            rc, rc_created = RoleCapability.objects.get_or_create(role=role, capability=cap, defaults={"is_active": bool(activate)})
            if not rc_created and activate:
                if not rc.is_active:
                    rc.is_active = True
                    rc.save(update_fields=["is_active"])            

        if rc_created:
            self.stdout.write(self.style.SUCCESS(f"Granted 'org.manage' to role '{role.code}'."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Role '{role.code}' already has 'org.manage' (activated={rc.is_active})."))

        self.stdout.write(self.style.NOTICE("Done."))
