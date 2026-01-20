from django.urls import path
from .views import (
    AchievementListView,
    UserAchievementListView,
    AchievementCategoriesView,
    UnnotifiedAchievementsView,
    PersonalRecordListView,
    PersonalRecordDetailView,
    UserStatisticsView,
    ExerciseRankingView,
    AllExerciseRankingsView,
    LeaderboardView,
    RecalculateStatisticsView,
)

urlpatterns = [
    # Achievement endpoints
    path('list/', AchievementListView.as_view(), name='achievement-list'),
    path('earned/', UserAchievementListView.as_view(), name='earned-achievements'),
    path('categories/', AchievementCategoriesView.as_view(), name='achievement-categories'),
    path('unnotified/', UnnotifiedAchievementsView.as_view(), name='unnotified-achievements'),
    path('unnotified/mark-seen/', UnnotifiedAchievementsView.as_view(), name='mark-achievements-seen'),

    # Personal Record endpoints
    path('prs/', PersonalRecordListView.as_view(), name='pr-list'),
    path('prs/<int:exercise_id>/', PersonalRecordDetailView.as_view(), name='pr-detail'),

    # Statistics endpoints
    path('stats/', UserStatisticsView.as_view(), name='user-statistics'),
    path('recalculate/', RecalculateStatisticsView.as_view(), name='recalculate-statistics'),

    # Ranking/Percentile endpoints
    path('ranking/<int:exercise_id>/', ExerciseRankingView.as_view(), name='exercise-ranking'),
    path('rankings/', AllExerciseRankingsView.as_view(), name='all-rankings'),

    # Leaderboard endpoints
    path('leaderboard/<int:exercise_id>/', LeaderboardView.as_view(), name='exercise-leaderboard'),
]
