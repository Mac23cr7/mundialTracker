from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from collections import Counter
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Match, Group, GroupTeam, GroupMatch, KnockoutMatch
from .forms import MatchForm, GroupForm, GroupTeamForm, GroupMatchForm
from .utils import get_flag_emoji

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, "Acceso denegado. Se requieren privilegios de administrador.")
            return redirect('mundial_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def dashboard(request):
    # Procesar formulario de creación si es POST
    if request.method == 'POST':
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, "Acceso denegado. Se requieren privilegios de administrador.")
            return redirect('dashboard')
        form = MatchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Partido registrado exitosamente!")
            return redirect('dashboard')
        else:
            messages.error(request, "Error al registrar el partido. Por favor revisa los datos.")
    else:
        form = MatchForm()

    # Obtener parámetros de filtrado y búsqueda
    sport_filter = request.GET.get('sport', 'ALL')
    search_query = request.GET.get('search', '').strip()

    matches = Match.objects.all()

    # Aplicar filtros
    if sport_filter in ['FB', 'BK']:
        matches = matches.filter(sport=sport_filter)
    
    if search_query:
        matches = matches.filter(
            Q(home_team__icontains=search_query) | 
            Q(away_team__icontains=search_query)
        )

    # Calcular estadísticas rápidas
    total_matches = Match.objects.count()
    football_count = Match.objects.filter(sport='FB').count()
    basketball_count = Match.objects.filter(sport='BK').count()

    # Determinar el equipo más activo
    all_team_names = []
    for m in Match.objects.all():
        all_team_names.append(m.home_team.strip())
        all_team_names.append(m.away_team.strip())
    
    most_active_team = "Ninguno"
    most_active_count = 0
    if all_team_names:
        counter = Counter(all_team_names)
        most_active_team, most_active_count = counter.most_common(1)[0]

    context = {
        'form': form,
        'matches': matches,
        'total_matches': total_matches,
        'football_count': football_count,
        'basketball_count': basketball_count,
        'most_active_team': most_active_team,
        'most_active_count': most_active_count,
        'sport_filter': sport_filter,
        'search_query': search_query,
    }
    return render(request, 'tracker/dashboard.html', context)

@admin_required
def delete_match(request, match_id):
    # Eliminar partido por ID (se permite POST por seguridad, pero también GET para facilidad de uso rápido)
    match = get_object_or_404(Match, id=match_id)
    if request.method == 'POST' or request.GET.get('confirm') == 'yes':
        match.delete()
        messages.success(request, "El partido fue eliminado correctamente.")
    else:
        messages.warning(request, "Acción de eliminación cancelada o inválida.")
    return redirect('dashboard')

def team_detail(request, team_name):
    team_name_clean = team_name.strip()
    
    # Obtener partidos donde el equipo participó
    matches = Match.objects.filter(
        Q(home_team__iexact=team_name_clean) | 
        Q(away_team__iexact=team_name_clean)
    ).order_by('-date', '-created_at')

    # Si no hay partidos para este equipo, redirigir al dashboard con advertencia
    if not matches.exists():
        messages.error(request, f"No se encontraron partidos para el equipo '{team_name_clean}'.")
        return redirect('dashboard')

    # Calcular estadísticas
    total_played = matches.count()
    wins = 0
    draws = 0
    losses = 0

    home_played = 0
    home_wins = 0
    home_draws = 0
    home_losses = 0

    away_played = 0
    away_wins = 0
    away_draws = 0
    away_losses = 0

    for m in matches:
        is_home = m.home_team.lower() == team_name_clean.lower()
        
        if is_home:
            home_played += 1
            if m.home_score > m.away_score:
                home_wins += 1
                wins += 1
            elif m.home_score < m.away_score:
                home_losses += 1
                losses += 1
            else:
                home_draws += 1
                draws += 1
        else:
            away_played += 1
            if m.away_score > m.home_score:
                away_wins += 1
                wins += 1
            elif m.away_score < m.home_score:
                away_losses += 1
                losses += 1
            else:
                away_draws += 1
                draws += 1

    win_rate = round((wins / total_played) * 100, 1) if total_played > 0 else 0

    context = {
        'team_name': team_name_clean,
        'matches': matches,
        'total_played': total_played,
        'wins': wins,
        'draws': draws,
        'losses': losses,
        'home_played': home_played,
        'home_wins': home_wins,
        'home_draws': home_draws,
        'home_losses': home_losses,
        'away_played': away_played,
        'away_wins': away_wins,
        'away_draws': away_draws,
        'away_losses': away_losses,
        'win_rate': win_rate,
    }
    return render(request, 'tracker/team_detail.html', context)


