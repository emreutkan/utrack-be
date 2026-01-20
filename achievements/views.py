from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F
from django.db import transaction
from decimal import Decimal
import logging
import numpy as np

from .models import (
    Achievement, UserAchievement, PersonalRecord,
    ExerciseStatistics, UserStatistics
)
from .serializers import (
    AchievementSerializer, UserAchievementSerializer,
    AchievementProgressSerializer, PersonalRecordSerializer,
    PersonalRecordSummarySerializer, ExerciseStatisticsSerializer,
    UserExerciseRankingSerializer, UserStatisticsSerializer,
    LeaderboardEntrySerializer, NewAchievementNotificationSerializer,
    PRUpdateResultSerializer
)
from exercise.models import Exercise
from workout.models import Workout, WorkoutExercise, ExerciseSet
from workout.permissions import is_pro_user, get_pro_response

logger = logging.getLogger('achievements')


class AchievementListView(APIView):
    """
    GET /api/achievements/list/
    List all available achievements with user's progress.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        category = request.query_params.get('category', None)

        # Get all active achievements
        achievements = Achievement.objects.filter(is_active=True)
        if category:
            achievements = achievements.filter(category=category)

        # Get user's earned achievements
        user_achievements = UserAchievement.objects.filter(
            user=user,
            achievement__in=achievements
        ).select_related('achievement')

        earned_map = {ua.achievement_id: ua for ua in user_achievements}

        # Build progress data for each achievement
        result = []
        for achievement in achievements:
            user_achievement = earned_map.get(achievement.id)
            is_earned = user_achievement is not None

            # Calculate current progress
            current_progress = self._get_achievement_progress(user, achievement)

            # Calculate percentage
            if achievement.requirement_value > 0:
                progress_pct = min(100, float(current_progress) / float(achievement.requirement_value) * 100)
            else:
                progress_pct = 100 if is_earned else 0

            result.append({
                'achievement': AchievementSerializer(achievement).data,
                'is_earned': is_earned,
                'current_progress': current_progress,
                'progress_percentage': round(progress_pct, 1),
                'earned_at': user_achievement.earned_at if user_achievement else None,
                'earned_value': user_achievement.earned_value if user_achievement else None
            })

        return Response(result)

    def _get_achievement_progress(self, user, achievement):
        """Calculate current progress for an achievement."""
        category = achievement.category

        if category == 'workout_count':
            return Workout.objects.filter(user=user, is_done=True, is_rest_day=False).count()

        elif category == 'workout_streak':
            stats, _ = UserStatistics.objects.get_or_create(user=user)
            return stats.current_streak

        elif category == 'pr_weight':
            if achievement.exercise:
                pr = PersonalRecord.objects.filter(
                    user=user, exercise=achievement.exercise
                ).first()
                return pr.best_weight if pr else 0
            return 0

        elif category == 'pr_one_rep_max':
            if achievement.exercise:
                pr = PersonalRecord.objects.filter(
                    user=user, exercise=achievement.exercise
                ).first()
                return pr.best_one_rep_max if pr else 0
            return 0

        elif category == 'total_volume':
            stats, _ = UserStatistics.objects.get_or_create(user=user)
            return stats.total_volume

        elif category == 'exercise_count':
            return WorkoutExercise.objects.filter(
                workout__user=user,
                workout__is_done=True
            ).values('exercise').distinct().count()

        return 0


class UserAchievementListView(APIView):
    """
    GET /api/achievements/earned/
    List only the user's earned achievements.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_achievements = UserAchievement.objects.filter(
            user=user
        ).select_related('achievement', 'achievement__exercise').order_by('-earned_at')

        serializer = UserAchievementSerializer(user_achievements, many=True)
        return Response(serializer.data)


