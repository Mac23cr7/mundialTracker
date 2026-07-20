from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from datetime import date
from django.contrib.auth.models import User
from .models import Match, Group, GroupTeam, GroupMatch, KnockoutMatch
from .forms import MatchForm

class MatchModelTest(TestCase):
    def test_create_valid_football_match(self):
        match = Match(
            sport='FB',
            home_team='Barcelona',
            away_team='Real Madrid',
            home_score=2,
            away_score=1,
            date=date(2026, 6, 9)
        )
        match.full_clean()
        match.save()
        self.assertEqual(match.sport, 'FB')
        self.assertEqual(str(match), "Fútbol: Barcelona 2 - 1 Real Madrid (2026-06-09)")

    def test_create_valid_basketball_match(self):
        match = Match(
            sport='BK',
            home_team='Lakers',
            away_team='Celtics',
            home_score=102,
            away_score=98,
            date=date(2026, 6, 9)
        )
        match.full_clean()
        match.save()
        self.assertEqual(match.sport, 'BK')
        self.assertEqual(str(match), "Básquet: Lakers 102 - 98 Celtics (2026-06-09)")

    def test_validation_same_team_fails(self):
        match = Match(
            sport='FB',
            home_team='Barcelona',
            away_team='Barcelona',
            home_score=1,
            away_score=1,
            date=date(2026, 6, 9)
        )
        with self.assertRaises(ValidationError):
            match.full_clean()


class MatchFormTest(TestCase):
    def test_valid_form(self):
        form_data = {
            'sport': 'FB',
            'home_team': 'Chelsea',
            'away_team': 'Arsenal',
            'home_score': 3,
            'away_score': 2,
            'date': '2026-06-09'
        }
        form = MatchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_same_teams(self):
        form_data = {
            'sport': 'FB',
            'home_team': 'Arsenal',
            'away_team': 'Arsenal',
            'home_score': 0,
            'away_score': 0,
            'date': '2026-06-09'
        }
        form = MatchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertEqual(form.errors['__all__'], ['El equipo local y el equipo visitante no pueden ser iguales.'])


class MatchViewsTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        self.match1 = Match.objects.create(
            sport='FB',
            home_team='Boca Juniors',
            away_team='River Plate',
            home_score=2,
            away_score=0,
            date=date(2026, 6, 8)
        )
        self.match2 = Match.objects.create(
            sport='BK',
            home_team='Boca Juniors',
            away_team='San Lorenzo',
            home_score=85,
            away_score=90,
            date=date(2026, 6, 9)
        )

    def test_dashboard_view_loads(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/dashboard.html')
        self.assertContains(response, 'Boca Juniors')
        self.assertContains(response, 'River Plate')
        self.assertContains(response, 'San Lorenzo')

    def test_dashboard_filtering(self):
        # Filter by Football
        response = self.client.get(reverse('dashboard') + '?sport=FB')
        self.assertContains(response, 'River Plate')
        self.assertNotContains(response, 'San Lorenzo')

        # Filter by Basketball
        response = self.client.get(reverse('dashboard') + '?sport=BK')
        self.assertNotContains(response, 'River Plate')
        self.assertContains(response, 'San Lorenzo')

    def test_dashboard_search(self):
        response = self.client.get(reverse('dashboard') + '?search=River')
        self.assertContains(response, 'River Plate')
        self.assertNotContains(response, 'San Lorenzo')

    def test_team_detail_view(self):
        response = self.client.get(reverse('team_detail', args=['Boca Juniors']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/team_detail.html')
        # Boca Juniors played 2 matches: 1 win (home, FB), 1 loss (home, BK)
        self.assertEqual(response.context['total_played'], 2)
        self.assertEqual(response.context['wins'], 1)
        self.assertEqual(response.context['losses'], 1)
        self.assertEqual(response.context['draws'], 0)
        self.assertEqual(response.context['win_rate'], 50.0)

    def test_delete_match_view(self):
        self.client.force_login(self.admin_user)
        # Delete match1
        response = self.client.post(reverse('delete_match', args=[self.match1.id]))
        self.assertEqual(response.status_code, 302) # Redirects to dashboard
        self.assertFalse(Match.objects.filter(id=self.match1.id).exists())


class WorldCupStandingsTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        self.group = Group.objects.create(name="Grupo A")
        self.mexico = GroupTeam.objects.create(group=self.group, name="México", flag="🇲🇽")
        self.south_africa = GroupTeam.objects.create(group=self.group, name="Sudáfrica", flag="🇿🇦")
        self.south_korea = GroupTeam.objects.create(group=self.group, name="Corea del Sur", flag="🇰🇷")
        self.czechia = GroupTeam.objects.create(group=self.group, name="Chequia", flag="🇨🇿")

    def test_standings_calculation(self):
        # Initial stats
        self.assertEqual(self.mexico.points, 0)
        self.assertEqual(self.mexico.games_played, 0)

        # Match 1: Mexico 2 - 1 South Africa
        match1 = GroupMatch.objects.create(
            group=self.group,
            home_team=self.mexico,
            away_team=self.south_africa,
            home_score=2,
            away_score=1,
            played=True
        )
        
        # Refresh from DB
        self.mexico.refresh_from_db()
        self.south_africa.refresh_from_db()

        self.assertEqual(self.mexico.games_played, 1)
        self.assertEqual(self.mexico.wins, 1)
        self.assertEqual(self.mexico.points, 3)
        self.assertEqual(self.mexico.goals_for, 2)
        self.assertEqual(self.mexico.goals_against, 1)
        self.assertEqual(self.mexico.goal_difference, 1)

        self.assertEqual(self.south_africa.games_played, 1)
        self.assertEqual(self.south_africa.losses, 1)
        self.assertEqual(self.south_africa.points, 0)
        self.assertEqual(self.south_africa.goals_for, 1)
        self.assertEqual(self.south_africa.goals_against, 2)
        self.assertEqual(self.south_africa.goal_difference, -1)

    def test_standings_sorting(self):
        # Mexico wins
        GroupMatch.objects.create(
            group=self.group, home_team=self.mexico, away_team=self.south_africa,
            home_score=2, away_score=0, played=True
        )
        # South Korea draws with Czechia
        GroupMatch.objects.create(
            group=self.group, home_team=self.south_korea, away_team=self.czechia,
            home_score=1, away_score=1, played=True
        )

        response = self.client.get(reverse('mundial_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check sorting order in context
        teams_in_context = response.context['groups_data'][0]['teams']
        
        # Expected order: Mexico (3 pts), Chequia (1 pt, DG=0, GF=1), Corea del Sur (1 pt, DG=0, GF=1, name asc), South Africa (0 pts)
        self.assertEqual(teams_in_context[0], self.mexico)
        self.assertEqual(teams_in_context[1], self.czechia)
        self.assertEqual(teams_in_context[2], self.south_korea)
        self.assertEqual(teams_in_context[3], self.south_africa)

    def test_best_thirds_calculation(self):
        # We already have Group A populated in setUp.
        # Now let's create Group B.
        group_b = Group.objects.create(name="Grupo B")
        spain = GroupTeam.objects.create(group=group_b, name="España", flag="🇪🇸")
        germany = GroupTeam.objects.create(group=group_b, name="Alemania", flag="🇩🇪")
        japan = GroupTeam.objects.create(group=group_b, name="Japón", flag="🇯🇵")
        costa_rica = GroupTeam.objects.create(group=group_b, name="Costa Rica", flag="🇨🇷")

        # In Group A, play matches to make Chequia 3rd with 1 point:
        # Mexico 2 - 0 South Africa
        GroupMatch.objects.create(group=self.group, home_team=self.mexico, away_team=self.south_africa, home_score=2, away_score=0, played=True)
        # South Korea 1 - 1 Chequia
        GroupMatch.objects.create(group=self.group, home_team=self.south_korea, away_team=self.czechia, home_score=1, away_score=1, played=True)
        # Standings Group A:
        # 1. Mexico (3 pts)
        # 2. Chequia (1 pt, DG=0, GF=1, alphabetical 'Ch')
        # 3. South Korea (1 pt, DG=0, GF=1, alphabetical 'Co')
        # 4. South Africa (0 pts)
        # So South Korea is 3rd in Group A with 1 point!

        # In Group B, play matches to make Japan 3rd with 3 points:
        # Spain 3 - 0 Germany
        GroupMatch.objects.create(group=group_b, home_team=spain, away_team=germany, home_score=3, away_score=0, played=True)
        # Japan 1 - 0 Costa Rica
        GroupMatch.objects.create(group=group_b, home_team=japan, away_team=costa_rica, home_score=1, away_score=0, played=True)
        # Spain 2 - 0 Japan
        GroupMatch.objects.create(group=group_b, home_team=spain, away_team=japan, home_score=2, away_score=0, played=True)
        # Germany 3 - 0 Costa Rica
        GroupMatch.objects.create(group=group_b, home_team=germany, away_team=costa_rica, home_score=3, away_score=0, played=True)
        # Standings Group B:
        # 1. Spain (6 pts)
        # 2. Germany (3 pts, DG=0)
        # 3. Japan (3 pts, DG=-1)
        # 4. Costa Rica (0 pts)
        # So Japan is 3rd in Group B with 3 points!

        # Request dashboard
        response = self.client.get(reverse('mundial_dashboard'))
        self.assertEqual(response.status_code, 200)

        # Check mejores_terceros in context
        mejores_terceros = response.context['mejores_terceros']
        
        # We expect Japan (3 pts) to be sorted above South Korea (1 pt)
        self.assertEqual(len(mejores_terceros), 2)
        self.assertEqual(mejores_terceros[0], japan)
        self.assertEqual(mejores_terceros[1], self.south_korea)

        # Check qualified_thirds_ids
        qualified_thirds_ids = response.context['qualified_thirds_ids']
        self.assertIn(japan.id, qualified_thirds_ids)
        self.assertIn(self.south_korea.id, qualified_thirds_ids)

        # Check total clasificados_32 count:
        # 2 direct from Group A (Mexico, Chequia) +
        # 2 direct from Group B (Spain, Germany) +
        # 2 thirds (Japan, South Korea)
        # Total = 6 teams
        clasificados = response.context['clasificados_32']
        self.assertEqual(len(clasificados), 6)

    def test_edit_group_view(self):
        self.client.force_login(self.admin_user)
        self.assertEqual(self.group.name, "Grupo A")
        response = self.client.post(
            reverse('edit_group', args=[self.group.id]),
            data={'name': 'Grupo Z'}
        )
        self.assertEqual(response.status_code, 302)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Grupo Z")

    def test_delete_group_view(self):
        self.client.force_login(self.admin_user)
        group_b = Group.objects.create(name="Grupo B")
        self.assertTrue(Group.objects.filter(id=group_b.id).exists())
        response = self.client.post(reverse('delete_group', args=[group_b.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Group.objects.filter(id=group_b.id).exists())

    def test_update_group_match_score_view(self):
        self.client.force_login(self.admin_user)
        match = GroupMatch.objects.create(
            group=self.group,
            home_team=self.mexico,
            away_team=self.south_africa,
            played=False
        )
        self.assertFalse(match.played)
        self.assertEqual(match.home_score, 0)
        self.assertEqual(match.away_score, 0)

        response = self.client.post(
            reverse('update_group_match_score', args=[match.id]),
            data={'home_score': '3', 'away_score': '2'}
        )
        self.assertEqual(response.status_code, 302)
        
        match.refresh_from_db()
        self.assertTrue(match.played)
        self.assertEqual(match.home_score, 3)
        self.assertEqual(match.away_score, 2)

    def test_show_qualifiers_condition(self):
        # 1. No matches registered -> show_qualifiers should be False
        response = self.client.get(reverse('mundial_dashboard'))
        self.assertFalse(response.context['show_qualifiers'])
        
        # 2. Add one unplayed match -> show_qualifiers should be False
        match = GroupMatch.objects.create(
            group=self.group,
            home_team=self.mexico,
            away_team=self.south_africa,
            played=False
        )
        response = self.client.get(reverse('mundial_dashboard'))
        self.assertFalse(response.context['show_qualifiers'])
        
        # 3. Mark the match as played -> show_qualifiers should be True
        match.played = True
        match.save()
        response = self.client.get(reverse('mundial_dashboard'))
        self.assertTrue(response.context['show_qualifiers'])


class WorldCupPermissionsAndKnockoutTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        self.viewer_user = User.objects.create_user('viewer', 'viewer@example.com', 'viewer123')
        
        self.group = Group.objects.create(name="Grupo A")
        self.team_a = GroupTeam.objects.create(group=self.group, name="México", flag="🇲🇽")
        self.team_b = GroupTeam.objects.create(group=self.group, name="Sudáfrica", flag="🇿🇦")
        
        self.match = GroupMatch.objects.create(
            group=self.group,
            home_team=self.team_a,
            away_team=self.team_b,
            home_score=0,
            away_score=0,
            played=False
        )

    def test_anonymous_user_cannot_write(self):
        # Anonymous user cannot edit group name
        response = self.client.post(
            reverse('edit_group', args=[self.group.id]),
            data={'name': 'Grupo Modificado'}
        )
        self.assertEqual(response.status_code, 302)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Grupo A")

        # Anonymous user cannot update match score
        response = self.client.post(
            reverse('update_group_match_score', args=[self.match.id]),
            data={'home_score': 3, 'away_score': 1}
        )
        self.assertEqual(response.status_code, 302)
        self.match.refresh_from_db()
        self.assertFalse(self.match.played)

    def test_normal_user_cannot_write(self):
        self.client.force_login(self.viewer_user)
        # Normal user cannot edit group name
        response = self.client.post(
            reverse('edit_group', args=[self.group.id]),
            data={'name': 'Grupo Modificado'}
        )
        self.assertEqual(response.status_code, 302)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Grupo A")

    def test_super_admin_can_write(self):
        self.client.force_login(self.admin_user)
        
        # Admin can update match score
        response = self.client.post(
            reverse('update_group_match_score', args=[self.match.id]),
            data={'home_score': 3, 'away_score': 1}
        )
        self.assertEqual(response.status_code, 302)
        self.match.refresh_from_db()
        self.assertTrue(self.match.played)
        self.assertEqual(self.match.home_score, 3)

    def test_knockout_match_validation(self):
        # Direct generation of KnockoutMatch
        match = KnockoutMatch(
            round='R32',
            match_number=1,
            home_team=self.team_a,
            away_team=self.team_b,
            home_score=2,
            away_score=2,
            played=True
        )
        # Should fail clean because home_score == away_score and no penalties are provided
        with self.assertRaises(ValidationError):
            match.full_clean()

        # Provide equal penalties, should also fail
        match.home_penalties = 4
        match.away_penalties = 4
        with self.assertRaises(ValidationError):
            match.full_clean()

        # Provide distinct penalties, should pass
        match.away_penalties = 5
        match.full_clean()
        match.save()
        self.assertEqual(match.winner, self.team_b)

    def test_knockout_progression_and_cascade(self):
        # Create bracket step-by-step
        # M1 (R32) -> home of M1 (R16)
        # M2 (R32) -> away of M1 (R16)
        m1_r32 = KnockoutMatch.objects.create(
            round='R32',
            match_number=1,
            home_team=self.team_a,
            away_team=self.team_b,
            played=False
        )
        
        m2_r32 = KnockoutMatch.objects.create(
            round='R32',
            match_number=2,
            home_team=self.team_b,
            away_team=self.team_a,
            played=False
        )
        
        # M1 (R16) should exist
        m1_r16 = KnockoutMatch.objects.create(
            round='R16',
            match_number=1,
            played=False
        )
        
        # Update M1 R32 with winner Mexico
        m1_r32.home_score = 2
        m1_r32.away_score = 1
        m1_r32.played = True
        m1_r32.save()
        
        # Check that team_a has propagated to M1 R16 home
        m1_r16.refresh_from_db()
        self.assertEqual(m1_r16.home_team, self.team_a)
        
        # Update M2 R32 with winner South Africa
        m2_r32.home_score = 3
        m2_r32.away_score = 0
        m2_r32.played = True
        m2_r32.save()
        
        # Check that team_b has propagated to M1 R16 away
        m1_r16.refresh_from_db()
        self.assertEqual(m1_r16.away_team, self.team_b)
        
        # Now, play M1 R16 with winner South Africa
        m1_r16.home_score = 1
        m1_r16.away_score = 2
        m1_r16.played = True
        m1_r16.save()
        
        # Let's get QF M1 which was auto-created by propagation
        qf_m1 = KnockoutMatch.objects.get(
            round='QF',
            match_number=1
        )
        
        # Update R16 to propagate winner to QF
        m1_r16.save() # Trigger propagation again
        qf_m1.refresh_from_db()
        self.assertEqual(qf_m1.home_team, self.team_b)
        
        # Now create two semifinal matches and play them to exercise third place propagation
        sf1 = KnockoutMatch.objects.create(round='SF', match_number=1, played=False)
        sf2 = KnockoutMatch.objects.create(round='SF', match_number=2, played=False)
        
        sf1.home_team = self.team_a
        sf1.away_team = self.team_b
        sf1.home_score = 2
        sf1.away_score = 1
        sf1.played = True
        sf1.save()
        
        sf2.home_team = self.team_b
        sf2.away_team = self.team_a
        sf2.home_score = 1
        sf2.away_score = 3
        sf2.played = True
        sf2.save()
        
        tp_match = KnockoutMatch.objects.get(round='TP', match_number=1)
        self.assertIsNotNone(tp_match.home_team)
        self.assertIsNotNone(tp_match.away_team)
        self.assertEqual(tp_match.home_team, self.team_b)
        self.assertEqual(tp_match.away_team, self.team_a)
        
        # Now reset M1 R32 score to see cascade clearing!
        m1_r32.played = False
        m1_r32.save()
        
        # M1 R16 home_team should be cleared
        m1_r16.refresh_from_db()
        self.assertIsNone(m1_r16.home_team)
        self.assertFalse(m1_r16.played)
        
        # QF M1 home_team should be cleared because M1 R16 was reset
        qf_m1.refresh_from_db()
        self.assertIsNone(qf_m1.home_team)
