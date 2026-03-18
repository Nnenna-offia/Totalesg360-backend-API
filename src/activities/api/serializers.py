from rest_framework import serializers

from activities.models.activity_type import ActivityType
from activities.models.scope import Scope
from submissions.models.activity_submission import ActivitySubmission


class ScopeSerializer(serializers.ModelSerializer):
	class Meta:
		model = Scope
		fields = ['id', 'code', 'name', 'description', 'created_at', 'updated_at']
		read_only_fields = ['id', 'created_at', 'updated_at']


class ActivityTypeListSerializer(serializers.ModelSerializer):
	"""Serializer for listing activity types with nested relationships."""
	scope = ScopeSerializer(read_only=True)
	indicator = serializers.SerializerMethodField()
	
	class Meta:
		model = ActivityType
		fields = ['id', 'name', 'unit', 'scope', 'indicator', 'category', 'is_active', 'created_at', 'updated_at']
		read_only_fields = ['id', 'created_at', 'updated_at']
	
	def get_indicator(self, obj):
		if obj.indicator:
			return {
				'id': str(obj.indicator.id),
				'code': obj.indicator.code,
				'name': obj.indicator.name,
				'collection_method': obj.indicator.collection_method
			}
		return None


class ActivityTypeDetailSerializer(serializers.ModelSerializer):
	"""Detailed serializer with full nested data."""
	scope = ScopeSerializer(read_only=True)
	indicator = serializers.SerializerMethodField()
	submission_count = serializers.SerializerMethodField()
	
	class Meta:
		model = ActivityType
		fields = ['id', 'name', 'description', 'unit', 'scope', 'indicator', 'category', 
				  'is_active', 'submission_count', 'created_at', 'updated_at']
		read_only_fields = ['id', 'created_at', 'updated_at']
	
	def get_indicator(self, obj):
		if obj.indicator:
			return {
				'id': str(obj.indicator.id),
				'code': obj.indicator.code,
				'name': obj.indicator.name,
				'pillar': obj.indicator.pillar,
				'data_type': obj.indicator.data_type,
				'collection_method': obj.indicator.collection_method
			}
		return None
	
	def get_submission_count(self, obj):
		return obj.submissions.count()


class ActivityTypeCreateUpdateSerializer(serializers.ModelSerializer):
	"""Serializer for creating/updating activity types."""
	
	class Meta:
		model = ActivityType
		fields = ['name', 'description', 'unit', 'scope', 'indicator', 'category', 'is_active']
	
	def validate(self, attrs):
		# Ensure indicator is set to activity-based if linked
		indicator = attrs.get('indicator')
		if indicator and indicator.collection_method != 'activity':
			# Auto-update indicator to activity-based
			from indicators.models import Indicator
			indicator.collection_method = Indicator.CollectionMethod.ACTIVITY
			indicator.save()
		return attrs


class ActivityTypeSerializer(serializers.ModelSerializer):
	class Meta:
		model = ActivityType
		fields = ['id', 'name', 'unit', 'scope']


class ActivitySubmissionCreateSerializer(serializers.Serializer):
	activity_type_id = serializers.UUIDField()
	reporting_period_id = serializers.UUIDField()
	facility_id = serializers.UUIDField(required=False, allow_null=True)
	value = serializers.DecimalField(max_digits=18, decimal_places=6)
	unit = serializers.CharField(max_length=50)

	def validate(self, attrs):
		# Basic validations omitted; service will perform deeper checks
		return attrs


class ActivitySubmissionListSerializer(serializers.ModelSerializer):
	"""Serializer for listing activity submissions with nested data."""
	activity_type = ActivityTypeListSerializer(read_only=True)
	organization = serializers.SerializerMethodField()
	facility = serializers.SerializerMethodField()
	reporting_period = serializers.SerializerMethodField()
	created_by = serializers.SerializerMethodField()
	
	class Meta:
		model = ActivitySubmission
		fields = ['id', 'organization', 'facility', 'activity_type', 'reporting_period', 
				  'value', 'unit', 'created_by', 'created_at', 'updated_at']
		read_only_fields = ['id', 'organization', 'created_by', 'created_at', 'updated_at']
	
	def get_organization(self, obj):
		return {'id': str(obj.organization.id), 'name': obj.organization.name}
	
	def get_facility(self, obj):
		if obj.facility:
			return {'id': str(obj.facility.id), 'name': obj.facility.name}
		return None
	
	def get_reporting_period(self, obj):
		return {
			'id': str(obj.reporting_period.id),
			'year': obj.reporting_period.year,
			'quarter': obj.reporting_period.quarter,
			'status': obj.reporting_period.status
		}
	
	def get_created_by(self, obj):
		if obj.created_by:
			return {'id': str(obj.created_by.id), 'email': obj.created_by.email}
		return None


class ActivitySubmissionUpdateSerializer(serializers.ModelSerializer):
	"""Serializer for updating activity submissions."""
	
	class Meta:
		model = ActivitySubmission
		fields = ['value', 'unit']


class ActivitySubmissionSerializer(serializers.ModelSerializer):
	class Meta:
		model = ActivitySubmission
		fields = ['id', 'organization', 'facility', 'activity_type', 'reporting_period', 'value', 'unit', 'created_by', 'created_at']
		read_only_fields = ['id', 'organization', 'created_by', 'created_at']