def generate_knockout_bracket(direct_qualifiers, qualified_thirds):
    winners = direct_qualifiers[::2]
    runners_up = direct_qualifiers[1::2]
    thirds_list = list(qualified_thirds)
    
    if len(winners) < 12 or len(runners_up) < 12 or len(thirds_list) < 8:
        return
        
    for i in range(8):
        winner = winners[i]
        third = thirds_list[i]
        if winner.group == third.group:
            for j in range(i + 1, 8):
                if thirds_list[j].group != winner.group and thirds_list[i].group != winners[j].group:
                    thirds_list[i], thirds_list[j] = thirds_list[j], thirds_list[i]
                    break

    pairings = [
        (winners[0], thirds_list[0]),
        (winners[1], thirds_list[1]),
        (winners[2], thirds_list[2]),
        (winners[3], thirds_list[3]),
        (winners[4], thirds_list[4]),
        (winners[5], thirds_list[5]),
        (winners[6], thirds_list[6]),
        (winners[7], thirds_list[7]),
        (winners[8], runners_up[9]),
        (winners[9], runners_up[8]),
        (winners[10], runners_up[11]),
        (winners[11], runners_up[10]),
        (runners_up[0], runners_up[1]),
        (runners_up[2], runners_up[3]),
        (runners_up[4], runners_up[5]),
        (runners_up[6], runners_up[7]),
    ]

    for idx, (home, away) in enumerate(pairings):
        KnockoutMatch.objects.create(
            round='R32',
            match_number=idx + 1,
            home_team=home,
            away_team=away,
            played=False
        )

    for m_num in range(1, 9):
        KnockoutMatch.objects.create(round='R16', match_number=m_num, played=False)
    for m_num in range(1, 5):
        KnockoutMatch.objects.create(round='QF', match_number=m_num, played=False)
    for m_num in range(1, 3):
        KnockoutMatch.objects.create(round='SF', match_number=m_num, played=False)
    KnockoutMatch.objects.create(round='TP', match_number=1, played=False)
    KnockoutMatch.objects.create(round='F', match_number=1, played=False)


