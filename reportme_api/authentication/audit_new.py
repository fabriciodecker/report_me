from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
import json
from .models import AuditLog

User = get_user_model()


def log_user_action(user, action, details="", obj=None, ip_address=None, user_agent="", changes=None):
    """
    Registra uma ação do usuário no log de auditoria
    """
    if changes is None:
        changes = {}
    
    content_type = None
    object_id = None
    object_repr = details
    
    if obj:
        content_type = ContentType.objects.get_for_model(obj)
        object_id = obj.pk
        object_repr = str(obj)
    
    audit_log = AuditLog.objects.create(
        user=user,
        action=action,
        content_type=content_type,
        object_id=object_id,
        object_repr=object_repr,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )
    
    return audit_log


def get_user_activity(user, action=None, days=30):
    """
    Retorna as atividades recentes de um usuário
    """
    from datetime import datetime, timedelta
    
    queryset = AuditLog.objects.filter(
        user=user,
        timestamp__gte=datetime.now() - timedelta(days=days)
    )
    
    if action:
        queryset = queryset.filter(action=action)
    
    return queryset.order_by('-timestamp')


def get_object_history(obj, days=30):
    """
    Retorna o histórico de mudanças de um objeto
    """
    from datetime import datetime, timedelta
    
    content_type = ContentType.objects.get_for_model(obj)
    
    return AuditLog.objects.filter(
        content_type=content_type,
        object_id=obj.pk,
        timestamp__gte=datetime.now() - timedelta(days=days)
    ).order_by('-timestamp')


def get_system_activity(action=None, days=7):
    """
    Retorna atividades recentes do sistema
    """
    from datetime import datetime, timedelta
    
    queryset = AuditLog.objects.filter(
        timestamp__gte=datetime.now() - timedelta(days=days)
    )
    
    if action:
        queryset = queryset.filter(action=action)
    
    return queryset.order_by('-timestamp')


def audit_login(user, request):
    """
    Registra login do usuário
    """
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    return log_user_action(
        user=user,
        action='login',
        details=f"Login realizado de {ip_address}",
        ip_address=ip_address,
        user_agent=user_agent
    )


def audit_logout(user, request):
    """
    Registra logout do usuário
    """
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    return log_user_action(
        user=user,
        action='logout',
        details=f"Logout realizado de {ip_address}",
        ip_address=ip_address,
        user_agent=user_agent
    )


def get_client_ip(request):
    """
    Extrai o IP do cliente da requisição
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
