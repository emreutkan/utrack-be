from django.shortcuts import render
from rest_framework.views import APIView
from .models import Exercise
from .serializers import ExerciseSerializer
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from workout.models import Workout, WorkoutExercise
# Create your views here.

class ExerciseListView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer

    @method_decorator(cache_page(60*15))
    def get(self, request):
        query = request.query_params.get('search', None)
        if query:
            exercises = Exercise.objects.filter(name__icontains=query)
        else:
            exercises = Exercise.objects.all()
        serializer = ExerciseSerializer(exercises, many=True)
        return Response(serializer.data)
        
class addExerciseToWorkoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, workout_id):
        try:
            workout = Workout.objects.get(id=workout_id, user=request.user)
        except Workout.DoesNotExist:
            return Response({'error': 'Workout not found'}, status=status.HTTP_404_NOT_FOUND)
        exercise_id = request.data.get('exercise_id')
        order = request.data.get('order')
        if not order:
            exercises_in_workout = WorkoutExercise.objects.filter(workout=workout).count()
            order = exercises_in_workout + 1
        if not exercise_id:
            return Response({'error': 'exercise_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            exercise = Exercise.objects.get(id=exercise_id)
        except Exercise.DoesNotExist:
             return Response({'error': 'Exercise not found'}, status=status.HTTP_404_NOT_FOUND)

        # Fix: Create a WorkoutExercise object instead of workout.exercises.add()
        WorkoutExercise.objects.create(workout=workout, exercise=exercise, order=order)
        
        return Response(ExerciseSerializer(exercise).data, status=status.HTTP_200_OK)

class UpdateExerciseOrderView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, workout_id):
        try:
            workout = Workout.objects.get(id=workout_id, user=request.user)
        except Workout.DoesNotExist:
            return Response({'error': 'Workout not found'}, status=status.HTTP_404_NOT_FOUND)
        exercises = WorkoutExercise.objects.filter(workout=workout)
        for exercise in exercises:
            exercise.order = exercise.order + 1
            exercise.save()
        return Response(status=status.HTTP_200_OK)