def mundial_dashboard(request):
    groups = Group.objects.all()
    
    # Check if all registered matches have been played
    total_matches = GroupMatch.objects.count()
    played_matches = GroupMatch.objects.filter(played=True).count()
    unplayed_matches = GroupMatch.objects.filter(played=False).count()
    show_qualifiers = total_matches > 0 and unplayed_matches == 0
    
    groups_data = []
    direct_qualifiers = []
    third_placed_teams = []
    
    for g in groups:
        sorted_teams = sorted(
            g.teams.all(),
            key=lambda t: (-t.points, -t.goal_difference, -t.goals_for, t.name)
        )
        groups_data.append({
            'group': g,
            'teams': sorted_teams,
            'matches': g.matches.all()
        })
        
        # Collect direct qualifiers (1st and 2nd)
        if len(sorted_teams) >= 1:
            direct_qualifiers.append(sorted_teams[0])
        if len(sorted_teams) >= 2:
            direct_qualifiers.append(sorted_teams[1])
        # Collect 3rd placed team
        if len(sorted_teams) >= 3:
            third_placed_teams.append(sorted_teams[2])

    # Sort third-placed teams across all groups:
    # 1. Pts desc, 2. DG desc, 3. GF desc, 4. Name asc
    sorted_thirds = sorted(
        third_placed_teams,
        key=lambda t: (-t.points, -t.goal_difference, -t.goals_for, t.name)
    )
    
    # Identify which of these 3rd placed teams qualify (top 8)
    qualified_thirds = sorted_thirds[:8]
    qualified_thirds_ids = [t.id for t in qualified_thirds]
    
    # Set a flag on each third placed team for easier rendering
    for t in sorted_thirds:
        t.is_qualified_third = t.id in qualified_thirds_ids
    
    # Combined qualified list
    qualified_all = direct_qualifiers + qualified_thirds
    # Sort them by group name then points/name to display them nicely
    qualified_all_sorted = sorted(qualified_all, key=lambda t: (t.group.name, -t.points, t.name))

    # Gen / Update bracket
    if show_qualifiers:
        has_ko = KnockoutMatch.objects.exists()
        if not has_ko:
            generate_knockout_bracket(direct_qualifiers, qualified_thirds)
        else:
            # Recreate if none played and teams changed
            ko_played = KnockoutMatch.objects.filter(played=True).exists()
            if not ko_played:
                r32_matches = KnockoutMatch.objects.filter(round='R32')
                existing_teams = set()
                for m in r32_matches:
                    if m.home_team: existing_teams.add(m.home_team.id)
                    if m.away_team: existing_teams.add(m.away_team.id)
                new_teams = set(t.id for t in qualified_all)
                if existing_teams != new_teams:
                    KnockoutMatch.objects.all().delete()
                    generate_knockout_bracket(direct_qualifiers, qualified_thirds)

    ko_matches = KnockoutMatch.objects.all()
    played_ko_count = ko_matches.filter(played=True).count()
    r32_matches = ko_matches.filter(round='R32')
    r16_matches = ko_matches.filter(round='R16')
    qf_matches = ko_matches.filter(round='QF')
    sf_matches = ko_matches.filter(round='SF')
    tp_match = ko_matches.filter(round='TP').first()
    final_match = ko_matches.filter(round='F').first()
    
    champion = None
    if final_match and final_match.played:
        champion = final_match.winner

    context = {
        'groups_data': groups_data,
        'groups': groups,
        'mejores_terceros': sorted_thirds if show_qualifiers else [],
        'qualified_thirds_ids': qualified_thirds_ids if show_qualifiers else [],
        'clasificados_32': qualified_all_sorted if show_qualifiers else [],
        'show_qualifiers': show_qualifiers,
        'total_matches': total_matches,
        'played_matches': played_matches,
        'played_ko_count': played_ko_count,
        'r32_matches': r32_matches,
        'r16_matches': r16_matches,
        'qf_matches': qf_matches,
        'sf_matches': sf_matches,
        'tp_match': tp_match,
        'final_match': final_match,
        'champion': champion,
        'group_form': GroupForm(),
        'team_form': GroupTeamForm(),
        'match_form': GroupMatchForm(),
    }
    return render(request, 'tracker/mundial.html', context)


@admin_required
def add_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Grupo creado exitosamente!")
        else:
            messages.error(request, "Error al crear el grupo. Es posible que el nombre ya exista.")
    return redirect('mundial_dashboard')


@admin_required
def add_group_team(request):
    if request.method == 'POST':
        form = GroupTeamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Equipo agregado al grupo exitosamente!")
        else:
            messages.error(request, "Error al agregar el equipo. Revisa que el nombre sea único en ese grupo.")
    return redirect('mundial_dashboard')


@admin_required
def add_group_match(request):
    if request.method == 'POST':
        form = GroupMatchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Partido de grupo registrado exitosamente!")
        else:
            errors = form.non_field_errors() or form.errors.get('__all__')
            msg = f"Error al registrar el partido. {errors[0]}" if errors else "Error al registrar el partido. Revisa los datos."
            messages.error(request, msg)
    return redirect('mundial_dashboard')


