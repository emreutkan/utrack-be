from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, time, timedelta
from django.db.models import Q, Max, Sum, Count
from django.db import models
from calendar import monthrange
from collections import defaultdict
import logging
from .serializers import CreateWorkoutSerializer, WorkoutExerciseSerializer, ExerciseSetSerializer, GetWorkoutSerializer, UpdateWorkoutSerializer, CreateTemplateWorkoutSerializer, GetTemplateWorkoutSerializer, TrainingResearchSerializer, MuscleRecoverySerializer # Import GetWorkoutSerializer
from .models import Workout, WorkoutExercise, ExerciseSet, TemplateWorkout, TemplateWorkoutExercise, TrainingResearch, MuscleRecovery
from exercise.models import Exercise
from django.core.cache import cache
from django.views.decorators.vary import vary_on_headers
from rest_framework.pagination import PageNumberPagination

# Get logger for this module
logger = logging.getLogger('workout')

def calculate_rest_status(elapsed_seconds, category):
    """
    Calculate rest status based on elapsed time and exercise category.
    Returns status object with text, color, and goals.
    """
    is_compound = category and category.lower() == 'compound'
    
    # Thresholds in seconds
    phase1_limit = 90 if is_compound else 60  # Red light limit
    phase2_limit = 180 if is_compound else 90  # Yellow light limit
    
    if elapsed_seconds < phase1_limit:
        return {
            "text": "Rest",
            "color": "#FF3B30",
            "goal": phase1_limit,
            "max_goal": phase2_limit
        }
    elif elapsed_seconds < phase2_limit:
        return {
            "text": "Recharging...",
            "color": "#FF9F0A",
            "goal": phase2_limit,
            "max_goal": phase2_limit
        }
    else:
        return {
            "text": "Ready to Go!",
            "color": "#34C759",
            "goal": phase2_limit,
            "max_goal": phase2_limit
        }

def calculate_one_rep_max(weight, reps):
    """
    Calculate 1RM using Brzycki formula.
    Formula: 1RM = weight / (1.0278 - 0.0278 × reps)
    """
    if reps <= 0 or weight <= 0:
        return None
    
    # Brzycki formula
    denominator = 1.0278 - (0.0278 * reps)
    if denominator <= 0:
        return None
    
    one_rm = float(weight) / denominator
    return round(one_rm, 2)

def calculate_workout_calories(workout):
    """
    Calculate total calories burned for a workout using MET method.
    Delegates to the workout model's calculate_calories method.
    
    Returns: Total calories burned (float)
    """
    return workout.calculate_calories()

def recalculate_workout_metrics(workout):
    """
    Recalculate calories and muscle recovery for a completed workout.
    Only runs if workout is done and not a rest day.
    Also recalculates if workout was completed in the last 4 days (for editing scenarios).
    """
    if workout.is_done and not workout.is_rest_day:
        # Check if workout was done in the last 4 days
        workout_datetime = workout.datetime or workout.created_at
        time_diff = timezone.now() - workout_datetime
        days_since_workout = time_diff.days
        
        # Recalculate if workout is done and within last 4 days (96 hours)
        # This handles editing scenarios where workout was done recently
        if days_since_workout <= 4 and time_diff.total_seconds() >= 0:
            # Recalculate calories
            calories_burned = calculate_workout_calories(workout)
            workout.calories_burned = calories_burned
            workout.save(update_fields=['calories_burned'])
            
            # Recalculate muscle recovery
            workout.calculate_muscle_recovery()

def calculate_workout_exercise_1rm(workout_exercise):
    """
    Calculate 1RM for a workout exercise.
    Gets all non-warmup sets, calculates 1RM for each, returns the highest.
    """
    # Get all non-warmup sets for this exercise
    sets = ExerciseSet.objects.filter(
        workout_exercise=workout_exercise,
        is_warmup=False
    ).exclude(weight=0).exclude(reps=0)
    
    if not sets.exists():
        return None
    
    # Calculate 1RM for each set and find the maximum
    max_1rm = None
    for exercise_set in sets:
        one_rm = calculate_one_rep_max(exercise_set.weight, exercise_set.reps)
        if one_rm is not None:
            if max_1rm is None or one_rm > max_1rm:
                max_1rm = one_rm
    
    return max_1rm

def get_rest_timer_state(workout):
    """
    Get rest timer state for active workout.
    Returns last set timestamp and exercise category.
    """
    if not workout or workout.is_done:
        return {
            "last_set_timestamp": None,
            "last_exercise_category": None,
            "elapsed_seconds": 0
        }
    
    # Find the most recent set across all exercises in the workout
    last_set = ExerciseSet.objects.filter(
        workout_exercise__workout=workout
    ).select_related(
        'workout_exercise',
        'workout_exercise__exercise'
    ).order_by('-created_at', '-id').first()
    
    if not last_set:
        return {
            "last_set_timestamp": None,
            "last_exercise_category": None,
            "elapsed_seconds": 0
        }
    
    # Get the exercise category from the workout exercise
    exercise = last_set.workout_exercise.exercise
    category = exercise.category if exercise and exercise.category else 'isolation'
    
    # Calculate elapsed time
    now = timezone.now()
    elapsed_seconds = int((now - last_set.created_at).total_seconds())
    
    # Determine rest status
    rest_status = calculate_rest_status(elapsed_seconds, category)
    
    return {
        "last_set_timestamp": last_set.created_at.isoformat(),
        "last_exercise_category": category,
        "elapsed_seconds": elapsed_seconds,
        "rest_status": rest_status
    }

# Create your views here.