class AchievementCategoriesView(APIView):
    """
    GET /api/achievements/categories/
    Get list of achievement categories with counts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        categories = []
        for code, name in Achievement.CATEGORY_CHOICES:
            total = Achievement.objects.filter(category=code, is_active=True).count()
            earned = UserAchievement.objects.filter(
                user=user,
                achievement__category=code
            ).count()

            categories.append({
                'code': code,
                'name': name,
                'total': total,
                'earned': earned,
                'progress_percentage': round((earned / total * 100) if total > 0 else 0, 1)
            })

        return Response(categories)


class UnnotifiedAchievementsView(APIView):
    """
    GET /api/achievements/unnotified/
    Get achievements that haven't been shown to the user yet.

    POST /api/achievements/unnotified/mark-seen/
    Mark achievements as seen.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        unnotified = UserAchievement.objects.filter(
            user=user,
            is_notified=False
        ).select_related('achievement')

        result = []
        for ua in unnotified:
            result.append({
                'achievement': AchievementSerializer(ua.achievement).data,
                'earned_at': ua.earned_at,
                'earned_value': ua.earned_value,
                'message': f"Achievement unlocked: {ua.achievement.name}!"
            })

        return Response(result)

    def post(self, request):
        user = request.user
        achievement_ids = request.data.get('achievement_ids', [])

        if achievement_ids:
            UserAchievement.objects.filter(
                user=user,
                achievement_id__in=achievement_ids,
                is_notified=False
            ).update(is_notified=True)
        else:
            # Mark all as seen
            UserAchievement.objects.filter(
                user=user,
                is_notified=False
            ).update(is_notified=True)

        return Response({'status': 'ok'})


