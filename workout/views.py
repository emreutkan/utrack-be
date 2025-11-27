from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import CreateWorkoutSerializer, WorkoutExerciseSerializer
from .models import Workout
from exercise.models import Exercise

# Create your views here.

class CreateWorkoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateWorkoutSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