@admin_required
def delete_group_match(request, match_id):
    match = get_object_or_404(GroupMatch, id=match_id)
    match.delete()
    messages.success(request, "Partido de grupo eliminado correctamente y tabla actualizada.")
    return redirect('mundial_dashboard')


@admin_required
def populate_worldcup(request):
    # Reset
    KnockoutMatch.objects.all().delete()
    GroupMatch.objects.all().delete()
    GroupTeam.objects.all().delete()
    Group.objects.all().delete()
    
    # Create test users
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
    
    # 12 Groups with 4 teams each (48 teams total)
    groups_data = {
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

    for g_name, team_list in groups_data.items():
        g = Group.objects.create(name=g_name)
        for name in team_list:
            flag = get_flag_emoji(name)
            GroupTeam.objects.create(group=g, name=name, flag=flag)

    messages.success(request, "¡12 Grupos del Mundial inicializados exitosamente y credenciales de prueba creadas (admin/admin123 y viewer/viewer123)!")
    return redirect('mundial_dashboard')


@admin_required
def edit_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Grupo actualizado exitosamente!")
        else:
            messages.error(request, "Error al actualizar el grupo. Es posible que el nombre ya exista.")
    return redirect('mundial_dashboard')


@admin_required
def delete_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group.delete()
    messages.success(request, f"El grupo '{group.name}' fue eliminado correctamente.")
    return redirect('mundial_dashboard')


@admin_required
def update_group_match_score(request, match_id):
    match = get_object_or_404(GroupMatch, id=match_id)
    if request.method == 'POST':
        home_score = request.POST.get('home_score')
        away_score = request.POST.get('away_score')
        try:
            match.home_score = int(home_score)
            match.away_score = int(away_score)
            match.played = True
            match.save()
            messages.success(request, f"¡Resultado de {match.home_team.name} vs {match.away_team.name} actualizado exitosamente!")
        except (ValueError, TypeError):
            messages.error(request, "Error al actualizar el resultado. Los goles deben ser enteros no negativos.")
    return redirect('mundial_dashboard')


def logout_view(request):
    logout(request)
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('mundial_dashboard')


@admin_required
def update_knockout_match_score(request, match_id):
    match = get_object_or_404(KnockoutMatch, id=match_id)
    if request.method == 'POST':
        home_score = request.POST.get('home_score')
        away_score = request.POST.get('away_score')
        home_penalties = request.POST.get('home_penalties')
        away_penalties = request.POST.get('away_penalties')
        
        try:
            match.home_score = int(home_score)
            match.away_score = int(away_score)
            
            if match.home_score == match.away_score:
                if home_penalties and away_penalties:
                    match.home_penalties = int(home_penalties)
                    match.away_penalties = int(away_penalties)
                else:
                    messages.error(request, "Se requieren los goles de penaltis en caso de empate.")
                    return redirect('mundial_dashboard')
            else:
                match.home_penalties = None
                match.away_penalties = None
                
            match.played = True
            match.save()
            messages.success(request, f"Marcador de {match} guardado exitosamente.")
        except (ValueError, TypeError, ValidationError) as e:
            messages.error(request, f"Error al actualizar marcador: {e}")
    return redirect('mundial_dashboard')


@admin_required
def reset_knockout_match(request, match_id):
    match = get_object_or_404(KnockoutMatch, id=match_id)
    match.played = False
    match.home_score = 0
    match.away_score = 0
    match.home_penalties = None
    match.away_penalties = None
    match.winner = None
    match.save()
    messages.success(request, f"Marcador eliminado.")
    return redirect('mundial_dashboard')


@admin_required
def reset_knockout_bracket(request):
    KnockoutMatch.objects.all().delete()
    messages.success(request, "Bracket de eliminación directa reseteado.")
    return redirect('mundial_dashboard')
