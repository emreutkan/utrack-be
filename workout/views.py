from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import CreateWorkoutSerializer, WorkoutExerciseSerializer, ExerciseSetSerializer, GetWorkoutSerializer # Import GetWorkoutSerializer
from .models import Workout, WorkoutExercise, ExerciseSet
from exercise.models import Exercise

# Create your views here.

class CreateWorkoutView(APIView):
    permission_classes = [IsAuthenticated]
   
    def post(self, request):
        # Change this line to .first() instead of .exists()
        active_workout = Workout.objects.filter(user=request.user, is_done=False).first()
        
        if active_workout:
            return Response({
                'error': 'ACTIVE_WORKOUT_EXISTS',
                'active_workout': active_workout.id
                }, status=status.HTTP_400_BAD_REQUEST)
                
        serializer = CreateWorkoutSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetWorkoutView(APIView):

    permission_classes = [IsAuthenticated]
    def get(self, request, workout_id):
        workout = Workout.objects.get(id=workout_id, user=request.user)
        serializer = GetWorkoutSerializer(workout)
        return Response(serializer.data)
    def get(self, request):
        workouts = Workout.objects.filter(user=request.user).order_by('-created_at')
        serializer = GetWorkoutSerializer(workouts, many=True) # Use GetWorkoutSerializer here
        return Response(serializer.data)
        


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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteExerciseSetView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, set_id):
        try:
            # Ensure the set belongs to a workout owned by the user
            exercise_set = ExerciseSet.objects.get(id=set_id, workout_exercise__workout__user=request.user)
            exercise_set.delete()
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
            workout_exercise.delete()

            ## for all workouts that have order greater than the deleted exercise's order, we need to decrement the order by 1
            for workout in Workout.objects.all():
                for exercise in WorkoutExercise.objects.filter(workout=workout, order__gt=workout_exercise_order):
                    exercise.order = exercise.order - 1
                    exercise.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except WorkoutExercise.DoesNotExist:
            return Response({'error': 'Exercise not found in workout'}, status=status.HTTP_404_NOT_FOUND)
