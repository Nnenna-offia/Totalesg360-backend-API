from django.urls import path
from . import views

urlpatterns = [
    path('goals', views.GoalListView.as_view(), name='targets-goals-list'),
    path('goals/<uuid:goal_id>', views.GoalDetailView.as_view(), name='targets-goal-detail'),
    path('milestones', views.MilestoneListView.as_view(), name='targets-milestones-list'),
    path('progress/<uuid:goal_id>', views.ProgressView.as_view(), name='targets-progress'),
]
