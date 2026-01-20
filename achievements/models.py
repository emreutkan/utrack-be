import uuid
from django.db import models
from django.conf import settings
from core.models import TimestampedModel
from exercise.models import Exercise


class Achievement(TimestampedModel):
    """
    Master achievement definitions.
    Achievements can be earned by completing workouts, hitting PRs, etc.
    """

    # Achievement Categories
    CATEGORY_CHOICES = [
        ('workout_count', 'Workout Count'),           # Complete X workouts
        ('workout_streak', 'Workout Streak'),         # X days in a row
        ('pr_weight', 'Personal Record Weight'),      # Lift X kg on exercise
        ('pr_one_rep_max', 'Personal Record 1RM'),    # Achieve X kg 1RM
        ('total_volume', 'Total Volume'),             # Lift X kg total
        ('exercise_count', 'Exercise Count'),         # Do X exercises
        ('muscle_volume', 'Muscle Volume'),           # X sets on muscle group
        ('consistency', 'Consistency'),               # X workouts per week/month
    ]

    # Rarity tiers (affects display/reward)
    RARITY_CHOICES = [
        ('common', 'Common'),           # Easy to achieve
        ('uncommon', 'Uncommon'),       # Moderate effort
        ('rare', 'Rare'),               # Significant effort
        ('epic', 'Epic'),               # Major milestone
        ('legendary', 'Legendary'),     # Elite achievement
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True, help_text="Icon identifier for frontend")

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')

    # Requirement fields
    requirement_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The value needed to earn this achievement (e.g., 100 for '100 workouts', 60 for '60kg bench')"
    )

    # Optional: Link to specific exercise (for PR achievements)
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='achievements',
        help_text="Required for PR-based achievements"
    )

    # Optional: Link to specific muscle group (for muscle volume achievements)
    muscle_group = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Required for muscle-based achievements"
    )

    # Points/XP value (optional gamification)
    points = models.PositiveIntegerField(default=10)

    # Control flags
    is_active = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False, help_text="Hidden achievements are revealed when earned")

    # Ordering for display
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['category', 'order', 'requirement_value']
        verbose_name = 'Achievement'
        verbose_name_plural = 'Achievements'

    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()})"


class UserAchievement(TimestampedModel):
    """
    Tracks which achievements a user has earned.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='achievements'
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='user_achievements'
    )
    earned_at = models.DateTimeField(auto_now_add=True)

    # Progress tracking for partial achievements
    current_progress = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Current progress towards achievement"
    )

    # The value when achievement was earned (for PR achievements)
    earned_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="The actual value when earned (e.g., actual weight lifted)"
    )

    # Track if user has seen the notification
    is_notified = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'achievement')
        ordering = ['-earned_at']
        verbose_name = 'User Achievement'
        verbose_name_plural = 'User Achievements'

    def __str__(self):
        return f"{self.user.email} - {self.achievement.name}"


class PersonalRecord(TimestampedModel):
    """
    Tracks personal records for each user per exercise.
    Updated automatically when a new PR is set.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='personal_records'
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='personal_records'
    )

    # Best weight lifted (regardless of reps)
    best_weight = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    best_weight_reps = models.PositiveIntegerField(default=0, help_text="Reps done at best weight")
    best_weight_date = models.DateTimeField(null=True, blank=True)

    # Best estimated 1RM (calculated using Brzycki formula)
    best_one_rep_max = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    best_one_rep_max_weight = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0,
        help_text="Weight used to calculate best 1RM"
    )
    best_one_rep_max_reps = models.PositiveIntegerField(
        default=0,
        help_text="Reps used to calculate best 1RM"
    )
    best_one_rep_max_date = models.DateTimeField(null=True, blank=True)

    # Best volume in a single set (weight x reps)
    best_set_volume = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    best_set_volume_date = models.DateTimeField(null=True, blank=True)

    # Total lifetime volume for this exercise
    total_volume = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_sets = models.PositiveIntegerField(default=0)
    total_reps = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'exercise')
        ordering = ['exercise__name']
        verbose_name = 'Personal Record'
        verbose_name_plural = 'Personal Records'

    def __str__(self):
        return f"{self.user.email} - {self.exercise.name}: {self.best_weight}kg"

    @staticmethod
    def calculate_one_rep_max(weight, reps):
        """Calculate 1RM using Brzycki formula."""
        if reps <= 0 or weight <= 0:
            return 0
        if reps == 1:
            return float(weight)
        # Brzycki formula: 1RM = weight / (1.0278 - 0.0278 × reps)
        # Only valid for reps <= 10-12, beyond that becomes less accurate
        if reps > 12:
            reps = 12  # Cap for formula accuracy
        return float(weight) / (1.0278 - 0.0278 * reps)


