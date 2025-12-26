from django.core.management.base import BaseCommand
from user.models import CustomUser
from workout.models import Workout


class Command(BaseCommand):
    help = 'Recalculate calories for all workouts for a specific user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='irfanemreutkan@outlook.com',
            help='Email of the user'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = CustomUser.objects.get(email=email)
            self.stdout.write(self.style.SUCCESS(f'Found user: {user.email}'))
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
            return

        # Get all workouts for this user
        workouts = Workout.objects.filter(user=user)
        total_workouts = workouts.count()
        
        self.stdout.write(f'Found {total_workouts} workouts for {user.email}')
        
        updated_count = 0
        for workout in workouts:
            try:
                old_calories = workout.calories_burned
                new_calories = workout.calculate_calories()
                
                if old_calories != new_calories:
                    self.stdout.write(
                        f'Workout ID {workout.id} ({workout.title}): '
                        f'{old_calories} -> {new_calories} calories'
                    )
                else:
                    self.stdout.write(
                        f'Workout ID {workout.id} ({workout.title}): '
                        f'{new_calories} calories (unchanged)'
                    )
                
                updated_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error calculating calories for workout {workout.id}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nCompleted! Recalculated calories for {updated_count}/{total_workouts} workouts')
        )


