from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'project-nodes', views.ProjectNodeViewSet, basename='projectnode')
router.register(r'connections', views.ConnectionViewSet, basename='connection')
router.register(r'queries', views.QueryViewSet, basename='query')
router.register(r'parameters', views.ParameterViewSet, basename='parameter')

urlpatterns = [
    path('', include(router.urls)),
    
    # Custom endpoints (a serem implementados)
    path('test-connection/', views.TestConnectionView.as_view(), name='test_connection'),
    path('execute-query/', views.ExecuteQueryView.as_view(), name='execute_query'),
    path('health/', views.HealthCheckView.as_view(), name='health_check'),
]