class PersonalRecordListView(APIView):
    """
    GET /api/achievements/prs/
    List all personal records for the user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        prs = PersonalRecord.objects.filter(
            user=user
        ).select_related('exercise').order_by('-best_weight')

        serializer = PersonalRecordSummarySerializer(prs, many=True)
        return Response(serializer.data)


class PersonalRecordDetailView(APIView):
    """
    GET /api/achievements/prs/<exercise_id>/
    Get detailed PR for a specific exercise.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, exercise_id):
        user = request.user

        try:
            pr = PersonalRecord.objects.select_related('exercise').get(
                user=user,
                exercise_id=exercise_id
            )
            serializer = PersonalRecordSerializer(pr)
            return Response(serializer.data)
        except PersonalRecord.DoesNotExist:
            return Response(
                {'error': 'No personal record found for this exercise'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserStatisticsView(APIView):
    """
    GET /api/achievements/stats/
    Get user's overall statistics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        stats, created = UserStatistics.objects.get_or_create(user=user)

        if created:
            # Initialize stats from existing data
            self._initialize_stats(user, stats)

        serializer = UserStatisticsSerializer(stats)
        return Response(serializer.data)

    def _initialize_stats(self, user, stats):
        """Initialize statistics from existing workout data."""
        # Count completed workouts
        workouts = Workout.objects.filter(user=user, is_done=True, is_rest_day=False)
        stats.total_workouts = workouts.count()

        # Sum duration
        total_duration = workouts.aggregate(total=Sum('duration'))['total'] or 0
        stats.total_workout_duration = total_duration

        # Calculate total volume, sets, reps from all exercises
        sets = ExerciseSet.objects.filter(
            workout_exercise__workout__user=user,
            workout_exercise__workout__is_done=True,
            is_warmup=False
        )

        aggregates = sets.aggregate(
            total_sets=Count('id'),
            total_reps=Sum('reps'),
            total_volume=Sum(F('weight') * F('reps'))
        )

        stats.total_sets = aggregates['total_sets'] or 0
        stats.total_reps = aggregates['total_reps'] or 0
        stats.total_volume = aggregates['total_volume'] or 0

        # Count achievements
        stats.total_achievements = UserAchievement.objects.filter(user=user).count()
        stats.total_points = UserAchievement.objects.filter(
            user=user
        ).aggregate(total=Sum('achievement__points'))['total'] or 0

        # Count PRs
        stats.total_prs = PersonalRecord.objects.filter(user=user).count()

        stats.save()


class ExerciseRankingView(APIView):
    """
    GET /api/achievements/ranking/<exercise_id>/
    Get user's ranking/percentile for a specific exercise.
    Shows "Only X% of users can lift this much" message.
    PRO only feature.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, exercise_id):
        # PRO check
        if not is_pro_user(request.user):
            return get_pro_response()
        
        user = request.user

        try:
            exercise = Exercise.objects.get(id=exercise_id)
        except Exercise.DoesNotExist:
            return Response(
                {'error': 'Exercise not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get user's PR for this exercise
        try:
            user_pr = PersonalRecord.objects.get(user=user, exercise=exercise)
        except PersonalRecord.DoesNotExist:
            return Response({
                'exercise_id': exercise_id,
                'exercise_name': exercise.name,
                'user_best_weight': 0,
                'user_best_one_rm': 0,
                'weight_percentile': None,
                'one_rm_percentile': None,
                'total_users': 0,
                'percentile_message': 'No personal record yet. Start lifting!'
            })

        # Get or create exercise statistics
        stats, created = ExerciseStatistics.objects.get_or_create(exercise=exercise)

        if created or not stats.weight_percentiles:
            # Recalculate statistics
            self._calculate_exercise_statistics(exercise, stats)

        # Get user's percentile
        weight_percentile = stats.get_user_percentile(float(user_pr.best_weight), 'weight')
        one_rm_percentile = stats.get_user_percentile(float(user_pr.best_one_rep_max), 'one_rm')

        # Generate percentile message
        if one_rm_percentile is not None and one_rm_percentile >= 90:
            top_percent = 100 - one_rm_percentile
            message = f"Top {top_percent}%! Only {top_percent}% of users can lift this much on {exercise.name}."
        elif one_rm_percentile is not None and one_rm_percentile >= 75:
            message = f"Stronger than {one_rm_percentile}% of users on {exercise.name}!"
        elif one_rm_percentile is not None:
            message = f"You're in the top {100 - one_rm_percentile}% for {exercise.name}. Keep pushing!"
        else:
            message = "Keep training to see how you compare!"

        return Response({
            'exercise_id': exercise_id,
            'exercise_name': exercise.name,
            'user_best_weight': user_pr.best_weight,
            'user_best_one_rm': user_pr.best_one_rep_max,
            'weight_percentile': weight_percentile,
            'one_rm_percentile': one_rm_percentile,
            'total_users': stats.total_users,
            'percentile_message': message
        })

    def _calculate_exercise_statistics(self, exercise, stats):
        """Calculate percentile statistics for an exercise."""
        prs = PersonalRecord.objects.filter(
            exercise=exercise,
            best_weight__gt=0
        ).values_list('best_weight', 'best_one_rep_max')

        if not prs:
            stats.total_users = 0
            stats.save()
            return

        weights = [float(pr[0]) for pr in prs if pr[0] > 0]
        one_rms = [float(pr[1]) for pr in prs if pr[1] > 0]

        stats.total_users = len(weights)

        if weights:
            weights_arr = np.array(weights)
            stats.weight_percentiles = {
                '10': float(np.percentile(weights_arr, 10)),
                '25': float(np.percentile(weights_arr, 25)),
                '50': float(np.percentile(weights_arr, 50)),
                '75': float(np.percentile(weights_arr, 75)),
                '90': float(np.percentile(weights_arr, 90)),
                '95': float(np.percentile(weights_arr, 95)),
                '99': float(np.percentile(weights_arr, 99)),
            }
            stats.average_weight = Decimal(str(np.mean(weights_arr)))
            stats.median_weight = Decimal(str(np.median(weights_arr)))

        if one_rms:
            one_rms_arr = np.array(one_rms)
            stats.one_rm_percentiles = {
                '10': float(np.percentile(one_rms_arr, 10)),
                '25': float(np.percentile(one_rms_arr, 25)),
                '50': float(np.percentile(one_rms_arr, 50)),
                '75': float(np.percentile(one_rms_arr, 75)),
                '90': float(np.percentile(one_rms_arr, 90)),
                '95': float(np.percentile(one_rms_arr, 95)),
                '99': float(np.percentile(one_rms_arr, 99)),
            }
            stats.average_one_rm = Decimal(str(np.mean(one_rms_arr)))
            stats.median_one_rm = Decimal(str(np.median(one_rms_arr)))

        stats.save()


class AllExerciseRankingsView(APIView):
    """
    GET /api/achievements/rankings/
    Get user's ranking for all exercises they have PRs in.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        prs = PersonalRecord.objects.filter(
            user=user,
            best_weight__gt=0
        ).select_related('exercise')

        results = []
        for pr in prs:
            stats, _ = ExerciseStatistics.objects.get_or_create(exercise=pr.exercise)

            weight_pct = stats.get_user_percentile(float(pr.best_weight), 'weight')
            one_rm_pct = stats.get_user_percentile(float(pr.best_one_rep_max), 'one_rm')

            results.append({
                'exercise_id': pr.exercise.id,
                'exercise_name': pr.exercise.name,
                'user_best_weight': pr.best_weight,
                'user_best_one_rm': pr.best_one_rep_max,
                'weight_percentile': weight_pct,
                'one_rm_percentile': one_rm_pct,
                'total_users': stats.total_users
            })

        # Sort by one_rm percentile descending (best rankings first)
        results.sort(key=lambda x: x['one_rm_percentile'] or 0, reverse=True)

        return Response(results)


class LeaderboardView(APIView):
    """
    GET /api/achievements/leaderboard/<exercise_id>/
    Get leaderboard for a specific exercise.
    PRO only feature.

    Query params:
    - limit: Number of entries (default 10)
    - stat: 'weight' or 'one_rm' (default 'one_rm')
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, exercise_id):
        # PRO check
        if not is_pro_user(request.user):
            return get_pro_response()
        
        user = request.user
        limit = int(request.query_params.get('limit', 10))
        stat_type = request.query_params.get('stat', 'one_rm')

        try:
            exercise = Exercise.objects.get(id=exercise_id)
        except Exercise.DoesNotExist:
            return Response(
                {'error': 'Exercise not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get top PRs for this exercise
        order_field = '-best_one_rep_max' if stat_type == 'one_rm' else '-best_weight'
        value_field = 'best_one_rep_max' if stat_type == 'one_rm' else 'best_weight'

        top_prs = PersonalRecord.objects.filter(
            exercise=exercise
        ).filter(**{f'{value_field}__gt': 0}).select_related('user').order_by(order_field)[:limit]

        leaderboard = []
        for rank, pr in enumerate(top_prs, 1):
            value = getattr(pr, value_field)
            leaderboard.append({
                'rank': rank,
                'user_id': pr.user.id,
                'display_name': pr.user.first_name or pr.user.email.split('@')[0],
                'value': value,
                'is_current_user': pr.user.id == user.id
            })

        # Check if current user is in top list
        user_in_list = any(entry['is_current_user'] for entry in leaderboard)

        # If not, add user's entry
        user_entry = None
        if not user_in_list:
            try:
                user_pr = PersonalRecord.objects.get(user=user, exercise=exercise)
                user_value = getattr(user_pr, value_field)

                # Calculate user's rank
                better_count = PersonalRecord.objects.filter(
                    exercise=exercise,
                    **{f'{value_field}__gt': user_value}
                ).count()

                user_entry = {
                    'rank': better_count + 1,
                    'user_id': user.id,
                    'display_name': user.first_name or user.email.split('@')[0],
                    'value': user_value,
                    'is_current_user': True
                }
            except PersonalRecord.DoesNotExist:
                pass

        return Response({
            'exercise_id': exercise_id,
            'exercise_name': exercise.name,
            'stat_type': stat_type,
            'leaderboard': leaderboard,
            'user_entry': user_entry
        })


class RecalculateStatisticsView(APIView):
    """
    POST /api/achievements/recalculate/
    Force recalculation of user statistics and check for new achievements.
    Used after data import or to fix discrepancies.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        with transaction.atomic():
            # Recalculate user statistics
            stats, _ = UserStatistics.objects.get_or_create(user=user)
            self._recalculate_user_stats(user, stats)

            # Recalculate all PRs
            self._recalculate_prs(user)

            # Check for new achievements
            new_achievements = check_all_achievements(user)

        return Response({
            'status': 'ok',
            'new_achievements': len(new_achievements),
            'stats': UserStatisticsSerializer(stats).data
        })

    def _recalculate_user_stats(self, user, stats):
        """Recalculate all user statistics from workout data."""
        from django.db.models import Sum, Count, F

        workouts = Workout.objects.filter(user=user, is_done=True, is_rest_day=False)
        stats.total_workouts = workouts.count()
        stats.total_workout_duration = workouts.aggregate(total=Sum('duration'))['total'] or 0

        sets = ExerciseSet.objects.filter(
            workout_exercise__workout__user=user,
            workout_exercise__workout__is_done=True,
            is_warmup=False
        )

        agg = sets.aggregate(
            total_sets=Count('id'),
            total_reps=Sum('reps'),
            total_volume=Sum(F('weight') * F('reps'))
        )

        stats.total_sets = agg['total_sets'] or 0
        stats.total_reps = agg['total_reps'] or 0
        stats.total_volume = agg['total_volume'] or 0

        stats.total_achievements = UserAchievement.objects.filter(user=user).count()
        stats.total_points = UserAchievement.objects.filter(
            user=user
        ).aggregate(total=Sum('achievement__points'))['total'] or 0

        stats.total_prs = PersonalRecord.objects.filter(user=user).count()

        # Calculate streak
        stats.current_streak = calculate_workout_streak(user)
        if stats.current_streak > stats.longest_streak:
            stats.longest_streak = stats.current_streak

        # Last workout date
        last_workout = workouts.order_by('-datetime').first()
        if last_workout:
            stats.last_workout_date = last_workout.datetime.date()

        stats.save()

    def _recalculate_prs(self, user):
        """Recalculate all personal records from set data."""
        exercises = Exercise.objects.filter(
            workout_exercises__workout__user=user,
            workout_exercises__workout__is_done=True
        ).distinct()

        for exercise in exercises:
            update_personal_record(user, exercise)


# ============== Helper Functions ==============

def calculate_workout_streak(user):
    """Calculate current workout streak in weeks.
    
    A week counts toward the streak if the user worked out at least once that week.
    Streak is broken if more than 1 week passes without any workout.
    """
    from datetime import timedelta

    workouts = Workout.objects.filter(
        user=user,
        is_done=True,
        is_rest_day=False
    ).order_by('-datetime').values_list('datetime', flat=True)

    if not workouts:
        return 0

    # Get all workout dates and convert to week identifiers (year, ISO week)
    workout_weeks = set()
    for workout_datetime in workouts:
        workout_date = workout_datetime.date()
        year, week, _ = workout_date.isocalendar()
        workout_weeks.add((year, week))

    if not workout_weeks:
        return 0

    # Get current week
    today = timezone.now().date()
    current_year, current_week, _ = today.isocalendar()
    current_week_key = (current_year, current_week)

    # Check if there's a workout in current week or last week
    last_week_date = today - timedelta(days=7)
    last_year, last_week, _ = last_week_date.isocalendar()
    last_week_key = (last_year, last_week)

    # If no workout in current or last week, streak is broken
    if current_week_key not in workout_weeks and last_week_key not in workout_weeks:
        return 0

    # Start from current week or last week (whichever has a workout)
    if current_week_key in workout_weeks:
        check_date = today
    else:
        check_date = last_week_date

    # Count consecutive weeks going backward
    streak = 0
    week_date = check_date

    # Go back week by week and check if that week has workouts
    while True:
        year, week, _ = week_date.isocalendar()
        week_key = (year, week)

        if week_key in workout_weeks:
            streak += 1
            # Go back 7 days to check previous week
            week_date = week_date - timedelta(days=7)
            # Safety check to prevent infinite loop (go back max 5 years)
            if (today - week_date).days > 365 * 5:
                break
        else:
            # No workout in this week, streak ends
            break

    return streak


def update_personal_record(user, exercise, weight=None, reps=None, set_date=None):
    """
    Update or create personal record for user/exercise.
    Returns tuple: (PersonalRecord, is_new_pr, pr_type)
    """
    pr, created = PersonalRecord.objects.get_or_create(
        user=user,
        exercise=exercise
    )

    is_new_pr = False
    pr_type = None
    old_value = None
    new_value = None

    if weight is not None and reps is not None:
        set_date = set_date or timezone.now()

        # Check weight PR
        if weight > pr.best_weight:
            old_value = pr.best_weight
            new_value = weight
            pr.best_weight = weight
            pr.best_weight_reps = reps
            pr.best_weight_date = set_date
            is_new_pr = True
            pr_type = 'weight'

        # Check 1RM PR
        one_rm = PersonalRecord.calculate_one_rep_max(weight, reps)
        if one_rm > float(pr.best_one_rep_max):
            if not is_new_pr:
                old_value = pr.best_one_rep_max
                new_value = Decimal(str(one_rm))
            pr.best_one_rep_max = Decimal(str(one_rm))
            pr.best_one_rep_max_weight = weight
            pr.best_one_rep_max_reps = reps
            pr.best_one_rep_max_date = set_date
            if not is_new_pr:
                is_new_pr = True
                pr_type = 'one_rm'

        # Check volume PR
        set_volume = weight * reps
        if set_volume > pr.best_set_volume:
            if not is_new_pr:
                old_value = pr.best_set_volume
                new_value = set_volume
            pr.best_set_volume = set_volume
            pr.best_set_volume_date = set_date
            if not is_new_pr:
                is_new_pr = True
                pr_type = 'volume'

        # Update totals
        pr.total_volume += set_volume
        pr.total_sets += 1
        pr.total_reps += reps

        pr.save()

    return pr, is_new_pr, pr_type, old_value, new_value


def check_all_achievements(user):
    """
    Check all achievements for a user and award any newly earned ones.
    Returns list of newly earned achievements.
    """
    new_achievements = []

    # Get all active achievements the user hasn't earned
    earned_ids = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
    pending_achievements = Achievement.objects.filter(is_active=True).exclude(id__in=earned_ids)

    for achievement in pending_achievements:
        earned, value = check_single_achievement(user, achievement)
        if earned:
            ua = UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                current_progress=achievement.requirement_value,
                earned_value=value
            )
            new_achievements.append(ua)

            # Update user stats
            stats, _ = UserStatistics.objects.get_or_create(user=user)
            stats.total_achievements += 1
            stats.total_points += achievement.points
            stats.save()

    return new_achievements


def check_single_achievement(user, achievement):
    """
    Check if user has earned a specific achievement.
    Returns tuple: (is_earned: bool, earned_value: Decimal or None)
    """
    category = achievement.category
    required = float(achievement.requirement_value)

    if category == 'workout_count':
        count = Workout.objects.filter(user=user, is_done=True, is_rest_day=False).count()
        return count >= required, Decimal(count) if count >= required else None

    elif category == 'workout_streak':
        streak = calculate_workout_streak(user)
        return streak >= required, Decimal(streak) if streak >= required else None

    elif category == 'pr_weight':
        if achievement.exercise:
            pr = PersonalRecord.objects.filter(user=user, exercise=achievement.exercise).first()
            if pr and float(pr.best_weight) >= required:
                return True, pr.best_weight
        return False, None

    elif category == 'pr_one_rep_max':
        if achievement.exercise:
            pr = PersonalRecord.objects.filter(user=user, exercise=achievement.exercise).first()
            if pr and float(pr.best_one_rep_max) >= required:
                return True, pr.best_one_rep_max
        return False, None

    elif category == 'total_volume':
        stats = UserStatistics.objects.filter(user=user).first()
        if stats and float(stats.total_volume) >= required:
            return True, stats.total_volume
        return False, None

    elif category == 'exercise_count':
        count = WorkoutExercise.objects.filter(
            workout__user=user,
            workout__is_done=True
        ).values('exercise').distinct().count()
        return count >= required, Decimal(count) if count >= required else None

    return False, None


def check_achievements_for_workout(user, workout):
    """
    Check achievements that might be triggered by completing a workout.
    Called when a workout is marked as complete.
    """
    new_achievements = []

    # Check workout count achievements
    count_achievements = Achievement.objects.filter(
        category='workout_count',
        is_active=True
    ).exclude(
        id__in=UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
    )

    workout_count = Workout.objects.filter(user=user, is_done=True, is_rest_day=False).count()

    for achievement in count_achievements:
        if workout_count >= float(achievement.requirement_value):
            ua = UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                current_progress=workout_count,
                earned_value=Decimal(workout_count)
            )
            new_achievements.append(ua)

    # Check streak achievements
    streak = calculate_workout_streak(user)
    streak_achievements = Achievement.objects.filter(
        category='workout_streak',
        is_active=True
    ).exclude(
        id__in=UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
    )

    for achievement in streak_achievements:
        if streak >= float(achievement.requirement_value):
            ua = UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                current_progress=streak,
                earned_value=Decimal(streak)
            )
            new_achievements.append(ua)

    # Update user stats
    if new_achievements:
        stats, _ = UserStatistics.objects.get_or_create(user=user)
        stats.total_achievements += len(new_achievements)
        total_points = sum(ua.achievement.points for ua in new_achievements)
        stats.total_points += total_points
        stats.save()

    return new_achievements


def check_achievements_for_pr(user, exercise, pr_value, pr_type='weight'):
    """
    Check PR-based achievements when a new PR is set.
    """
    new_achievements = []

    category = 'pr_weight' if pr_type == 'weight' else 'pr_one_rep_max'

    pr_achievements = Achievement.objects.filter(
        category=category,
        exercise=exercise,
        is_active=True
    ).exclude(
        id__in=UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
    )

    for achievement in pr_achievements:
        if float(pr_value) >= float(achievement.requirement_value):
            ua = UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                current_progress=pr_value,
                earned_value=pr_value
            )
            new_achievements.append(ua)

    # Update user stats
    if new_achievements:
        stats, _ = UserStatistics.objects.get_or_create(user=user)
        stats.total_achievements += len(new_achievements)
        total_points = sum(ua.achievement.points for ua in new_achievements)
        stats.total_points += total_points
        stats.total_prs += 1
        stats.save()

    return new_achievements
