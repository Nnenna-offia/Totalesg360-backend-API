from django.core.management.base import BaseCommand
from accounts.models import User, Membership
from roles.models import Role


class Command(BaseCommand):
    help = "Assign org_admin role to emmat300005+44@gmail.com if they have an org membership"

    def handle(self, *args, **options):
        email = 'emmat300005+44@gmail.com'
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            self.stdout.write('USER_NOT_FOUND')
            return
        self.stdout.write(f'USER: {user.email} {user.id}')
        memberships = list(user.memberships.select_related('organization', 'role'))
        if not memberships:
            self.stdout.write('NO_MEMBERSHIPS')
            return
        for m in memberships:
            org = getattr(m, 'organization', None)
            self.stdout.write(f'EXISTING_MEMBERSHIP: {m.id} {getattr(org,"id",None)} {getattr(org,"name",None)} {m.role.code}')
        org = memberships[0].organization if memberships else None
        if not org:
            self.stdout.write('NO_ORG_TO_ATTACH_ROLE')
            return
        try:
            role = Role.objects.get(code='org_admin')
        except Role.DoesNotExist:
            self.stdout.write('ROLE_NOT_FOUND')
            return
        exists = Membership.objects.filter(user=user, organization=org, role=role).exists()
        if exists:
            self.stdout.write('MEMBERSHIP_ALREADY_PRESENT')
        else:
            m = Membership.objects.create(user=user, organization=org, role=role, is_active=True, added_by=None)
            self.stdout.write(f'CREATED_MEMBERSHIP {m.id}')
