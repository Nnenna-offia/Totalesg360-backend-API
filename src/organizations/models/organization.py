# organizations/models/organization.py
from django.db import models
from common.models import BaseModel
from django_countries.fields import CountryField


class Organization(BaseModel):
    """
    Represents a company/entity using the ESG platform.
    Supports hierarchical structure: Groups → Subsidiaries → Business Units.
    Settings field stores sector-specific configuration (dropdowns, scopes, etc.).
    """
    
    class PrimaryReportingFocus(models.TextChoices):
        NIGERIA = "NIGERIA", "Nigeria Regulators Only"
        INTERNATIONAL = "INTERNATIONAL", "International Frameworks Only"
        HYBRID = "HYBRID", "Nigeria + International (Hybrid)"
    
    class EntityType(models.TextChoices):
        GROUP = "group", "Group"
        SUBSIDIARY = "subsidiary", "Subsidiary"
        FACILITY = "facility", "Facility"
        DEPARTMENT = "department", "Department"

    OrganizationType = EntityType
    
    # Hierarchy fields
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="subsidiaries",
        db_index=True,
        help_text="Parent organization (for subsidiaries and business units)"
    )
    
    entity_type = models.CharField(
        max_length=20,
        choices=EntityType.choices,
        blank=True,
        db_index=True,
        help_text="Organization type in hierarchy: Group, Subsidiary, Facility, Department"
    )
    
    name = models.CharField(max_length=255)
    registered_name = models.CharField(
        max_length=500,
        blank=True,
        help_text="Official registered company name"
    )
    registration_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Company registration number"
    )
    company_size = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("small", "Small (1-50 employees)"),
            ("medium", "Medium (51-250 employees)"),
            ("large", "Large (251-1000 employees)"),
            ("enterprise", "Enterprise (1000+ employees)"),
        ],
        help_text="Organization size category"
    )
    logo = models.ImageField(
        upload_to="organization_logos/",
        blank=True,
        null=True,
        help_text="Organization logo"
    )
    sector = models.CharField(
        max_length=50,
        choices=[
            ("manufacturing", "Manufacturing"),
            ("oil_gas", "Oil & Gas"),
            ("finance", "Finance"),
        ],
    )
    country = CountryField(blank_label='(select country)', help_text="Organization's country")
    
    primary_reporting_focus = models.CharField(
        max_length=20,
        choices=PrimaryReportingFocus.choices,
        default=PrimaryReportingFocus.NIGERIA,
        help_text="Primary reporting focus: Nigeria only, International only, or Hybrid"
    )
    
    # Many-to-many relationship with frameworks
    regulatory_frameworks = models.ManyToManyField(
        "organizations.RegulatoryFramework",
        through="organizations.OrganizationFramework",
        related_name="organizations",
        help_text="Assigned regulatory frameworks"
    )
    
    # Config-driven: stores sector-specific settings, scopes, permits, etc.
    def _default_settings():
        return {"modules": {}, "sector_defaults": {}}

    settings = models.JSONField(
        default=_default_settings,
        blank=True,
        help_text="Sector-specific configuration (scopes, permits, frameworks)"
    )
    
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'organizations_organization'
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
        indexes = [
            models.Index(fields=['sector', 'is_active']),
            models.Index(fields=['primary_reporting_focus']),
            models.Index(fields=['parent']),
            models.Index(fields=['entity_type']),
            models.Index(fields=['parent', 'entity_type']),
        ]

    def __init__(self, *args, **kwargs):
        if 'organization_type' in kwargs and 'entity_type' not in kwargs:
            kwargs['entity_type'] = kwargs.pop('organization_type')
        super().__init__(*args, **kwargs)

    def __str__(self):
        """Return organization name with hierarchy context."""
        if self.parent:
            return f"{self.name} (child of {self.parent.name})"
        return self.name

    @property
    def organization_type(self):
        return self.entity_type

    @organization_type.setter
    def organization_type(self, value):
        self.entity_type = value

    @property
    def children(self):
        return self.subsidiaries

    @property
    def frameworks(self):
        return self.framework_assignments

    @property
    def organization_frameworks(self):
        return self.framework_assignments

    def get_organization_type_display(self):
        return self.get_entity_type_display()

    def _default_entity_type(self):
        return self.EntityType.SUBSIDIARY if self.parent_id else self.EntityType.GROUP

    def clean(self):
        from organizations.services.hierarchy_validation import validate_hierarchy

        if not self.entity_type:
            self.entity_type = self._default_entity_type()
        validate_hierarchy(self.parent, self.entity_type, instance=self)

    def save(self, *args, **kwargs):
        from organizations.services.hierarchy_validation import validate_hierarchy

        update_fields = kwargs.get('update_fields')
        if update_fields:
            normalized_fields = []
            for field_name in update_fields:
                normalized_fields.append('entity_type' if field_name == 'organization_type' else field_name)
            kwargs['update_fields'] = normalized_fields

        if not self.entity_type:
            self.entity_type = self._default_entity_type()
        validate_hierarchy(self.parent, self.entity_type, instance=self)
        return super().save(*args, **kwargs)

    def is_group(self):
        return self.entity_type == self.EntityType.GROUP

    def is_subsidiary(self):
        return self.entity_type == self.EntityType.SUBSIDIARY

    def get_children(self):
        return self.children.all()

    def get_subsidiaries(self):
        return self.children.filter(entity_type=self.EntityType.SUBSIDIARY)
    
    def get_ancestors(self):
        """Get all parent organizations up the hierarchy."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_descendants(self, include_self=False):
        """Get all child organizations (recursive)."""
        descendants = []
        if include_self:
            descendants.append(self)
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    @property
    def hierarchy_level(self):
        """Calculate depth in hierarchy (0 = root, 1 = child, etc.)."""
        return len(self.get_ancestors())
