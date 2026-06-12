from django import forms
from .models import Match, Group, GroupTeam, GroupMatch

class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['sport', 'home_team', 'away_team', 'home_score', 'away_score', 'date']
        widgets = {
            'sport': forms.Select(attrs={
                'class': 'form-select premium-input',
                'id': 'id_sport'
            }),
            'home_team': forms.TextInput(attrs={
                'class': 'form-input premium-input',
                'placeholder': 'Ej. Real Madrid',
                'autocomplete': 'off',
                'id': 'id_home_team'
            }),
            'away_team': forms.TextInput(attrs={
                'class': 'form-input premium-input',
                'placeholder': 'Ej. Barcelona',
                'autocomplete': 'off',
                'id': 'id_away_team'
            }),
            'home_score': forms.NumberInput(attrs={
                'class': 'form-input premium-input score-input',
                'min': '0',
                'placeholder': '0',
                'id': 'id_home_score'
            }),
            'away_score': forms.NumberInput(attrs={
                'class': 'form-input premium-input score-input',
                'min': '0',
                'placeholder': '0',
                'id': 'id_away_score'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-input premium-input',
                'type': 'date',
                'id': 'id_date'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        home_team = cleaned_data.get('home_team')
        away_team = cleaned_data.get('away_team')

        if home_team and away_team and home_team.strip().lower() == away_team.strip().lower():
            raise forms.ValidationError("El equipo local y el equipo visitante no pueden ser iguales.")
        
        return cleaned_data


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input premium-input',
                'placeholder': 'Ej. Grupo A',
                'id': 'id_group_name'
            })
        }


class GroupTeamForm(forms.ModelForm):
    class Meta:
        model = GroupTeam
        fields = ['group', 'name', 'flag']
        widgets = {
            'group': forms.Select(attrs={
                'class': 'form-select premium-input',
                'id': 'id_team_group'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input premium-input',
                'placeholder': 'Ej. México',
                'id': 'id_team_name'
            }),
            'flag': forms.TextInput(attrs={
                'class': 'form-input premium-input',
                'placeholder': 'Ej. 🇲🇽',
                'id': 'id_team_flag'
            }),
        }


class GroupMatchForm(forms.ModelForm):
    class Meta:
        model = GroupMatch
        fields = ['group', 'home_team', 'away_team', 'date']
        widgets = {
            'group': forms.Select(attrs={
                'class': 'form-select premium-input',
                'id': 'id_match_group'
            }),
            'home_team': forms.Select(attrs={
                'class': 'form-select premium-input',
                'id': 'id_match_home_team'
            }),
            'away_team': forms.Select(attrs={
                'class': 'form-select premium-input',
                'id': 'id_match_away_team'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-input premium-input',
                'type': 'date',
                'id': 'id_match_date'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        home_team = cleaned_data.get('home_team')
        away_team = cleaned_data.get('away_team')

        if home_team and away_team and home_team == away_team:
            raise forms.ValidationError("Un equipo no puede jugar contra sí mismo.")
        
        return cleaned_data
