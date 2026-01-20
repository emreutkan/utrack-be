from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
import logging

from workout.models import Workout, ExerciseSet
from .models import PersonalRecord, UserStatistics, UserAchievement
from .views import (
    update_personal_record,
    check_achievements_for_workout,
    check_achievements_for_pr,
    calculate_workout_streak
)

logger = logging.getLogger('achievements')


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_statistics(sender, instance, created, **kwargs):
    """Create UserStatistics when a new user is created."""
    if created:
        UserStatistics.objects.get_or_create(user=instance)


@receiver(post_save, sender=ExerciseSet)
def track_set_for_pr(sender, instance, created, **kwargs):
    """
    Track personal records when a new set is added.
    Updates PR if the set beats previous records.
    """
    if not created:
        return

    # Skip warmup sets
    if instance.is_warmup:
        return

    workout_exercise = instance.workout_exercise
    if not workout_exercise:
        return

    user = workout_exercise.workout.user
    exercise = workout_exercise.exercise
    weight = instance.weight
    reps = instance.reps

    if weight <= 0 or reps <= 0:
        return

    try:
        # Update personal record
        pr, is_new_pr, pr_type, old_value, new_value = update_personal_record(
            user=user,
            exercise=exercise,
            weight=weight,
            reps=reps,
            set_date=timezone.now()
        )

        if is_new_pr:
            logger.info(
                f"New PR for {user.email} on {exercise.name}: "
                f"{pr_type} - {old_value} -> {new_value}"
            )

            # Check for PR-based achievements
            if pr_type == 'weight':
                check_achievements_for_pr(user, exercise, weight, 'weight')
            elif pr_type == 'one_rm':
                check_achievements_for_pr(user, exercise, pr.best_one_rep_max, 'one_rm')

    except Exception as e:
        logger.error(f"Error tracking PR for set {instance.id}: {e}")


@receiver(pre_save, sender=Workout)
def track_workout_completion(sender, instance, **kwargs):
    """
    Store the previous is_done state before save to detect completion.
    """
    if instance.pk:
        try:
            old_instance = Workout.objects.get(pk=instance.pk)
            instance._was_done = old_instance.is_done
        except Workout.DoesNotExist:
            instance._was_done = False
    else:
        instance._was_done = False


@receiver(post_save, sender=Workout)
def check_workout_achievements(sender, instance, created, **kwargs):
    """
    Check for achievements when a workout is completed.
    Triggered when is_done changes from False to True.
    """
    # Skip rest days
    if instance.is_rest_day:
        return

    # Check if workout was just completed
    was_done = getattr(instance, '_was_done', False)
    if not was_done and instance.is_done:
        user = instance.user

        try:
            # Update user statistics
            stats, _ = UserStatistics.objects.get_or_create(user=user)
            stats.total_workouts += 1

            if instance.duration:
                stats.total_workout_duration += instance.duration

            # Update streak
            stats.current_streak = calculate_workout_streak(user)
            if stats.current_streak > stats.longest_streak:
                stats.longest_streak = stats.current_streak

            stats.last_workout_date = instance.datetime.date() if instance.datetime else timezone.now().date()
            stats.save()

            # Check for achievements
            new_achievements = check_achievements_for_workout(user, instance)

            if new_achievements:
                logger.info(
                    f"User {user.email} earned {len(new_achievements)} new achievements: "
                    f"{[ua.achievement.name for ua in new_achievements]}"
                )

        except Exception as e:
            logger.error(f"Error checking achievements for workout {instance.id}: {e}")
