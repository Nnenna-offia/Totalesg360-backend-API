"""Validation helpers for organization hierarchy rules."""
from django.core.exceptions import ValidationError


ALLOWED_CHILDREN = {
    "group": ["subsidiary"],
    "subsidiary": ["facility", "department"],
    "facility": ["department"],
    "department": [],
}


def validate_hierarchy(parent, entity_type, instance=None):
    """Validate organization parent-child relationships."""
    if not entity_type:
        raise ValidationError("Entity type is required")

    if parent and instance and parent.pk == instance.pk:
        raise ValidationError("An organization cannot be its own parent")

    if parent and not getattr(parent, "is_active", True):
        raise ValidationError("Parent organization must be active and valid")

    if parent:
        current = parent
        while current is not None:
            if instance and current.pk == instance.pk:
                raise ValidationError("Cannot create circular organization hierarchy")
            current = current.parent

        allowed = ALLOWED_CHILDREN.get(parent.entity_type, [])
        if entity_type not in allowed:
            raise ValidationError(
                f"{entity_type} cannot be created under {parent.entity_type}"
            )
        return

    if entity_type != "group":
        raise ValidationError("Only GROUP can exist without a parent")