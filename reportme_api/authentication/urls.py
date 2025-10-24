from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # JWT Authentication endpoints (customizados)
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User management endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Password reset endpoints
    path('password-reset-request/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    
    # Admin endpoints
    path('users/', views.UserListView.as_view(), name='user_list'),
    
    # Permission endpoints
    path('permissions/', views.UserPermissionsView.as_view(), name='user_permissions'),
    path('test-permission/', views.TestPermissionView.as_view(), name='test_permission'),
]
