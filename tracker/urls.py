from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('match/delete/<int:match_id>/', views.delete_match, name='delete_match'),
    path('team/<str:team_name>/', views.team_detail, name='team_detail'),
    path('mundial/', views.mundial_dashboard, name='mundial_dashboard'),
    path('mundial/group/add/', views.add_group, name='add_group'),
    path('mundial/team/add/', views.add_group_team, name='add_group_team'),
    path('mundial/match/add/', views.add_group_match, name='add_group_match'),
    path('mundial/match/delete/<int:match_id>/', views.delete_group_match, name='delete_group_match'),
    path('mundial/populate/', views.populate_worldcup, name='populate_worldcup'),
    path('mundial/group/edit/<int:group_id>/', views.edit_group, name='edit_group'),
    path('mundial/group/delete/<int:group_id>/', views.delete_group, name='delete_group'),
    path('mundial/match/update/<int:match_id>/', views.update_group_match_score, name='update_group_match_score'),
    path('logout/', views.logout_view, name='logout'),
    path('mundial/knockout/update/<int:match_id>/', views.update_knockout_match_score, name='update_knockout_match_score'),
    path('mundial/knockout/reset-match/<int:match_id>/', views.reset_knockout_match, name='reset_knockout_match'),
    path('mundial/knockout/reset-bracket/', views.reset_knockout_bracket, name='reset_knockout_bracket'),
]
