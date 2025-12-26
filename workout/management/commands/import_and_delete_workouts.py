import csv
import os
import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from user.models import CustomUser
from workout.models import Workout, WorkoutExercise, ExerciseSet
from exercise.models import Exercise

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class Command(BaseCommand):
    help = 'Import workouts from CSV and add to user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='irfanemreutkan@outlook.com',
            help='Email of the user to add workouts to'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        # Get user
        try:
            user = CustomUser.objects.get(email=email)
            self.stdout.write(self.style.SUCCESS(f'Found user: {user.email}'))
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
            return

        # Read CSV
        csv_path = os.path.join(settings.BASE_DIR, 'asd.csv')
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'CSV file not found: {csv_path}'))
            return

        # Parse workouts from CSV
        workouts_data = self.parse_csv(csv_path)
        self.stdout.write(self.style.SUCCESS(f'Found {len(workouts_data)} workouts in CSV'))

        # Process each workout one by one
        for idx, workout_data in enumerate(workouts_data, 1):
            self.stdout.write(f'\n--- Processing Workout {idx}/{len(workouts_data)}: {workout_data["title"]} ---')
            
            try:
                # Create workout
                workout = self.create_workout(user, workout_data)
                self.stdout.write(self.style.SUCCESS(f'Created workout: {workout.title}'))
                
                # Create exercises and sets
                exercises_created = 0
                sets_created = 0
                
                for exercise_name, sets in workout_data['exercises'].items():
                    # Try to find exercise by name (case-insensitive, partial match)
                    exercise = self.find_exercise(exercise_name)
                    
                    if not exercise:
                        self.stdout.write(self.style.WARNING(f'Exercise not found: {exercise_name}, skipping...'))
                        continue
                    
                    # Create WorkoutExercise
                    workout_exercise = WorkoutExercise.objects.create(
                        workout=workout,
                        exercise=exercise,
                        order=exercises_created
                    )
                    exercises_created += 1
                    
                    # Create sets and track 1RM calculations
                    max_one_rep_max = 0.0
                    
                    for set_num, set_data in enumerate(sets, 1):
                        reps = int(set_data['reps']) if set_data['reps'] else 0
                        weight = float(set_data['weight']) if set_data['weight'] else 0.0
                        
                        ExerciseSet.objects.create(
                            workout_exercise=workout_exercise,
                            set_number=set_num,
                            reps=reps,
                            weight=weight,
                            rest_time_before_set=int(set_data['rest_time']) if set_data['rest_time'] else 0,
                            is_warmup=False,
                            reps_in_reserve=0
                        )
                        sets_created += 1
                        
                        # Calculate 1RM for this set if reps and weight are valid
                        if reps > 0 and weight > 0:
                            one_rep_max = self.calculate_one_rep_max(weight, reps)
                            if one_rep_max > max_one_rep_max:
                                max_one_rep_max = one_rep_max
                    
                    # Update WorkoutExercise with calculated 1RM
                    if max_one_rep_max > 0:
                        workout_exercise.one_rep_max = round(max_one_rep_max, 2)
                        workout_exercise.save()
                
                self.stdout.write(self.style.SUCCESS(f'Created {exercises_created} exercises with {sets_created} sets - Workout ID: {workout.id}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing workout: {str(e)}'))
                import traceback
                traceback.print_exc()
                continue

        self.stdout.write(self.style.SUCCESS(f'\nCompleted processing {len(workouts_data)} workouts'))

    def parse_csv(self, csv_path):
        """Parse CSV and extract workout data"""
        workouts = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        i = 0
        while i < len(rows):
            row = rows[i]
            
            # Check if this is a workout title row
            # Pattern: First column has workout name, other columns are mostly empty
            if row and row[0] and row[0].strip() and \
               (not row[0].startswith('Workout') or 'Workout' in row[0] and ('Evening' in row[0] or 'Morning' in row[0] or 'Afternoon' in row[0])) and \
               row[0] != 'All Sets' and row[0] != 'Exercise' and \
               not row[0].startswith('Total') and not row[0].startswith('Burned'):
                
                workout_title = row[0].strip()
                workout_start = None
                duration_seconds = 0
                exercises_data = {}
                
                # Look ahead for metadata and sets
                j = i + 1
                found_all_sets = False
                
                while j < len(rows):
                    current_row = rows[j]
                    
                    if not current_row:
                        j += 1
                        continue
                    
                    first_col = current_row[0].strip() if current_row[0] else ''
                    
                    # Check for workout start
                    if first_col == 'Workout Start' and len(current_row) > 1 and current_row[1]:
                        try:
                            workout_start = datetime.strptime(current_row[1].strip(), '%Y-%m-%d %H:%M:%S')
                            workout_start = timezone.make_aware(workout_start)
                        except:
                            pass
                    
                    # Check for duration
                    if first_col == 'Total Duration (seconds)' and len(current_row) > 1 and current_row[1]:
                        try:
                            duration_seconds = int(current_row[1].strip())
                        except:
                            pass
                    
                    # Check for "All Sets" - this marks the start of exercise data
                    if first_col == 'All Sets':
                        found_all_sets = True
                        j += 1
                        # Next should be "Exercise,Reps,Weight..." header
                        if j < len(rows) and rows[j][0] == 'Exercise':
                            j += 1
                            # Now read actual sets
                            while j < len(rows):
                                set_row = rows[j]
                                
                                if not set_row or not set_row[0]:
                                    # Empty row - might be end of workout or separator
                                    j += 1
                                    # Check if next non-empty row is a new workout
                                    k = j
                                    while k < len(rows) and (not rows[k] or not rows[k][0]):
                                        k += 1
                                    if k < len(rows) and rows[k][0] and \
                                       (rows[k][0].endswith('Workout') or ('Evening' in rows[k][0] or 'Morning' in rows[k][0] or 'Afternoon' in rows[k][0])):
                                        # Next workout found, break
                                        break
                                    continue
                                
                                first_col_set = set_row[0].strip() if set_row[0] else ''
                                
                                # Stop if we hit a new workout title
                                if first_col_set and (first_col_set.endswith('Workout') or \
                                   ('Evening' in first_col_set or 'Morning' in first_col_set or 'Afternoon' in first_col_set)) and \
                                   first_col_set != 'Exercise':
                                    break
                                
                                # Stop if we hit metadata rows
                                if first_col_set in ['Workout Start', 'Workout End', 'Total Duration', 'Total Sets', 'Burned Calories', 'Total TVL', 'All Sets']:
                                    break
                                
                                # Parse set data (Exercise, Reps, Weight, Rest Time, Note)
                                if len(set_row) >= 3 and first_col_set and first_col_set != 'Exercise':
                                    exercise_name = first_col_set
                                    reps = set_row[1].strip() if len(set_row) > 1 and set_row[1] else '0'
                                    weight = set_row[2].strip() if len(set_row) > 2 and set_row[2] else '0'
                                    rest_time = set_row[3].strip() if len(set_row) > 3 and set_row[3] else '0'
                                    note = set_row[4].strip() if len(set_row) > 4 and set_row[4] else ''
                                    
                                    if exercise_name:
                                        if exercise_name not in exercises_data:
                                            exercises_data[exercise_name] = []
                                        
                                        exercises_data[exercise_name].append({
                                            'reps': reps,
                                            'weight': weight,
                                            'rest_time': rest_time,
                                            'note': note
                                        })
                                
                                j += 1
                        break
                    
                    # If we haven't found "All Sets" yet, keep looking
                    if not found_all_sets:
                        j += 1
                    else:
                        break
                
                # Only add workout if we have exercises
                if exercises_data:
                    workouts.append({
                        'title': workout_title,
                        'workout_start': workout_start,
                        'duration': duration_seconds,
                        'exercises': exercises_data
                    })
                
                # Move to next potential workout (skip to where we left off)
                i = j if found_all_sets else i + 1
            else:
                i += 1
        
        return workouts

    def find_exercise(self, exercise_name):
        """Try to find exercise by name with fuzzy matching, or create if not found"""
        # First try exact match (case-insensitive)
        try:
            return Exercise.objects.get(name__iexact=exercise_name)
        except Exercise.DoesNotExist:
            pass
        except Exercise.MultipleObjectsReturned:
            # If multiple, return first
            return Exercise.objects.filter(name__iexact=exercise_name).first()
        
        # Try partial match
        exercises = Exercise.objects.filter(name__icontains=exercise_name)
        if exercises.exists():
            # Prefer exact word match
            for ex in exercises:
                if ex.name.lower() == exercise_name.lower():
                    return ex
            return exercises.first()
        
        # Exercise not found - create it with smart defaults
        return self.create_exercise_from_name(exercise_name)
    
    def create_exercise_from_name(self, exercise_name):
        """Create an exercise from name with inferred defaults"""
        name_lower = exercise_name.lower()
        
        # Infer equipment type
        equipment_type = 'other'
        if 'cable' in name_lower:
            equipment_type = 'cable'
        elif 'barbell' in name_lower or 'ez-bar' in name_lower or 'ez bar' in name_lower:
            equipment_type = 'barbell'
        elif 'dumbbell' in name_lower:
            equipment_type = 'dumbbell'
        elif 'machine' in name_lower:
            equipment_type = 'machine'
        elif 'bodyweight' in name_lower or 'sit-up' in name_lower or 'leg raise' in name_lower:
            equipment_type = 'bodyweight'
        
        # Infer primary muscle group
        primary_muscle = 'chest'  # default
        if any(x in name_lower for x in ['bicep', 'curl', 'spider']):
            primary_muscle = 'biceps'
        elif any(x in name_lower for x in ['tricep', 'pushdown', 'extension', 'kickback']):
            primary_muscle = 'triceps'
        elif any(x in name_lower for x in ['shoulder', 'press', 'lateral raise', 'rear delt', 'upright row']):
            primary_muscle = 'shoulders'
        elif any(x in name_lower for x in ['chest', 'bench', 'press', 'fly', 'pec']):
            primary_muscle = 'chest'
        elif any(x in name_lower for x in ['lat', 'pulldown', 'row', 'pull down', 'seated row']):
            primary_muscle = 'lats'
        elif any(x in name_lower for x in ['bent over row', 'upright row']):
            primary_muscle = 'lats'
        elif any(x in name_lower for x in ['calf', 'calf raise']):
            primary_muscle = 'calves'
        elif any(x in name_lower for x in ['hamstring', 'leg curl', 'hamstring curl']):
            primary_muscle = 'hamstrings'
        elif any(x in name_lower for x in ['ab', 'crunch', 'sit-up', 'leg raise']):
            primary_muscle = 'abs'
        elif any(x in name_lower for x in ['forearm']):
            primary_muscle = 'forearms'
        
        # Infer category
        category = 'isolation'
        if any(x in name_lower for x in ['press', 'row', 'pulldown', 'deadlift', 'squat']):
            category = 'compound'
        
        # Create the exercise
        exercise = Exercise.objects.create(
            name=exercise_name,
            primary_muscle=primary_muscle,
            equipment_type=equipment_type,
            category=category,
            difficulty_level='intermediate',
            is_active=True
        )
        
        return exercise

    def calculate_one_rep_max(self, weight, reps):
        """
        Calculate 1 rep max using Brzycki formula: weight × (36 / (37 - reps))
        This formula works well for rep ranges 1-10
        For higher reps, we'll use a modified approach
        """
        if reps <= 0 or weight <= 0:
            return 0.0
        
        if reps == 1:
            return float(weight)
        
        if reps <= 10:
            # Brzycki formula (most accurate for 1-10 reps)
            one_rm = weight * (36 / (37 - reps))
        elif reps <= 30:
            # Epley formula for higher reps: weight × (1 + reps/30)
            one_rm = weight * (1 + reps / 30)
        else:
            # For very high reps, use a conservative estimate
            one_rm = weight * (1 + reps / 25)
        
        return float(one_rm)

    def create_workout(self, user, workout_data):
        """Create a workout from workout data"""
        workout = Workout.objects.create(
            user=user,
            title=workout_data['title'],
            datetime=workout_data['workout_start'] or timezone.now(),
            duration=workout_data['duration'],
            intensity='medium',  # Default intensity
            notes='',
            is_done=True
        )
        return workout


