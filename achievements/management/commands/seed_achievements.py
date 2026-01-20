from django.core.management.base import BaseCommand
from achievements.models import Achievement
from exercise.models import Exercise


class Command(BaseCommand):
    help = 'Seeds the database with initial achievements'

    def handle(self, *args, **options):
        self.stdout.write('Seeding achievements...')

        # Workout Count Achievements
        workout_count_achievements = [
            {
                'name': 'First Steps',
                'description': 'Complete your first workout',
                'icon': 'first_workout',
                'category': 'workout_count',
                'rarity': 'common',
                'requirement_value': 1,
                'points': 10,
                'order': 1
            },
            {
                'name': 'Getting Started',
                'description': 'Complete 5 workouts',
                'icon': 'workout_5',
                'category': 'workout_count',
                'rarity': 'common',
                'requirement_value': 5,
                'points': 25,
                'order': 2
            },
            {
                'name': 'Committed',
                'description': 'Complete 10 workouts',
                'icon': 'workout_10',
                'category': 'workout_count',
                'rarity': 'common',
                'requirement_value': 10,
                'points': 50,
                'order': 3
            },
            {
                'name': 'Dedicated',
                'description': 'Complete 25 workouts',
                'icon': 'workout_25',
                'category': 'workout_count',
                'rarity': 'uncommon',
                'requirement_value': 25,
                'points': 100,
                'order': 4
            },
            {
                'name': 'Gym Regular',
                'description': 'Complete 50 workouts',
                'icon': 'workout_50',
                'category': 'workout_count',
                'rarity': 'uncommon',
                'requirement_value': 50,
                'points': 200,
                'order': 5
            },
            {
                'name': 'Century Club',
                'description': 'Complete 100 workouts',
                'icon': 'workout_100',
                'category': 'workout_count',
                'rarity': 'rare',
                'requirement_value': 100,
                'points': 500,
                'order': 6
            },
            {
                'name': 'Iron Dedication',
                'description': 'Complete 250 workouts',
                'icon': 'workout_250',
                'category': 'workout_count',
                'rarity': 'epic',
                'requirement_value': 250,
                'points': 1000,
                'order': 7
            },
            {
                'name': 'Legendary Lifter',
                'description': 'Complete 500 workouts',
                'icon': 'workout_500',
                'category': 'workout_count',
                'rarity': 'legendary',
                'requirement_value': 500,
                'points': 2500,
                'order': 8
            },
            {
                'name': 'Iron Legend',
                'description': 'Complete 1000 workouts',
                'icon': 'workout_1000',
                'category': 'workout_count',
                'rarity': 'legendary',
                'requirement_value': 1000,
                'points': 5000,
                'order': 9
            },
        ]

        # Streak Achievements
        streak_achievements = [
            {
                'name': 'Warm Up',
                'description': 'Work out 2 days in a row',
                'icon': 'streak_2',
                'category': 'workout_streak',
                'rarity': 'common',
                'requirement_value': 2,
                'points': 15,
                'order': 1
            },
            {
                'name': 'Hat Trick',
                'description': 'Work out 3 days in a row',
                'icon': 'streak_3',
                'category': 'workout_streak',
                'rarity': 'common',
                'requirement_value': 3,
                'points': 25,
                'order': 2
            },
            {
                'name': 'Week Warrior',
                'description': 'Work out 7 days in a row',
                'icon': 'streak_7',
                'category': 'workout_streak',
                'rarity': 'uncommon',
                'requirement_value': 7,
                'points': 100,
                'order': 3
            },
            {
                'name': 'Two Week Titan',
                'description': 'Work out 14 days in a row',
                'icon': 'streak_14',
                'category': 'workout_streak',
                'rarity': 'rare',
                'requirement_value': 14,
                'points': 250,
                'order': 4
            },
            {
                'name': 'Monthly Monster',
                'description': 'Work out 30 days in a row',
                'icon': 'streak_30',
                'category': 'workout_streak',
                'rarity': 'epic',
                'requirement_value': 30,
                'points': 750,
                'order': 5
            },
            {
                'name': 'Unstoppable',
                'description': 'Work out 60 days in a row',
                'icon': 'streak_60',
                'category': 'workout_streak',
                'rarity': 'legendary',
                'requirement_value': 60,
                'points': 2000,
                'order': 6
            },
            {
                'name': 'Machine',
                'description': 'Work out 100 days in a row',
                'icon': 'streak_100',
                'category': 'workout_streak',
                'rarity': 'legendary',
                'requirement_value': 100,
                'points': 5000,
                'order': 7
            },
        ]

        # Total Volume Achievements (in kg)
        volume_achievements = [
            {
                'name': 'First Ton',
                'description': 'Lift 1,000 kg total volume',
                'icon': 'volume_1k',
                'category': 'total_volume',
                'rarity': 'common',
                'requirement_value': 1000,
                'points': 15,
                'order': 1
            },
            {
                'name': 'Heavy Lifter',
                'description': 'Lift 10,000 kg total volume',
                'icon': 'volume_10k',
                'category': 'total_volume',
                'rarity': 'common',
                'requirement_value': 10000,
                'points': 50,
                'order': 2
            },
            {
                'name': 'Volume Veteran',
                'description': 'Lift 50,000 kg total volume',
                'icon': 'volume_50k',
                'category': 'total_volume',
                'rarity': 'uncommon',
                'requirement_value': 50000,
                'points': 150,
                'order': 3
            },
            {
                'name': '100K Club',
                'description': 'Lift 100,000 kg total volume',
                'icon': 'volume_100k',
                'category': 'total_volume',
                'rarity': 'rare',
                'requirement_value': 100000,
                'points': 350,
                'order': 4
            },
            {
                'name': 'Quarter Million',
                'description': 'Lift 250,000 kg total volume',
                'icon': 'volume_250k',
                'category': 'total_volume',
                'rarity': 'epic',
                'requirement_value': 250000,
                'points': 750,
                'order': 5
            },
            {
                'name': 'Half Million',
                'description': 'Lift 500,000 kg total volume',
                'icon': 'volume_500k',
                'category': 'total_volume',
                'rarity': 'epic',
                'requirement_value': 500000,
                'points': 1500,
                'order': 6
            },
            {
                'name': 'Million Pound Club',
                'description': 'Lift 1,000,000 kg total volume',
                'icon': 'volume_1m',
                'category': 'total_volume',
                'rarity': 'legendary',
                'requirement_value': 1000000,
                'points': 5000,
                'order': 7
            },
        ]

        # Create non-exercise-specific achievements
        for ach_data in workout_count_achievements + streak_achievements + volume_achievements:
            achievement, created = Achievement.objects.update_or_create(
                name=ach_data['name'],
                defaults=ach_data
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {achievement.name}')

        # PR Achievements for specific exercises (will be created if exercises exist)
        # Define PR milestones for major compound lifts
        pr_exercises = {
            'Bench Press': {
                'milestones': [40, 60, 80, 100, 120, 140, 160, 180, 200, 225],
                'rarities': ['common', 'common', 'uncommon', 'rare', 'rare', 'epic', 'epic', 'legendary', 'legendary', 'legendary'],
            },
            'Barbell Bench Press': {
                'milestones': [40, 60, 80, 100, 120, 140, 160, 180, 200, 225],
                'rarities': ['common', 'common', 'uncommon', 'rare', 'rare', 'epic', 'epic', 'legendary', 'legendary', 'legendary'],
            },
            'Squat': {
                'milestones': [60, 80, 100, 120, 140, 160, 180, 200, 225, 250],
                'rarities': ['common', 'common', 'uncommon', 'rare', 'rare', 'epic', 'epic', 'legendary', 'legendary', 'legendary'],
            },
            'Barbell Squat': {
                'milestones': [60, 80, 100, 120, 140, 160, 180, 200, 225, 250],
                'rarities': ['common', 'common', 'uncommon', 'rare', 'rare', 'epic', 'epic', 'legendary', 'legendary', 'legendary'],
            },
            'Deadlift': {
                'milestones': [60, 100, 120, 140, 160, 180, 200, 225, 250, 300],
                'rarities': ['common', 'common', 'uncommon', 'rare', 'rare', 'epic', 'epic', 'legendary', 'legendary', 'legendary'],
            },
            'Conventional Deadlift': {
                'milestones': [60, 100, 120, 140, 160, 180, 200, 225, 250, 300],
                'rarities': ['common', 'common', 'uncommon', 'rare', 'rare', 'epic', 'epic', 'legendary', 'legendary', 'legendary'],
            },
            'Overhead Press': {
                'milestones': [30, 40, 50, 60, 70, 80, 90, 100, 110, 120],
                'rarities': ['common', 'common', 'uncommon', 'rare', 'rare', 'epic', 'epic', 'legendary', 'legendary', 'legendary'],
            },
            'Barbell Row': {
                'milestones': [40, 60, 80, 100, 120, 140, 160],
                'rarities': ['common', 'common', 'uncommon', 'rare', 'rare', 'epic', 'legendary'],
            },
            'Pull Up': {
                'milestones': [5, 10, 15, 20, 25, 30],
                'rarities': ['common', 'common', 'uncommon', 'rare', 'epic', 'legendary'],
                'is_reps': True
            },
            'Dumbbell Curl': {
                'milestones': [10, 15, 20, 25, 30, 35, 40],
                'rarities': ['common', 'common', 'uncommon', 'rare', 'epic', 'epic', 'legendary'],
            },
            'Lat Pulldown': {
                'milestones': [40, 60, 80, 100, 120, 140],
                'rarities': ['common', 'common', 'uncommon', 'rare', 'epic', 'legendary'],
            },
            'Leg Press': {
                'milestones': [100, 150, 200, 250, 300, 350, 400, 450, 500],
                'rarities': ['common', 'common', 'uncommon', 'rare', 'rare', 'epic', 'epic', 'legendary', 'legendary'],
            },
        }

        # Create PR achievements for existing exercises
        for exercise_name, config in pr_exercises.items():
            try:
                # Try to find the exercise (case-insensitive search)
                exercise = Exercise.objects.filter(name__iexact=exercise_name).first()
                if not exercise:
                    exercise = Exercise.objects.filter(name__icontains=exercise_name).first()

                if exercise:
                    milestones = config['milestones']
                    rarities = config['rarities']
                    is_reps = config.get('is_reps', False)

                    for i, (weight, rarity) in enumerate(zip(milestones, rarities)):
                        unit = 'reps' if is_reps else 'kg'
                        points = {
                            'common': 25,
                            'uncommon': 75,
                            'rare': 200,
                            'epic': 500,
                            'legendary': 1500
                        }[rarity]

                        ach_name = f'{exercise.name} {weight}{unit}'
                        ach_data = {
                            'name': ach_name,
                            'description': f'Lift {weight}{unit} on {exercise.name}',
                            'icon': f'pr_{exercise.name.lower().replace(" ", "_")}_{weight}',
                            'category': 'pr_weight',
                            'rarity': rarity,
                            'requirement_value': weight,
                            'exercise': exercise,
                            'points': points,
                            'order': i + 1
                        }

                        achievement, created = Achievement.objects.update_or_create(
                            name=ach_name,
                            exercise=exercise,
                            defaults=ach_data
                        )
                        status = 'Created' if created else 'Updated'
                        self.stdout.write(f'  {status}: {achievement.name}')
                else:
                    self.stdout.write(self.style.WARNING(f'  Exercise not found: {exercise_name}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error creating PR achievements for {exercise_name}: {e}'))

        total = Achievement.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\nSeeding complete! Total achievements: {total}'))
