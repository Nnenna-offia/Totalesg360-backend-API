from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0012_refactor_organization_entity_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrganizationESGSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enable_environmental", models.BooleanField(default=True)),
                ("enable_social", models.BooleanField(default=True)),
                ("enable_governance", models.BooleanField(default=True)),
                ("reporting_level", models.CharField(choices=[("group", "Group"), ("subsidiary", "Subsidiary"), ("facility", "Facility"), ("department", "Department")], default="subsidiary", max_length=20)),
                ("reporting_frequency", models.CharField(choices=[("DAILY", "Daily"), ("WEEKLY", "Weekly"), ("BI_WEEKLY", "Bi-Weekly"), ("MONTHLY", "Monthly"), ("QUARTERLY", "Quarterly"), ("SEMI_ANNUAL", "Semi-Annual"), ("ANNUAL", "Annual"), ("CUSTOM", "Custom")], default="MONTHLY", max_length=20)),
                ("fiscal_year_start_month", models.IntegerField(default=1)),
                ("sector_defaults", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("organization", models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="esg_settings", to="organizations.organization")),
            ],
            options={
                "db_table": "organizations_esg_settings",
                "verbose_name": "Organization ESG Settings",
                "verbose_name_plural": "Organization ESG Settings",
            },
        ),
    ]