class ExerciseStatistics(TimestampedModel):
    """
    Global statistics for each exercise across all users.
    Used for percentile calculations (e.g., "Top 1% of bench pressers").
    Recalculated periodically.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exercise = models.OneToOneField(
        Exercise,
        on_delete=models.CASCADE,
        related_name='statistics'
    )

    # Total users who have done this exercise
    total_users = models.PositiveIntegerField(default=0)

    # Weight percentiles (stored as JSON for flexibility)
    # Format: {"50": 40.0, "75": 60.0, "90": 80.0, "95": 100.0, "99": 120.0}
    weight_percentiles = models.JSONField(default=dict)

    # 1RM percentiles
    one_rm_percentiles = models.JSONField(default=dict)

    # Volume percentiles (total volume lifted)
    volume_percentiles = models.JSONField(default=dict)

    # Average values
    average_weight = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    average_one_rm = models.DecimalField(max_digits=7, decimal_places=2, default=0)

    # Median values
    median_weight = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    median_one_rm = models.DecimalField(max_digits=7, decimal_places=2, default=0)

    # Last calculation timestamp
    last_calculated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Exercise Statistics'
        verbose_name_plural = 'Exercise Statistics'

    def __str__(self):
        return f"{self.exercise.name} Stats ({self.total_users} users)"

    def get_user_percentile(self, value, stat_type='weight'):
        """
        Get the percentile rank for a given value.
        Returns 0-100 indicating what percentage of users the value beats.
        """
        percentiles = getattr(self, f'{stat_type}_percentiles', {})
        if not percentiles:
            return None

        # Find the percentile bracket
        sorted_percentiles = sorted(
            [(int(k), v) for k, v in percentiles.items()],
            key=lambda x: x[0]
        )

        for percentile, threshold in sorted_percentiles:
            if value < threshold:
                return percentile - 1 if percentile > 0 else 0

        # Value is above all percentiles
        return 99


class UserStatistics(TimestampedModel):
    """
    Aggregated statistics for each user.
    Updated when workouts are completed.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='statistics'
    )

    # Workout stats
    total_workouts = models.PositiveIntegerField(default=0)
    total_workout_duration = models.PositiveIntegerField(default=0, help_text="Total seconds")

    # Volume stats
    total_volume = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_sets = models.PositiveIntegerField(default=0)
    total_reps = models.PositiveIntegerField(default=0)

    # Streak stats
    current_streak = models.PositiveIntegerField(default=0, help_text="Current workout streak in weeks")
    longest_streak = models.PositiveIntegerField(default=0, help_text="Longest workout streak ever (in weeks)")
    last_workout_date = models.DateField(null=True, blank=True)

    # Achievement stats
    total_achievements = models.PositiveIntegerField(default=0)
    total_points = models.PositiveIntegerField(default=0)

    # PR counts
    total_prs = models.PositiveIntegerField(default=0, help_text="Total personal records set")
    prs_this_month = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'User Statistics'
        verbose_name_plural = 'User Statistics'

    def __str__(self):
        return f"{self.user.email} Stats"
