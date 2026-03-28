from rest_framework import serializers

from submissions.models import DataSubmission, ReportingPeriod
from indicators.models import Indicator
from indicators.selectors.queries import get_org_effective_indicators
from django.core.exceptions import ValidationError as DjangoValidationError


class SubmissionCreateSerializer(serializers.Serializer):
	indicator_id = serializers.UUIDField()
	reporting_period_id = serializers.UUIDField()
	facility_id = serializers.UUIDField(required=False, allow_null=True)
	value = serializers.JSONField(required=False)
	metadata = serializers.JSONField(required=False)

	def validate(self, attrs):
		# Basic shape validation: ensure `value` matches a JSON primitive type.
		val = attrs.get("value", None)
		if val is None:
			return attrs

		# primitive types allowed
		if isinstance(val, (int, float, bool, str)):
			pass
		else:
			raise serializers.ValidationError({"value": "Unsupported value type"})

		# indicator-specific validation if org context provided
		org = self.context.get("org") if hasattr(self, "context") else None
		indicator_id = attrs.get("indicator_id")
		if org and indicator_id:
			# ensure indicator exists and active for org
			try:
				# indicator_id may be UUID or string
				eff_qs = get_org_effective_indicators(org)
				ind = eff_qs.filter(id=indicator_id).first()
				if not ind or not getattr(ind, "is_active_effective", True):
					raise serializers.ValidationError({"indicator_id": "Indicator is not active for this organization"})
				# validate value type against indicator data_type
				dt = ind.data_type
				if dt in (Indicator.DataType.NUMBER, Indicator.DataType.PERCENT, Indicator.DataType.CURRENCY):
					try:
						float(val)
					except Exception:
						raise serializers.ValidationError({"value": "Value must be numeric for this indicator"})
				elif dt == Indicator.DataType.BOOLEAN:
					if not isinstance(val, bool):
						raise serializers.ValidationError({"value": "Value must be boolean for this indicator"})
				elif dt == Indicator.DataType.TEXT:
					if val is None:
						raise serializers.ValidationError({"value": "Value must be provided for text indicator"})
				else:
					# unknown data type
					raise serializers.ValidationError({"indicator_id": "Unsupported indicator data_type"})
			except DjangoValidationError as e:
				raise serializers.ValidationError({"detail": str(e)})

		return attrs


class DataSubmissionSerializer(serializers.ModelSerializer):
	class Meta:
		model = DataSubmission
		fields = [
			"id",
			"organization",
			"indicator",
			"reporting_period",
			"facility",
			"value_number",
			"value_text",
			"value_boolean",
			"metadata",
			"status",
			"submitted_by",
			"submitted_at",
			"approved_by",
			"approved_at",
		]
		read_only_fields = [
			"id",
			"organization",
			"status",
			"submitted_by",
			"submitted_at",
			"approved_by",
			"approved_at",
		]


class IndicatorSummarySerializer(serializers.Serializer):
	id = serializers.UUIDField(source="indicator.id")
	code = serializers.CharField(source="indicator.code")
	name = serializers.CharField(source="indicator.name")
	pillar = serializers.CharField(source="indicator.pillar")
	data_type = serializers.CharField(source="indicator.data_type")
	is_required_effective = serializers.BooleanField()
	is_active_effective = serializers.BooleanField()
	submission = DataSubmissionSerializer(allow_null=True)


class ReportingPeriodSerializer(serializers.ModelSerializer):
	class Meta:
		model = ReportingPeriod
		fields = [
			"id",
			"organization",
			"name",
			"period_type",
			"start_date",
			"end_date",
			"status",
			"opened_at",
			"locked_at",
			"is_active"
		]
		read_only_fields = ["id", "organization", "opened_at", "locked_at"]
	
	def validate(self, data):
		"""Validate that start_date is before end_date"""
		start_date = data.get('start_date')
		end_date = data.get('end_date')
		
		if start_date and end_date and start_date >= end_date:
			raise serializers.ValidationError("start_date must be before end_date")
		
		return data


class ReportingPeriodGenerationSerializer(serializers.Serializer):
	"""
	Serializer for generating reporting periods automatically.
	Accepts year and period_type, then auto-generates all periods.
	"""
	year = serializers.IntegerField(min_value=2000, max_value=2100)
	period_type = serializers.ChoiceField(
		choices=[
			'DAILY',
			'WEEKLY',
			'BI_WEEKLY',
			'MONTHLY',
			'QUARTERLY',
			'SEMI_ANNUAL',
			'ANNUAL'
		]
	)
	
	def validate_year(self, value):
		"""Ensure year is reasonable"""
		from datetime import datetime
		current_year = datetime.now().year
		if value < current_year - 10:
			raise serializers.ValidationError(f"Year must be {current_year - 10} or later")
		if value > current_year + 10:
			raise serializers.ValidationError(f"Year must be {current_year + 10} or earlier")
		return value

