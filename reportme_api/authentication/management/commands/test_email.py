from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Testa o envio de email do sistema'

    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, help='Email de destino para teste')

    def handle(self, *args, **options):
        to_email = options.get('to')
        
        if not to_email:
            self.stdout.write(
                self.style.ERROR('Por favor, forneça um email de destino usando --to email@exemplo.com')
            )
            return

        try:
            subject = 'Teste de Email - ReportMe'
            message = '''
Este é um email de teste do sistema ReportMe.

Se você recebeu este email, significa que a configuração de email está funcionando corretamente.

Atenciosamente,
Sistema ReportMe
            '''

            # Tentar enviar o email
            self.stdout.write('Enviando email de teste...')
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )

            self.stdout.write(
                self.style.SUCCESS(f'Email de teste enviado com sucesso para: {to_email}')
            )
            
            # Mostrar configurações atuais
            self.stdout.write('\n--- Configurações de Email Atuais ---')
            self.stdout.write(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
            
            if hasattr(settings, 'EMAIL_HOST'):
                self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
                self.stdout.write(f'EMAIL_PORT: {settings.EMAIL_PORT}')
                self.stdout.write(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
                self.stdout.write(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
                
            self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao enviar email: {str(e)}')
            )
            
            # Mostrar algumas dicas de troubleshooting
            self.stdout.write('\n--- Dicas de Troubleshooting ---')
            self.stdout.write('1. Verifique se as configurações de email estão corretas no settings.py')
            self.stdout.write('2. Se usando Gmail, certifique-se de usar uma "Senha de App" em vez da senha normal')
            self.stdout.write('3. Verifique se o EMAIL_HOST e EMAIL_PORT estão corretos para seu provedor')
            self.stdout.write('4. Para desenvolvimento, considere usar EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"')