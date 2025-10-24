"""
Script para executar testes do ReportMe com configurações específicas
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reportme.test_settings')
    django.setup()
    
    # Configurar runner de testes
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Executar testes
    failures = test_runner.run_tests([
        "tests.test_authentication",
        "tests.test_projects", 
        "tests.test_connections",
        "tests.test_queries",
        "tests.test_integration"
    ])
    
    if failures:
        sys.exit(1)