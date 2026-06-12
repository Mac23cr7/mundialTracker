from django.contrib import admin
from .models import Match, Group, GroupTeam, GroupMatch, KnockoutMatch

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('sport', 'home_team', 'home_score', 'away_score', 'away_team', 'date')
    list_filter = ('sport', 'date')
    search_fields = ('home_team', 'away_team')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(GroupTeam)
class GroupTeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'flag', 'games_played', 'points', 'goal_difference')
    list_filter = ('group',)
    search_fields = ('name', 'group__name')

@admin.register(GroupMatch)
class GroupMatchAdmin(admin.ModelAdmin):
    list_display = ('group', 'home_team', 'home_score', 'away_score', 'away_team', 'date', 'played')
    list_filter = ('group', 'played', 'date')
    search_fields = ('home_team__name', 'away_team__name', 'group__name')

@admin.register(KnockoutMatch)
class KnockoutMatchAdmin(admin.ModelAdmin):
    list_display = ('round', 'match_number', 'home_team', 'home_score', 'away_score', 'away_team', 'winner', 'played')
    list_filter = ('round', 'played', 'date')
    search_fields = ('home_team__name', 'away_team__name', 'round')

