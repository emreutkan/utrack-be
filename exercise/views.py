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
from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination

class ExercisePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200

class ExerciseListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ExercisePagination
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer

    def get(self, request):
        query = request.query_params.get('search', None)
        cache_key = f'exercises_list_{query or "all"}'
        
        # Cache globally (same for all users) - exercises don't change per user
        exercises_data = cache.get(cache_key)
        if exercises_data is None:
            if query:
                exercises = Exercise.objects.filter(name__icontains=query, is_active=True)
            else:
                exercises = Exercise.objects.filter(is_active=True)
            serializer = ExerciseSerializer(exercises, many=True)
            exercises_data = serializer.data
            cache.set(cache_key, exercises_data, 60*60)  # 1 hour cache
        
        return Response(exercises_data)
        
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

