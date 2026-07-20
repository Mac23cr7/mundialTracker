from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Match(models.Model):
    SPORT_CHOICES = [
        ('FB', 'Fútbol'),
        ('BK', 'Básquet'),
    ]

    sport = models.CharField(
        max_length=2,
        choices=SPORT_CHOICES,
        default='FB',
        verbose_name="Deporte"
    )
    home_team = models.CharField(
        max_length=100,
        verbose_name="Equipo Local"
    )
    away_team = models.CharField(
        max_length=100,
        verbose_name="Equipo Visitante"
    )
    home_score = models.PositiveIntegerField(
        default=0,
        verbose_name="Resultado Local"
    )
    away_score = models.PositiveIntegerField(
        default=0,
        verbose_name="Resultado Visitante"
    )
    date = models.DateField(
        verbose_name="Fecha del Partido"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro"
    )

    class Meta:
        verbose_name = "Partido"
        verbose_name_plural = "Partidos"
        ordering = ['-date', '-created_at']

    def clean(self):
        super().clean()
        # Validar que los equipos no sean el mismo
        if self.home_team and self.away_team:
            if self.home_team.strip().lower() == self.away_team.strip().lower():
                raise ValidationError({
                    'away_team': "El equipo visitante no puede ser el mismo que el equipo local."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_sport_display()}: {self.home_team} {self.home_score} - {self.away_score} {self.away_team} ({self.date})"


class Group(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre del Grupo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"
        ordering = ['name']

    def __str__(self):
        return self.name

    def update_standings(self):
        # Reset stats
        teams = self.teams.all()
        for t in teams:
            t.games_played = 0
            t.wins = 0
            t.draws = 0
            t.losses = 0
            t.goals_for = 0
            t.goals_against = 0
            t.points = 0
            t.save()
        
        # Calculate
        matches = self.matches.filter(played=True)
        for m in matches:
            home = m.home_team
            away = m.away_team
            
            home.games_played += 1
            away.games_played += 1
            
            home.goals_for += m.home_score
            home.goals_against += m.away_score
            
            away.goals_for += m.away_score
            away.goals_against += m.home_score
            
            if m.home_score > m.away_score:
                home.wins += 1
                home.points += 3
                away.losses += 1
            elif m.home_score < m.away_score:
                away.wins += 1
                away.points += 3
                home.losses += 1
            else:
                home.draws += 1
                home.points += 1
                away.draws += 1
                away.points += 1
                
            home.save()
            away.save()


class GroupTeam(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='teams', verbose_name="Grupo")
    name = models.CharField(max_length=100, verbose_name="Nombre del Equipo")
    flag = models.CharField(max_length=10, default="🏳️", verbose_name="Bandera (Emoji)")
    
    # Standing stats
    games_played = models.PositiveIntegerField(default=0, verbose_name="PJ")
    wins = models.PositiveIntegerField(default=0, verbose_name="G")
    draws = models.PositiveIntegerField(default=0, verbose_name="E")
    losses = models.PositiveIntegerField(default=0, verbose_name="P")
    goals_for = models.PositiveIntegerField(default=0, verbose_name="GF")
    goals_against = models.PositiveIntegerField(default=0, verbose_name="GC")
    points = models.PositiveIntegerField(default=0, verbose_name="Pts")

    class Meta:
        verbose_name = "Equipo de Grupo"
        verbose_name_plural = "Equipos de Grupo"
        unique_together = ('group', 'name')
    
    @property
    def goal_difference(self):
        return self.goals_for - self.goals_against

    def __str__(self):
        return f"{self.flag} {self.name}"


class GroupMatch(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='matches', verbose_name="Grupo")
    home_team = models.ForeignKey(GroupTeam, on_delete=models.CASCADE, related_name='home_matches', verbose_name="Equipo Local")
    away_team = models.ForeignKey(GroupTeam, on_delete=models.CASCADE, related_name='away_matches', verbose_name="Equipo Visitante")
    
    home_score = models.PositiveIntegerField(default=0, verbose_name="Goles Local")
    away_score = models.PositiveIntegerField(default=0, verbose_name="Goles Visitante")
    date = models.DateField(verbose_name="Fecha del Partido", default=timezone.now)
    played = models.BooleanField(default=False, verbose_name="Jugado")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Partido de Grupo"
        verbose_name_plural = "Partidos de Grupo"
        ordering = ['created_at']

    def clean(self):
        super().clean()
        if self.home_team and self.away_team:
            if self.home_team == self.away_team:
                raise ValidationError("Un equipo no puede jugar contra sí mismo.")
            if self.home_team.group != self.group or self.away_team.group != self.group:
                raise ValidationError("Ambos equipos deben pertenecer al mismo grupo.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.group.update_standings()

    def delete(self, *args, **kwargs):
        group = self.group
        super().delete(*args, **kwargs)
        group.update_standings()

    def __str__(self):
        return f"{self.group.name}: {self.home_team} {self.home_score} - {self.away_score} {self.away_team}"


class KnockoutMatch(models.Model):
    ROUND_CHOICES = [
        ('R32', 'Dieciseisavos de Final'),
        ('R16', 'Octavos de Final'),
        ('QF', 'Cuartos de Final'),
        ('SF', 'Semifinales'),
        ('TP', 'Tercer Puesto'),
        ('F', 'Final'),
    ]

    round = models.CharField(max_length=5, choices=ROUND_CHOICES, verbose_name="Ronda")
    match_number = models.PositiveIntegerField(verbose_name="Número de Partido")
    
    home_team = models.ForeignKey(GroupTeam, on_delete=models.SET_NULL, null=True, blank=True, related_name='home_knockout_matches', verbose_name="Equipo Local")
    away_team = models.ForeignKey(GroupTeam, on_delete=models.SET_NULL, null=True, blank=True, related_name='away_knockout_matches', verbose_name="Equipo Visitante")
    
    home_score = models.PositiveIntegerField(default=0, verbose_name="Goles Local")
    away_score = models.PositiveIntegerField(default=0, verbose_name="Goles Visitante")
    
    home_penalties = models.PositiveIntegerField(null=True, blank=True, verbose_name="Penaltis Local")
    away_penalties = models.PositiveIntegerField(null=True, blank=True, verbose_name="Penaltis Visitante")
    
    winner = models.ForeignKey(GroupTeam, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_knockout_matches', verbose_name="Ganador")
    played = models.BooleanField(default=False, verbose_name="Jugado")
    
    date = models.DateField(default=timezone.now, verbose_name="Fecha del Partido")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Partido de Eliminación Directa"
        verbose_name_plural = "Partidos de Eliminación Directa"
        ordering = ['round', 'match_number']
        unique_together = ('round', 'match_number')

    def clean(self):
        super().clean()
        if self.played:
            if self.home_team is None or self.away_team is None:
                raise ValidationError("No se puede jugar un partido sin definir ambos equipos.")
            if self.home_team == self.away_team:
                raise ValidationError("Un equipo no puede jugar contra sí mismo.")
            if self.home_score == self.away_score:
                if self.home_penalties is None or self.away_penalties is None:
                    raise ValidationError("Los partidos de eliminación directa no pueden terminar en empate sin penaltis.")
                if self.home_penalties == self.away_penalties:
                    raise ValidationError("En caso de empate en los penaltis, debe haber un ganador de la tanda.")

    def save(self, *args, **kwargs):
        if self.played:
            self.full_clean()
            if self.home_score > self.away_score:
                self.winner = self.home_team
            elif self.away_score > self.home_score:
                self.winner = self.away_team
            else:
                if self.home_penalties > self.away_penalties:
                    self.winner = self.home_team
                else:
                    self.winner = self.away_team
        else:
            self.winner = None
            self.home_penalties = None
            self.away_penalties = None
            
        super().save(*args, **kwargs)
        
        if self.played and self.winner:
            self.propagate_winner()
            self.propagate_loser()
        else:
            self.clear_from_next_round()
            self.clear_loser_from_third_place()

    def propagate_winner(self):
        next_round_map = {
            'R32': 'R16',
            'R16': 'QF',
            'QF': 'SF',
            'SF': 'F',
        }
        
        if self.round not in next_round_map:
            return
            
        next_round = next_round_map[self.round]
        next_match_number = (self.match_number + 1) // 2
        is_home = (self.match_number % 2 != 0)
        
        next_match, created = KnockoutMatch.objects.get_or_create(
            round=next_round,
            match_number=next_match_number
        )
        
        old_team = next_match.home_team if is_home else next_match.away_team
        if old_team != self.winner:
            if is_home:
                next_match.home_team = self.winner
            else:
                next_match.away_team = self.winner
            
            next_match.home_score = 0
            next_match.away_score = 0
            next_match.home_penalties = None
            next_match.away_penalties = None
            next_match.winner = None
            next_match.played = False
            next_match.save()

    def propagate_loser(self):
        loser_round_map = {
            'SF': 'TP',
        }
        if self.round not in loser_round_map:
            return

        next_match_number = 1
        is_home = (self.match_number == 1)
        loser = self.away_team if self.winner == self.home_team else self.home_team

        if loser is None:
            return

        next_match, created = KnockoutMatch.objects.get_or_create(
            round=loser_round_map[self.round],
            match_number=next_match_number
        )

        old_team = next_match.home_team if is_home else next_match.away_team
        if old_team != loser:
            if is_home:
                next_match.home_team = loser
            else:
                next_match.away_team = loser

            next_match.home_score = 0
            next_match.away_score = 0
            next_match.home_penalties = None
            next_match.away_penalties = None
            next_match.winner = None
            next_match.played = False
            next_match.save()

    def clear_from_next_round(self):
        next_round_map = {
            'R32': 'R16',
            'R16': 'QF',
            'QF': 'SF',
            'SF': 'F',
        }
        if self.round not in next_round_map:
            return
            
        next_round = next_round_map[self.round]
        next_match_number = (self.match_number + 1) // 2
        is_home = (self.match_number % 2 != 0)
        
        try:
            next_match = KnockoutMatch.objects.get(
                round=next_round,
                match_number=next_match_number
            )
            current_team = next_match.home_team if is_home else next_match.away_team
            if current_team:
                if is_home:
                    next_match.home_team = None
                else:
                    next_match.away_team = None
                
                next_match.home_score = 0
                next_match.away_score = 0
                next_match.home_penalties = None
                next_match.away_penalties = None
                next_match.winner = None
                next_match.played = False
                next_match.save()
        except KnockoutMatch.DoesNotExist:
            pass

    def clear_loser_from_third_place(self):
        loser_round_map = {
            'SF': 'TP',
        }
        if self.round not in loser_round_map:
            return

        next_match_number = 1
        is_home = (self.match_number == 1)

        try:
            next_match = KnockoutMatch.objects.get(
                round=loser_round_map[self.round],
                match_number=next_match_number
            )
            if is_home and next_match.home_team is not None:
                next_match.home_team = None
            elif not is_home and next_match.away_team is not None:
                next_match.away_team = None

            next_match.home_score = 0
            next_match.away_score = 0
            next_match.home_penalties = None
            next_match.away_penalties = None
            next_match.winner = None
            next_match.played = False
            next_match.save()
        except KnockoutMatch.DoesNotExist:
            pass

    @property
    def home_source_label(self):
        if self.round == 'R16':
            return f"Ganador Dieciseisavos M{(self.match_number * 2) - 1}"
        elif self.round == 'QF':
            return f"Ganador Octavos M{(self.match_number * 2) - 1}"
        elif self.round == 'SF':
            return f"Ganador Cuartos M{(self.match_number * 2) - 1}"
        elif self.round == 'TP':
            return "Perdedor Semifinal 1"
        elif self.round == 'F':
            return f"Ganador Semifinal 1"
        return "Por definir"

    @property
    def away_source_label(self):
        if self.round == 'R16':
            return f"Ganador Dieciseisavos M{self.match_number * 2}"
        elif self.round == 'QF':
            return f"Ganador Octavos M{self.match_number * 2}"
        elif self.round == 'SF':
            return f"Ganador Cuartos M{self.match_number * 2}"
        elif self.round == 'TP':
            return "Perdedor Semifinal 2"
        elif self.round == 'F':
            return f"Ganador Semifinal 2"
        return "Por definir"

    def __str__(self):
        h_name = self.home_team.name if self.home_team else f"Ganador M{(self.match_number*2)-1}"
        a_name = self.away_team.name if self.away_team else f"Ganador M{self.match_number*2}"
        if self.played:
            if self.home_score == self.away_score:
                return f"{self.get_round_display()} - M{self.match_number}: {self.home_team.flag} {h_name} {self.home_score} ({self.home_penalties}) - ({self.away_penalties}) {self.away_score} {a_name} {self.away_team.flag}"
            return f"{self.get_round_display()} - M{self.match_number}: {self.home_team.flag} {h_name} {self.home_score} - {self.away_score} {a_name} {self.away_team.flag}"
        return f"{self.get_round_display()} - M{self.match_number}: {h_name} vs {a_name}"

