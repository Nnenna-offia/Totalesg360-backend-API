from django.test import TestCase

from activities.models.activity_type import ActivityType
from activities.models.scope import Scope
from indicators.models.indicator import Indicator


class ActivityTypeModelTests(TestCase):
    def test_unit_autosync_from_indicator_on_save(self):
        scope = Scope.objects.create(name="Test Scope", code="test")
        indicator = Indicator.objects.create(
            code="TEST-1",
            name="Test Indicator",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            unit="kg",
        )

        # Provide a different unit manually — save() should override it
        activity = ActivityType.objects.create(
            name="Fuel Use",
            description="",
            unit="tonnes",
            scope=scope,
            is_active=True,
            indicator=indicator,
        )

        self.assertEqual(activity.unit, "kg")
