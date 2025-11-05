from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import CreateWorkoutSerializer, WorkoutExerciseSerializer, ExerciseSetSerializer
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
    def get(self, request):
        workouts = Workout.objects.filter(user=request.user).order_by('-created_at')
        serializer = CreateWorkoutSerializer(workouts, many=True)
        return Response(serializer.data)

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