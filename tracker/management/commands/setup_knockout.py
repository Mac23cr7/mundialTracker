import json
import re
from django.core.management.base import BaseCommand
from django.utils import timezone
from tracker.models import GroupTeam, KnockoutMatch
from tracker.utils import normalize_name

class Command(BaseCommand):
    help = 'Configura los enfrentamientos de Dieciseisavos de Final de la Copa Mundial 2026 usando un archivo JSON o el JSON por defecto.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json-data',
            type=str,
            help='Datos JSON en texto directo o ruta a un archivo JSON.',
        )

    def handle(self, *args, **options):
        # Default data provided by user
        default_data = {
            "fase": "Dieciseisavos de Final (Primera ronda de eliminación directa)",
            "torneo": "Mundial FIFA 2026",
            "partidos": [
                { "encuentro": "Sudáfrica vs Canadá", "fecha": "28 de junio" },
                { "encuentro": "Brasil vs Japón", "fecha": "29 de junio" },
                { "encuentro": "Alemania vs Paraguay", "fecha": "29 de junio" },
                { "encuentro": "Países Bajos vs Marruecos", "fecha": "29 de junio" },
                { "encuentro": "Costa de Marfil vs Noruega", "fecha": "30 de junio" },
                { "encuentro": "Francia vs Suecia", "fecha": "30 de junio" },
                { "encuentro": "México vs Ecuador", "fecha": "30 de junio" },
                { "encuentro": "Inglaterra vs RD Congo", "fecha": "1 de julio" },
                { "encuentro": "Bélgica vs Senegal", "fecha": "1 de julio" },
                { "encuentro": "Estados Unidos vs Bosnia y Herzegovina", "fecha": "1 de julio" },
                { "encuentro": "España vs Austria", "fecha": "2 de julio" },
                { "encuentro": "Portugal vs Croacia", "fecha": "2 de julio" },
                { "encuentro": "Suiza vs Argelia", "fecha": "2 de julio" },
                { "encuentro": "Australia vs Egipto", "fecha": "3 de julio" },
                { "encuentro": "Argentina vs Cabo Verde", "fecha": "3 de julio" },
                { "encuentro": "Colombia vs Ghana", "fecha": "3 de julio" }
            ]
        }

        json_arg = options['json_data']
        if json_arg:
            try:
                # Check if it looks like JSON or a file path
                if json_arg.strip().startswith('{') or json_arg.strip().startswith('['):
                    data = json.loads(json_arg)
                else:
                    with open(json_arg, 'r', encoding='utf-8') as f:
                        data = json.load(f)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error al procesar JSON: {e}"))
                return
        else:
            data = default_data

        partidos = data.get("partidos", [])
        if not partidos:
            self.stderr.write(self.style.ERROR("No se encontraron partidos en el JSON."))
            return

        self.stdout.write(self.style.WARNING("Eliminando partidos de eliminación directa existentes..."))
        KnockoutMatch.objects.all().delete()

        # Helper mapping for specific team names
        TEAM_MAPPING = {
            "rd congo": "RD del Congo",
            "republica democratica del congo": "RD del Congo",
        }

        def find_team(name):
            cleaned_name = name.strip()
            # Apply mapping if exists
            if cleaned_name.lower() in TEAM_MAPPING:
                cleaned_name = TEAM_MAPPING[cleaned_name.lower()]

            # Try exact match
            try:
                return GroupTeam.objects.get(name=cleaned_name)
            except GroupTeam.DoesNotExist:
                pass

            # Try case-insensitive match
            try:
                return GroupTeam.objects.get(name__iexact=cleaned_name)
            except GroupTeam.DoesNotExist:
                pass

            # Try normalized name match
            target_norm = normalize_name(cleaned_name)
            for team in GroupTeam.objects.all():
                if normalize_name(team.name) == target_norm:
                    return team

            raise ValueError(f"Equipo no encontrado en la base de datos: '{name}'")

        DATE_MAPPING = {
            "28 de junio": "2026-06-28",
            "29 de junio": "2026-06-29",
            "30 de junio": "2026-06-30",
            "1 de julio": "2026-07-01",
            "2 de julio": "2026-07-02",
            "3 de julio": "2026-07-03",
        }

        def parse_date(date_str):
            if date_str in DATE_MAPPING:
                return DATE_MAPPING[date_str]
            # Try to parse "X de [mes]"
            months = {
                "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
                "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
            }
            try:
                parts = date_str.lower().split(" de ")
                if len(parts) == 2:
                    day = int(parts[0])
                    month_name = parts[1].strip()
                    month = months.get(month_name, 6)
                    return f"2026-{month:02d}-{day:02d}"
            except Exception:
                pass
            return "2026-06-28"

        created_count = 0
        for idx, p in enumerate(partidos):
            encuentro = p.get("encuentro", "")
            fecha_str = p.get("fecha", "")

            # Split by "vs" case-insensitive
            teams = re.split(r'\s+[vV][sS]\s+', encuentro)
            if len(teams) != 2:
                self.stderr.write(self.style.ERROR(f"Formato de encuentro inválido: '{encuentro}'"))
                return

            try:
                home_team = find_team(teams[0])
                away_team = find_team(teams[1])
            except ValueError as e:
                self.stderr.write(self.style.ERROR(str(e)))
                return

            match_date = parse_date(fecha_str)

            KnockoutMatch.objects.create(
                round='R32',
                match_number=idx + 1,
                home_team=home_team,
                away_team=away_team,
                played=False,
                date=match_date
            )
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"Partido {idx+1} creado: {home_team.name} vs {away_team.name} ({match_date})"))

        # Create placeholder matches for future rounds
        self.stdout.write(self.style.WARNING("Creando partidos de marcador en blanco para las rondas futuras..."))
        for m_num in range(1, 9):
            KnockoutMatch.objects.create(round='R16', match_number=m_num, played=False)
        for m_num in range(1, 5):
            KnockoutMatch.objects.create(round='QF', match_number=m_num, played=False)
        for m_num in range(1, 3):
            KnockoutMatch.objects.create(round='SF', match_number=m_num, played=False)
        KnockoutMatch.objects.create(round='F', match_number=1, played=False)

        self.stdout.write(self.style.SUCCESS(f"¡Fase de eliminación directa armada con {created_count} enfrentamientos iniciales exitosamente!"))
