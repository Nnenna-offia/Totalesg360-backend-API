from rest_framework import serializers


class TargetGoalCreateSerializer(serializers.Serializer):
    indicator_id = serializers.UUIDField(required=True)
    facility_id = serializers.UUIDField(required=False, allow_null=True)
    department_id = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    reporting_frequency = serializers.ChoiceField(
        choices=[
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('BI_WEEKLY', 'Bi-Weekly'),
            ('MONTHLY', 'Monthly'),
            ('QUARTERLY', 'Quarterly'),
            ('SEMI_ANNUAL', 'Semi-Annual'),
            ('ANNUAL', 'Annual'),
        ],
        required=True,
        help_text="Reporting frequency for this target"
    )
    baseline_year = serializers.IntegerField()
    baseline_value = serializers.FloatField()
    target_year = serializers.IntegerField()
    target_value = serializers.FloatField()
    direction = serializers.ChoiceField(choices=[('increase', 'Increase'), ('decrease', 'Decrease')], default='decrease')


class TargetGoalPatchSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    reporting_frequency = serializers.ChoiceField(
        choices=[
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('BI_WEEKLY', 'Bi-Weekly'),
            ('MONTHLY', 'Monthly'),
            ('QUARTERLY', 'Quarterly'),
            ('SEMI_ANNUAL', 'Semi-Annual'),
            ('ANNUAL', 'Annual'),
        ],
        required=False
    )
    baseline_year = serializers.IntegerField(required=False)
    baseline_value = serializers.FloatField(required=False)
    target_year = serializers.IntegerField(required=False)
    target_value = serializers.FloatField(required=False)
    direction = serializers.ChoiceField(choices=[('increase', 'Increase'), ('decrease', 'Decrease')], required=False)
    status = serializers.ChoiceField(choices=[('active','Active'),('completed','Completed'),('archived','Archived')], required=False)


class MilestoneCreateSerializer(serializers.Serializer):
    goal_id = serializers.UUIDField(required=True)
    year = serializers.IntegerField(required=True)
    target_value = serializers.FloatField(required=True)
