import json
import sys
from django.core.management.base import BaseCommand
from tracker.models import Group, GroupTeam, GroupMatch
from tracker.utils import get_flag_emoji

class Command(BaseCommand):
    help = 'Carga los grupos y equipos del Mundial desde un archivo JSON o usa los datos por defecto de la Copa Mundial 2026.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Ruta opcional a un archivo JSON con los datos de los grupos.',
        )

    def handle(self, *args, **options):
        # Clear existing data first
        from tracker.models import KnockoutMatch
        KnockoutMatch.objects.all().delete()
        GroupMatch.objects.all().delete()
        GroupTeam.objects.all().delete()
        Group.objects.all().delete()
        
        # Create test users
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        else:
            u = User.objects.get(username='admin')
            u.is_staff = True
            u.is_superuser = True
            u.save()

        if not User.objects.filter(username='viewer').exists():
            User.objects.create_user('viewer', 'viewer@example.com', 'viewer123')
        else:
            u = User.objects.get(username='viewer')
            u.is_staff = False
            u.is_superuser = False
            u.save()
        
        file_path = options['file']
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error al leer el archivo JSON: {e}"))
                return
        else:
            data = {
                "torneo": "Copa Mundial de la FIFA 2026",
                "grupos": {
                    "Grupo A": ["México", "Sudáfrica", "Corea del Sur", "República Checa"],
                    "Grupo B": ["Canadá", "Bosnia y Herzegovina", "Catar", "Suiza"],
                    "Grupo C": ["Brasil", "Marruecos", "Haití", "Escocia"],
                    "Grupo D": ["Estados Unidos", "Paraguay", "Australia", "Turquía"],
                    "Grupo E": ["Alemania", "Curazao", "Costa de Marfil", "Ecuador"],
                    "Grupo F": ["Países Bajos", "Japón", "Suecia", "Túnez"],
                    "Grupo G": ["Bélgica", "Egipto", "Irán", "Nueva Zelanda"],
                    "Grupo H": ["España", "Cabo Verde", "Arabia Saudita", "Uruguay"],
                    "Grupo I": ["Francia", "Senegal", "Irak", "Noruega"],
                    "Grupo J": ["Argentina", "Argelia", "Austria", "Jordania"],
                    "Grupo K": ["Portugal", "RD del Congo", "Uzbekistán", "Colombia"],
                    "Grupo L": ["Inglaterra", "Croacia", "Ghana", "Panamá"]
                }
            }

        grupos = data.get("grupos", {})
        for g_name, team_list in grupos.items():
            g = Group.objects.create(name=g_name)
            for name in team_list:
                flag = get_flag_emoji(name)
                GroupTeam.objects.create(group=g, name=name, flag=flag)
            
            # Safe print to avoid UnicodeEncodeError on Windows CP1252 consoles
            msg = f"Grupo '{g_name}' cargado con {len(team_list)} equipos."
            try:
                self.stdout.write(self.style.SUCCESS(msg))
            except UnicodeEncodeError:
                self.stdout.write(self.style.SUCCESS(msg.encode('ascii', 'replace').decode('ascii')))

        success_msg = "¡Carga del Mundial completada exitosamente!"
        try:
            self.stdout.write(self.style.SUCCESS(success_msg))
        except UnicodeEncodeError:
            self.stdout.write(self.style.SUCCESS(success_msg.encode('ascii', 'replace').decode('ascii')))