class CreateWorkoutView(APIView):
    permission_classes = [IsAuthenticated]
   
    def post(self, request):
        active_workout = Workout.objects.filter(user=request.user, is_done=False).first()
        
        # Check if new workout is a rest day (rest days are automatically set as is_done=True)
        is_rest_day = request.data.get('is_rest_day', False)
        
        # Check if new workout is being created as active (is_done: false or not set)
        new_workout_is_done = request.data.get('is_done', False)  # Defaults to False if not provided
        
        # Parse workout date to check for rest day conflicts
        workout_datetime_str = request.data.get('workout_date') or request.data.get('date')
        workout_date = None
        
        if workout_datetime_str:
            try:
                # Parse the datetime (handle ISO datetime string)
                if 'T' in workout_datetime_str:
                    # Handle ISO format with Z (UTC) or timezone
                    if workout_datetime_str.endswith('Z'):
                        workout_datetime = datetime.fromisoformat(workout_datetime_str.replace('Z', '+00:00'))
                    else:
                        workout_datetime = datetime.fromisoformat(workout_datetime_str)
                    
                    # Make timezone-aware if needed
                    if timezone.is_naive(workout_datetime):
                        workout_datetime = timezone.make_aware(workout_datetime)
                    workout_date = workout_datetime.date()
                else:
                    # Try parsing as date only
                    from django.utils.dateparse import parse_date
                    workout_date = parse_date(workout_datetime_str)
            except (ValueError, TypeError):
                pass
        else:
            # No date provided = current date
            workout_date = timezone.now().date()
        
        # Check for rest day conflicts
        if workout_date:
            # If creating a rest day, check if any workout exists for that date
            if is_rest_day:
                existing_workout = Workout.objects.filter(
                    user=request.user,
                    datetime__date=workout_date
                ).first()
                
                if existing_workout:
                    return Response({
                        'error': 'WORKOUT_EXISTS_FOR_DATE',
                        'message': f'A workout already exists for {workout_date}. Cannot create a rest day for this date.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # If creating a regular workout, check if a rest day exists for that date
            else:
                existing_rest_day = Workout.objects.filter(
                    user=request.user,
                    datetime__date=workout_date,
                    is_rest_day=True
                ).first()
                
                if existing_rest_day:
                    return Response({
                        'error': 'REST_DAY_EXISTS_FOR_DATE',
                        'message': f'A rest day already exists for {workout_date}. Cannot create a workout for this date.'
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Allow rest days even if there's an active workout (they're automatically completed)
        if active_workout and not new_workout_is_done and not is_rest_day:
            # Block creating a new active workout if one already exists
            return Response({
                'error': 'ACTIVE_WORKOUT_EXISTS',
                'active_workout': active_workout.id,
                'message': 'Cannot create a new active workout. Complete or delete the existing active workout first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if active_workout and new_workout_is_done and not is_rest_day:
            # If creating a completed workout (not rest day), check datetime to ensure it's not after active workout
            if workout_date:
                try:
                    # Convert date back to datetime for comparison
                    workout_datetime = timezone.make_aware(datetime.combine(workout_date, time.min))
                    
                    # Get active workout's datetime (use datetime field, fallback to created_at)
                    active_workout_datetime = getattr(active_workout, 'datetime', active_workout.created_at)
                    
                    # Block if new workout datetime is after active workout's datetime
                    if workout_datetime and workout_datetime > active_workout_datetime:
                        return Response({
                            'error': 'ACTIVE_WORKOUT_EXISTS',
                            'active_workout': active_workout.id,
                            'message': f'Cannot create workout at {workout_datetime} after active workout at {active_workout_datetime}'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError) as e:
                    # If datetime parsing fails, allow it (completed workout)
                    pass
                
        serializer = CreateWorkoutSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WorkoutPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class GetWorkoutView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = WorkoutPagination
    
    def get(self, request, workout_id=None):
        if workout_id:
            # Get specific workout with optimized queries
            try:
                workout = Workout.objects.select_related('user').prefetch_related(
                    'workoutexercise_set__exercise',
                    'workoutexercise_set__sets'
                ).get(id=workout_id, user=request.user)
                serializer = GetWorkoutSerializer(workout)
                logger.info(f"User {request.user.email} retrieved workout {workout_id}")
                return Response(serializer.data)
            except Workout.DoesNotExist:
                logger.warning(f"User {request.user.email} attempted to access non-existent workout {workout_id}")
                return Response({'error': 'Workout not found'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error retrieving workout {workout_id} for user {request.user.email}: {str(e)}", exc_info=True)
                return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Get pagination params
            page = int(request.query_params.get('page', 1))
            page_size = request.query_params.get('page_size', 20)
            
            # Only cache first page (most common case) to limit memory usage
            # 200 users = 200 cache entries max instead of 200+ per page
            should_cache = page == 1
            
            if should_cache:
                cache_key = f'workouts_list_user_{request.user.id}_page_1_size_{page_size}'
                cached_response = cache.get(cache_key)
                if cached_response is not None:
                    return Response(cached_response)
            
            # Get all workouts with pagination and optimized queries (including rest days)
            workouts = Workout.objects.filter(
                user=request.user, 
                is_done=True
            ).select_related('user').prefetch_related(
                'workoutexercise_set__exercise',
                'workoutexercise_set__sets'
            ).order_by('-created_at')
            
            # Paginate
            paginator = self.pagination_class()
            paginated_workouts = paginator.paginate_queryset(workouts, request)
            serializer = GetWorkoutSerializer(paginated_workouts, many=True)
            paginated_response = paginator.get_paginated_response(serializer.data)
            
            # Only cache first page to limit memory usage
            if should_cache:
                cache.set(cache_key, paginated_response.data, 300)  # 5 minutes
            
            return paginated_response
        


class GetActiveWorkoutView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        active_workout = Workout.objects.filter(user=request.user, is_done=False).first()
        if active_workout:
            serializer = GetWorkoutSerializer(active_workout)
            return Response(serializer.data)
        return Response({'error': 'No active workout found'}, status=status.HTTP_404_NOT_FOUND)

class AddExerciseToWorkoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, workout_id):
        # Check if workout exists and belongs to user
        try:
            workout = Workout.objects.get(id=workout_id, user=request.user)
        except Workout.DoesNotExist:
            return Response({'error': 'Workout not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get exercise_id from request data
        exercise_id = request.data.get('exercise_id')
        if not exercise_id:
            return Response({'error': 'exercise_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify exercise exists
        try:
            exercise = Exercise.objects.get(id=exercise_id)
        except Exercise.DoesNotExist:
            return Response({'error': 'Exercise not found'}, status=status.HTTP_404_NOT_FOUND)

        # Create WorkoutExercise
        # Auto-calculate order: count existing exercises + 1
        current_count = workout.workoutexercise_set.count()
        
        data = {
            'workout': workout.id,
            'exercise': exercise.id,
            'order': current_count + 1
        }
        
        serializer = WorkoutExerciseSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddExerciseSetToWorkoutExerciseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, workout_exercise_id):

        try:
            workout_exercise = WorkoutExercise.objects.get(id=workout_exercise_id, workout__user=request.user)

        except WorkoutExercise.DoesNotExist:
            return Response({'error': 'Workout exercise not found'}, status=status.HTTP_404_NOT_FOUND)

        current_sets = workout_exercise.sets.count()
        set_number = current_sets + 1

        data = request.data.copy()
        data['workout_exercise'] = workout_exercise.id ## we grab the workout exercise id from the reqest header  POST /api/workout/exercise/5/add_set/
        data['set_number'] = set_number
        
        serializer = ExerciseSetSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            
            # Recalculate recovery if workout is completed
            workout = workout_exercise.workout
            recalculate_workout_metrics(workout)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateExerciseSetView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, set_id):
        try:
            # Ensure the set belongs to a workout owned by the user
            exercise_set = ExerciseSet.objects.get(id=set_id, workout_exercise__workout__user=request.user)
            
            serializer = ExerciseSetSerializer(exercise_set, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                
                # Recalculate recovery if workout is completed
                workout = exercise_set.workout_exercise.workout
                recalculate_workout_metrics(workout)
                
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ExerciseSet.DoesNotExist:
            return Response({'error': 'Set not found'}, status=status.HTTP_404_NOT_FOUND)

class DeleteExerciseSetView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, set_id):
        try:
            # Ensure the set belongs to a workout owned by the user
            exercise_set = ExerciseSet.objects.get(id=set_id, workout_exercise__workout__user=request.user)
            workout = exercise_set.workout_exercise.workout
            exercise_set.delete()
            
            # Recalculate recovery if workout is completed
            recalculate_workout_metrics(workout)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ExerciseSet.DoesNotExist:
            return Response({'error': 'Set not found'}, status=status.HTTP_404_NOT_FOUND)

class DeleteWorkoutExerciseView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, workout_exercise_id):
        try:
            # Ensure the workout exercise belongs to a workout owned by the user
            workout_exercise = WorkoutExercise.objects.get(id=workout_exercise_id, workout__user=request.user)
            workout_exercise_order = workout_exercise.order
            current_workout = workout_exercise.workout
            workout_exercise.delete()

            ## for all exercises in THIS workout that have order greater than the deleted exercise's order, we need to decrement the order by 1
            for exercise in WorkoutExercise.objects.filter(workout=current_workout, order__gt=workout_exercise_order):
                exercise.order = exercise.order - 1
                exercise.save()
            
            # Recalculate recovery if workout is completed
            recalculate_workout_metrics(current_workout)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except WorkoutExercise.DoesNotExist:
            return Response({'error': 'Exercise not found in workout'}, status=status.HTTP_404_NOT_FOUND)

class UpdateExerciseOrderView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, workout_id):
        try:
            workout = Workout.objects.get(id=workout_id, user=request.user)
            
            # Expecting a list of {id: 1, order: 2} where id is the WorkoutExercise ID
            exercise_orders = request.data.get('exercise_orders', [])
            
            for item in exercise_orders:
                try:
                    # Using workout_exercise_id to identify the specific exercise instance in this workout
                    workout_exercise = WorkoutExercise.objects.get(id=item['id'], workout=workout)
                    workout_exercise.order = item['order']
                    workout_exercise.save()
                except WorkoutExercise.DoesNotExist:
                    continue # Skip if ID is wrong or belongs to another workout
                
            return Response(status=status.HTTP_200_OK)
        except Workout.DoesNotExist:
            return Response({'error': 'Workout not found'}, status=status.HTTP_404_NOT_FOUND)

class CompleteWorkoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, workout_id):
        try:
            workout = Workout.objects.get(id=workout_id, user=request.user)
            
            if workout.is_done:
                return Response({'error': 'Workout is already completed'}, status=status.HTTP_400_BAD_REQUEST)
                
            # Update fields if provided
            update_fields = ['is_done']
            
            if 'duration' in request.data:
                try:
                    workout.duration = int(request.data['duration'])
                    update_fields.append('duration')
                except (ValueError, TypeError):
                    return Response({'error': 'Duration must be an integer (seconds)'}, status=status.HTTP_400_BAD_REQUEST)

            if 'intensity' in request.data:
                workout.intensity = request.data['intensity']
                update_fields.append('intensity')
            if 'notes' in request.data:
                workout.notes = request.data['notes']
                update_fields.append('notes')

            workout.is_done = True
            workout.save(update_fields=update_fields)
            
            # Calculate 1RM for all exercises in the workout
            workout_exercises = WorkoutExercise.objects.filter(workout=workout)
            for workout_exercise in workout_exercises:
                one_rm = calculate_workout_exercise_1rm(workout_exercise)
                if one_rm is not None:
                    workout_exercise.one_rep_max = one_rm
                    workout_exercise.save()
            
            # Calculate calories and recovery
            recalculate_workout_metrics(workout)

            return Response(GetWorkoutSerializer(workout).data, status=status.HTTP_200_OK)
        except Workout.DoesNotExist:
            return Response({'error': 'Workout not found'}, status=status.HTTP_404_NOT_FOUND)

class UpdateWorkoutView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, workout_id):
        try:
            workout = Workout.objects.get(id=workout_id, user=request.user)
            
            # If updating datetime, check for conflicts with active workout
            if 'date' in request.data and not workout.is_done:
                # If making an active workout into a past workout, check for conflicts
                workout_datetime_str = request.data.get('date')
                if workout_datetime_str:
                    try:
                        if 'T' in workout_datetime_str:
                            if workout_datetime_str.endswith('Z'):
                                new_datetime = datetime.fromisoformat(workout_datetime_str.replace('Z', '+00:00'))
                            else:
                                new_datetime = datetime.fromisoformat(workout_datetime_str)
                            if timezone.is_naive(new_datetime):
                                new_datetime = timezone.make_aware(new_datetime)
                        else:
                            from django.utils.dateparse import parse_date
                            workout_date = parse_date(workout_datetime_str)
                            if workout_date:
                                new_datetime = timezone.make_aware(datetime.combine(workout_date, time.min))
                            else:
                                raise ValueError("Invalid date format")
                        
                        # Check if new datetime conflicts with rest day
                        new_date = new_datetime.date()
                        existing_rest_day = Workout.objects.filter(
                            user=request.user,
                            datetime__date=new_date,
                            is_rest_day=True
                        ).exclude(id=workout_id).first()
                        
                        if existing_rest_day:
                            return Response({
                                'error': 'REST_DAY_EXISTS_FOR_DATE',
                                'message': f'A rest day already exists for {new_date}. Cannot update workout to this date.'
                            }, status=status.HTTP_400_BAD_REQUEST)
                    except (ValueError, TypeError):
                        pass
            
            serializer = UpdateWorkoutSerializer(workout, data=request.data, partial=True)
            if serializer.is_valid():
                updated_workout = serializer.save()
                
                # Recalculate calories and recovery if workout is completed
                recalculate_workout_metrics(updated_workout)
                
                return Response(GetWorkoutSerializer(updated_workout).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Workout.DoesNotExist:
            return Response({'error': 'Workout not found'}, status=status.HTTP_404_NOT_FOUND)

class DeleteWorkoutView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, workout_id):
        try:
            workout = Workout.objects.get(id=workout_id, user=request.user)
            workout.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Workout.DoesNotExist:
            return Response({'error': 'Workout not found'}, status=status.HTTP_404_NOT_FOUND)

class CalendarView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/workout/calendar/
        Returns calendar data with workouts marked by date.
        Query params: year, month, week (optional)
        """
        year = request.query_params.get('year')
        month = request.query_params.get('month', None)
        week = request.query_params.get('week', None)
        
        # Default to current year/month if not provided
        if not year:
            year = timezone.now().year
        if not month:
            month = timezone.now().month
        
        try:
            year = int(year)
            month = int(month) if month else None
            week = int(week) if week else None
        except ValueError:
            return Response({'error': 'Invalid year/month/week format'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Build date range based on view type
        if week and month and year:
            # Week view - calculate week start from month start
            month_start = datetime(year, month, 1).date()
            # Find first Monday of the month or before
            days_since_monday = month_start.weekday()
            first_monday = month_start - timedelta(days=days_since_monday)
            # Calculate the week start (week 1, 2, 3, 4, etc.)
            week_start = first_monday + timedelta(weeks=week-1)
            week_end = week_start + timedelta(days=6)
            date_range = (week_start, week_end)
        elif month and year:
            # Month view
            start_date = datetime(year, month, 1).date()
            last_day = monthrange(year, month)[1]
            end_date = datetime(year, month, last_day).date()
            date_range = (start_date, end_date)
        elif year:
            # Year view
            start_date = datetime(year, 1, 1).date()
            end_date = datetime(year, 12, 31).date()
            date_range = (start_date, end_date)
        else:
            return Response({'error': 'Invalid parameters'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all workouts in date range
        workouts = Workout.objects.filter(
            user=request.user,
            datetime__date__gte=date_range[0],
            datetime__date__lte=date_range[1]
        ).order_by('datetime')
        
        # Build calendar data as array for easier frontend consumption
        calendar_data = []
        current_date = date_range[0]
        while current_date <= date_range[1]:
            date_str = current_date.isoformat()
            day_workouts = workouts.filter(datetime__date=current_date)
            
            has_workout = day_workouts.filter(is_rest_day=False, is_done=True).exists()
            is_rest_day = day_workouts.filter(is_rest_day=True).exists()
            
            calendar_data.append({
                'date': date_str,
                'day': current_date.day,
                'weekday': current_date.weekday(),  # 0=Monday, 6=Sunday
                'has_workout': has_workout,
                'is_rest_day': is_rest_day,
                'workout_count': day_workouts.filter(is_rest_day=False, is_done=True).count(),
                'rest_day_count': day_workouts.filter(is_rest_day=True).count()
            })
            current_date += timedelta(days=1)
        
        return Response({
            'calendar': calendar_data,
            'period': {
                'year': year,
                'month': month,
                'week': week,
                'start_date': date_range[0].isoformat(),
                'end_date': date_range[1].isoformat()
            }
        })

class GetAvailableYearsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/workout/years/
        Returns list of years that have workouts.
        """
        years = Workout.objects.filter(
            user=request.user
        ).values_list('datetime__year', flat=True).distinct().order_by('-datetime__year')
        
        return Response({'years': list(years)})

class CalendarStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/workout/calendar/stats/
        Returns stats for a given period.
        Query params: year (required), month (optional), week (optional)
        """
        year = request.query_params.get('year')
        month = request.query_params.get('month', None)
        week = request.query_params.get('week', None)
        
        if not year:
            return Response({'error': 'Year is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            year = int(year)
            month = int(month) if month else None
            week = int(week) if week else None
        except ValueError:
            return Response({'error': 'Invalid year/month/week format'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Build date range
        if week and month:
            # Week view - calculate week start from month start
            month_start = datetime(year, month, 1).date()
            days_since_monday = month_start.weekday()
            first_monday = month_start - timedelta(days=days_since_monday)
            week_start = first_monday + timedelta(weeks=week-1)
            week_end = week_start + timedelta(days=6)
            date_range = (week_start, week_end)
            total_days = 7
        elif month:
            # Month view
            start_date = datetime(year, month, 1).date()
            last_day = monthrange(year, month)[1]
            end_date = datetime(year, month, last_day).date()
            date_range = (start_date, end_date)
            total_days = last_day
        else:
            # Year view
            start_date = datetime(year, 1, 1).date()
            end_date = datetime(year, 12, 31).date()
            date_range = (start_date, end_date)
            total_days = 365 if year % 4 != 0 else 366  # Handle leap year
        
        # Get stats
        workouts = Workout.objects.filter(
            user=request.user,
            datetime__date__gte=date_range[0],
            datetime__date__lte=date_range[1]
        )
        
        total_workouts = workouts.filter(is_rest_day=False, is_done=True).count()
        total_rest_days = workouts.filter(is_rest_day=True).count()
        
        # Count unique days with workouts (excluding rest days)
        days_with_workouts = workouts.filter(
            is_rest_day=False,
            is_done=True
        ).values_list('datetime__date', flat=True).distinct().count()
        
        days_not_worked = total_days - days_with_workouts - total_rest_days
        
        return Response({
            'total_workouts': total_workouts,
            'total_rest_days': total_rest_days,
            'days_not_worked': max(0, days_not_worked),  # Ensure non-negative
            'total_days': total_days,
            'period': {
                'year': year,
                'month': month,
                'week': week,
                'start_date': date_range[0].isoformat(),
                'end_date': date_range[1].isoformat()
            }
        })

class TotalWorkoutsPerformedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        total_workouts = Workout.objects.filter(user=request.user, is_done=True).count()
                ## get how many days past since the first workout was performed
        first_workout = Workout.objects.filter(user=request.user, is_done=True).order_by('created_at').first()
        if first_workout:
            days_past = (timezone.now() - first_workout.created_at).days
            weeks_past = days_past / 7
        else:
            days_past = 1
            weeks_past = 1
        ## get the average number of workouts per day
        average_workouts_per_week = total_workouts / weeks_past
        ## get how many days has past in this year 
        days_past_in_year = (timezone.now().date() - datetime(timezone.now().year, 1, 1).date()).days
        ## get how many workouts have been performed in this year
        workouts_performed_in_year = Workout.objects.filter(user=request.user, is_done=True, datetime__year=timezone.now().year).count()
        ## get the amount of days that user did not perform a workout
        days_not_performed_a_workout = days_past_in_year - workouts_performed_in_year
        return Response(
            {'total_workouts': total_workouts,
             'days_past': days_past,
             'weeks_past': weeks_past,
             'average_workouts_per_week': average_workouts_per_week,
             'days_not_performed_a_workout': days_not_performed_a_workout,
             'workouts_performed_in_year': workouts_performed_in_year,
             'days_past_in_year': days_past_in_year})

class CheckWorkoutPerformedTodayView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Check if a workout was performed today.
        
        Returns:
        - If active workout exists (is_done=False): Active workout info (any date)
        - If rest day: Rest day info
        - If workout performed: Workout details
        - If nothing: No workout performed today
        """
        # First check for ANY active workout in the system (not just today)
        active_workout = Workout.objects.filter(
            user=request.user,
            is_done=False
        ).first()
        
        if active_workout:
            return Response({
                'workout_performed': False,
                'active_workout': True
            }, status=status.HTTP_200_OK)
        
        today = timezone.now().date()
        
        # Check for any workout today (completed or not)
        today_workouts = Workout.objects.filter(
            user=request.user,
            datetime__date=today
        ).order_by('-datetime')
        
        if not today_workouts.exists():
            return Response({
                'workout_performed': False,
                'date': today.isoformat(),
                'message': 'No workout performed today'
            }, status=status.HTTP_200_OK)
        
        # Check for completed workouts (rest day or regular workout)
        completed_workout = today_workouts.filter(is_done=True).first()
        
        if completed_workout:
            if completed_workout.is_rest_day:
                return Response({
                    'workout_performed': True,
                    'is_rest': True
                }, status=status.HTTP_200_OK)
            else:
                # Regular workout performed
                workout_data = GetWorkoutSerializer(completed_workout).data
                return Response({
                    'workout_performed': True,
                    'is_rest_day': False,
                    'date': today.isoformat(),
                    'workout': workout_data,
                    'message': 'Workout performed today'
                }, status=status.HTTP_200_OK)
        
        # Fallback (shouldn't reach here)
        return Response({
            'workout_performed': False,
            'date': today.isoformat(),
            'message': 'No workout performed today'
        }, status=status.HTTP_200_OK)

class CreateTemplateWorkoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateTemplateWorkoutSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            template_workout = serializer.save()
            # Return with calculated muscle groups
            response_serializer = GetTemplateWorkoutSerializer(template_workout)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetTemplateWorkoutsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        template_workouts = TemplateWorkout.objects.filter(user=request.user).order_by('-created_at')
        serializer = GetTemplateWorkoutSerializer(template_workouts, many=True)
        return Response(serializer.data)

class StartTemplateWorkoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        template_workout_id = request.data.get('template_workout_id')
        
        if not template_workout_id:
            return Response({'error': 'template_workout_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            template_workout = TemplateWorkout.objects.get(id=template_workout_id, user=request.user)
        except TemplateWorkout.DoesNotExist:
            return Response({'error': 'Template workout not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if there's already an active workout
        active_workout = Workout.objects.filter(user=request.user, is_done=False).first()
        if active_workout:
            return Response({
                'error': 'ACTIVE_WORKOUT_EXISTS',
                'active_workout': active_workout.id,
                'message': 'Cannot start a new workout. Complete or delete the existing active workout first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new active workout
        workout = Workout.objects.create(
            user=request.user,
            title=template_workout.title,
            is_done=False,
            notes=template_workout.notes  # Copy notes from template
        )
        
        # Add exercises from template to workout
        template_exercises = TemplateWorkoutExercise.objects.filter(
            template_workout=template_workout
        ).order_by('order')
        
        for template_exercise in template_exercises:
            WorkoutExercise.objects.create(
                workout=workout,
                exercise=template_exercise.exercise,
                order=template_exercise.order
            )
        
        # Return the created workout
        serializer = GetWorkoutSerializer(workout)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class GetRestTimerStateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/workout/active/rest-timer/
        Returns rest timer state for user's active workout.
        """
        try:
            # Get active workout
            workout = Workout.objects.filter(
                user=request.user,
                is_done=False
            ).first()
            
            if not workout:
                return Response({
                    "last_set_timestamp": None,
                    "last_exercise_category": None,
                    "elapsed_seconds": 0
                })
            
            # Get rest timer state
            state = get_rest_timer_state(workout)
            return Response(state)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetExercise1RMHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, exercise_id):
        """
        GET /api/workout/exercise/<exercise_id>/1rm-history/
        Returns 1RM history for a specific exercise across all workouts.
        """
        try:
            # Verify exercise exists
            exercise = Exercise.objects.get(id=exercise_id)
        except Exercise.DoesNotExist:
            return Response({'error': 'Exercise not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get all workout exercises for this exercise, only from completed workouts
        workout_exercises = WorkoutExercise.objects.filter(
            exercise_id=exercise_id,
            workout__user=request.user,
            workout__is_done=True,
            one_rep_max__isnull=False
        ).select_related('workout').order_by('-workout__datetime')
        
        history = []
        for workout_exercise in workout_exercises:
            history.append({
                'workout_id': workout_exercise.workout.id,
                'workout_title': workout_exercise.workout.title,
                'workout_date': workout_exercise.workout.datetime.isoformat(),
                'one_rep_max': float(workout_exercise.one_rep_max) if workout_exercise.one_rep_max else None
            })
        
        return Response({
            'exercise_id': exercise_id,
            'exercise_name': exercise.name,
            'history': history,
            'total_workouts': len(history)
        })

class GetRecoveryRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/workout/recommendations/recovery/
        Returns recovery recommendations based on user's last workout.
        """
        # Get last completed workout
        last_workout = Workout.objects.filter(
            user=request.user,
            is_done=True,
            is_rest_day=False
        ).order_by('-datetime').first()
        
        if not last_workout:
            return Response({
                'message': 'No completed workouts found',
                'recommendations': []
            })
        
        # Get muscle groups worked in last workout
        workout_exercises = WorkoutExercise.objects.filter(workout=last_workout).select_related('exercise')
        muscle_groups = set()
        exercise_types = set()
        
        for we in workout_exercises:
            if we.exercise.primary_muscle:
                muscle_groups.add(we.exercise.primary_muscle)
            if we.exercise.category:
                exercise_types.add(we.exercise.category)
        
        # Find relevant research
        research_items = TrainingResearch.objects.filter(
            is_active=True,
            category__in=['MUSCLE_RECOVERY', 'MUSCLE_GROUPS', 'PROTEIN_SYNTHESIS']
        )
        
        recommendations = []
        for research in research_items:
            # Check if applicable to user's workout
            applicable = False
            if 'all' in research.applicable_muscle_groups:
                applicable = True
            elif any(mg in research.applicable_muscle_groups for mg in muscle_groups):
                applicable = True
            
            if applicable:
                params = research.parameters or {}
                recommendations.append({
                    'title': research.title,
                    'summary': research.summary,
                    'category': research.category,
                    'confidence_score': float(research.confidence_score),
                    'parameters': params,
                    'source_url': research.source_url
                })
        
        # Calculate recommended recovery time
        hours_since_workout = (timezone.now() - last_workout.datetime).total_seconds() / 3600
        
        # Get recovery time from research
        recovery_hours = 48  # Default
        for rec in recommendations:
            if 'recovery_time_hours' in rec.get('parameters', {}):
                recovery_hours = rec['parameters']['recovery_time_hours']
                break
        
        return Response({
            'last_workout_id': last_workout.id,
            'last_workout_date': last_workout.datetime.isoformat(),
            'hours_since_workout': round(hours_since_workout, 1),
            'muscle_groups_worked': sorted(list(muscle_groups)),
            'recommended_recovery_hours': recovery_hours,
            'is_recovered': hours_since_workout >= recovery_hours,
            'recommendations': sorted(recommendations, key=lambda x: x['confidence_score'], reverse=True)
        })

class GetRestPeriodRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, workout_exercise_id):
        """
        GET /api/workout/exercise/<workout_exercise_id>/rest-recommendations/
        Returns recommended rest periods for an exercise based on research.
        """
        try:
            workout_exercise = WorkoutExercise.objects.get(
                id=workout_exercise_id,
                workout__user=request.user
            )
        except WorkoutExercise.DoesNotExist:
            return Response({'error': 'Workout exercise not found'}, status=status.HTTP_404_NOT_FOUND)
        
        exercise = workout_exercise.exercise
        is_compound = exercise.category == 'compound'
        
        # Get rest period research
        research = TrainingResearch.objects.filter(
            is_active=True,
            category='REST_PERIODS',
            is_validated=True
        ).first()
        
        if research and research.parameters:
            params = research.parameters
            if is_compound:
                min_rest = params.get('compound_rest_min_seconds', 120)
                max_rest = params.get('compound_rest_max_seconds', 300)
            else:
                min_rest = params.get('isolation_rest_min_seconds', 60)
                max_rest = params.get('isolation_rest_max_seconds', 180)
        else:
            # Defaults
            if is_compound:
                min_rest = 120
                max_rest = 300
            else:
                min_rest = 60
                max_rest = 180
        
        return Response({
            'exercise_id': exercise.id,
            'exercise_name': exercise.name,
            'exercise_type': exercise.category,
            'recommended_rest_seconds': {
                'min': min_rest,
                'max': max_rest,
                'optimal': (min_rest + max_rest) // 2
            },
            'research_source': research.source_url if research else None
        })

class GetTrainingFrequencyRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/workout/recommendations/frequency/
        Returns training frequency recommendations based on research.
        """
        # Get research on training frequency
        research = TrainingResearch.objects.filter(
            is_active=True,
            category='TRAINING_FREQUENCY',
            is_validated=True
        ).order_by('-priority', '-confidence_score').first()
        
        if research and research.parameters:
            params = research.parameters
            recommendations = {
                'optimal_frequency_per_week': {
                    'min': params.get('optimal_frequency_min', 2),
                    'max': params.get('optimal_frequency_max', 3)
                },
                'max_days_between_sessions': params.get('max_days_between_sessions', 4),
                'protein_synthesis_window_hours': params.get('protein_synthesis_window_hours', 48),
                'research_title': research.title,
                'research_summary': research.summary,
                'source_url': research.source_url
            }
        else:
            recommendations = {
                'optimal_frequency_per_week': {'min': 2, 'max': 3},
                'max_days_between_sessions': 4,
                'protein_synthesis_window_hours': 48,
                'research_title': None,
                'research_summary': None,
                'source_url': None
            }
        
        return Response(recommendations)

class GetRelevantResearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/workout/research/
        Returns relevant research articles based on query params.
        Query params: category, muscle_group, exercise_type, tags
        """
        category = request.query_params.get('category', None)
        muscle_group = request.query_params.get('muscle_group', None)
        exercise_type = request.query_params.get('exercise_type', None)
        tags = request.query_params.getlist('tags', [])
        
        research = TrainingResearch.objects.filter(is_active=True)
        
        if category:
            research = research.filter(category=category)
        
        if muscle_group:
            research = research.filter(
                models.Q(applicable_muscle_groups__contains=[muscle_group]) |
                models.Q(applicable_muscle_groups__contains=['all'])
            )
        
        if exercise_type:
            research = research.filter(
                models.Q(applicable_exercise_types__contains=[exercise_type]) |
                models.Q(applicable_exercise_types__contains=['all'])
            )
        
        if tags:
            for tag in tags:
                research = research.filter(tags__contains=[tag])
        
        serializer = TrainingResearchSerializer(research.order_by('-priority', '-confidence_score'), many=True)
        return Response(serializer.data)

class GetMuscleRecoveryStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get current recovery status for all muscle groups.
        Returns the most recent recovery record for each muscle group.
        """
        # Get all unique muscle groups
        from exercise.models import Exercise
        all_muscle_groups = [choice[0] for choice in Exercise.MUSCLE_GROUPS]
        
        # Get the most recent recovery record for each muscle group
        recovery_status = {}
        
        # SQLite-compatible approach: fetch all records, order by datetime, then group in Python
        all_records = MuscleRecovery.objects.filter(
            user=request.user,
            muscle_group__in=all_muscle_groups
        ).select_related('source_workout').order_by(
            'muscle_group',
            '-source_workout__datetime',
            '-recovery_until'
        )
        
        # Group by muscle_group and take the first (most recent) for each
        seen_groups = set()
        recovery_records = []
        for record in all_records:
            if record.muscle_group not in seen_groups:
                recovery_records.append(record)
                seen_groups.add(record.muscle_group)

        for record in recovery_records:
            # Update recovery status
            record.update_recovery_status()
            recovery_status[record.muscle_group] = MuscleRecoverySerializer(record).data
        
        return Response({
            'recovery_status': recovery_status,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)

class VolumeAnalysisView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/workout/volume-analysis/
        Analyzes volume per muscle group per week.
        
        Query params:
        - weeks_back (optional): Number of weeks to analyze (default: 12)
        - start_date (optional): Start date in YYYY-MM-DD format
        - end_date (optional): End date in YYYY-MM-DD format
        """
        # Get query parameters
        weeks_back = request.query_params.get('weeks_back', 12)
        start_date_param = request.query_params.get('start_date', None)
        end_date_param = request.query_params.get('end_date', None)
        
        try:
            weeks_back = int(weeks_back)
        except ValueError:
            weeks_back = 12
        
        # Calculate date range
        if start_date_param and end_date_param:
            try:
                start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Default to last N weeks
            end_date = timezone.now().date()
            # Get Monday of the current week
            days_since_monday = end_date.weekday()
            current_monday = end_date - timedelta(days=days_since_monday)
            # Go back N weeks from current Monday
            start_date = current_monday - timedelta(weeks=weeks_back)
        
        # Get all completed workouts in date range (excluding rest days)
        workouts = Workout.objects.filter(
            user=request.user,
            is_done=True,
            is_rest_day=False,
            datetime__date__gte=start_date,
            datetime__date__lte=end_date
        ).select_related().prefetch_related(
            'workoutexercise_set__exercise',
            'workoutexercise_set__sets'
        ).order_by('datetime')
        
        # Dictionary to store volume data: {week_start: {muscle_group: {volume, sets, workouts}}}
        volume_data = defaultdict(lambda: defaultdict(lambda: {'total_volume': 0.0, 'sets': 0, 'workouts': set()}))
        
        # Get all muscle groups
        from exercise.models import Exercise
        all_muscle_groups = [choice[0] for choice in Exercise.MUSCLE_GROUPS]
        
        # Process each workout
        for workout in workouts:
            workout_date = workout.datetime.date() if workout.datetime else workout.created_at.date()
            
            # Calculate Monday of the week for this workout
            days_since_monday = workout_date.weekday()
            week_monday = workout_date - timedelta(days=days_since_monday)
            week_key = week_monday.isoformat()
            
            # Process each exercise in the workout
            for workout_exercise in workout.workoutexercise_set.all():
                exercise = workout_exercise.exercise
                sets = workout_exercise.sets.all()
                
                # Process each set
                for exercise_set in sets:
                    # Skip warmup sets
                    if exercise_set.is_warmup:
                        continue
                    
                    # Calculate volume (weight × reps)
                    weight = float(exercise_set.weight) if exercise_set.weight else 0.0
                    reps = exercise_set.reps if exercise_set.reps else 0
                    
                    if weight > 0 and reps > 0:
                        volume = weight * reps
                        
                        # Add to primary muscle
                        primary_muscle = exercise.primary_muscle
                        if primary_muscle:
                            volume_data[week_key][primary_muscle]['total_volume'] += volume
                            volume_data[week_key][primary_muscle]['sets'] += 1
                            volume_data[week_key][primary_muscle]['workouts'].add(workout.id)
                        
                        # Add to secondary muscles (40% of volume)
                        secondary_muscles = exercise.secondary_muscles or []
                        for secondary_muscle in secondary_muscles:
                            if secondary_muscle:
                                volume_data[week_key][secondary_muscle]['total_volume'] += volume * 0.4
                                volume_data[week_key][secondary_muscle]['sets'] += 1
                                volume_data[week_key][secondary_muscle]['workouts'].add(workout.id)
        
        # Convert to response format
        weeks_list = []
        for week_start_str in sorted(volume_data.keys()):
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            week_end = week_start + timedelta(days=6)
            
            muscle_groups_data = {}
            for muscle_group in all_muscle_groups:
                if muscle_group in volume_data[week_start_str]:
                    data = volume_data[week_start_str][muscle_group]
                    muscle_groups_data[muscle_group] = {
                        'total_volume': round(data['total_volume'], 2),
                        'sets': data['sets'],
                        'workouts': len(data['workouts'])
                    }
                else:
                    muscle_groups_data[muscle_group] = {
                        'total_volume': 0.0,
                        'sets': 0,
                        'workouts': 0
                    }
            
            weeks_list.append({
                'week_start': week_start_str,
                'week_end': week_end.isoformat(),
                'muscle_groups': muscle_groups_data
            })
        
        # Calculate summary statistics
        summary = {}
        for muscle_group in all_muscle_groups:
            volumes = []
            total_sets = 0
            total_workouts = 0
            
            for week_data in weeks_list:
                mg_data = week_data['muscle_groups'][muscle_group]
                if mg_data['total_volume'] > 0:
                    volumes.append(mg_data['total_volume'])
                    total_sets += mg_data['sets']
                    total_workouts += mg_data['workouts']
            
            if volumes:
                summary[muscle_group] = {
                    'average_volume_per_week': round(sum(volumes) / len(volumes), 2),
                    'max_volume_per_week': round(max(volumes), 2),
                    'min_volume_per_week': round(min(volumes), 2),
                    'total_weeks_trained': len(volumes),
                    'total_sets': total_sets,
                    'total_workouts': total_workouts
                }
            else:
                summary[muscle_group] = {
                    'average_volume_per_week': 0.0,
                    'max_volume_per_week': 0.0,
                    'min_volume_per_week': 0.0,
                    'total_weeks_trained': 0,
                    'total_sets': 0,
                    'total_workouts': 0
                }
        
        return Response({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_weeks': len(weeks_list)
            },
            'weeks': weeks_list,
            'summary': summary
        }, status=status.HTTP_200_OK)

    