from django.urls import path
from .views import (
    CreateBodyMeasurementView,
    GetBodyMeasurementsView,
    CalculateBodyFatMenView,
    CalculateBodyFatWomenView
)

urlpatterns = [
    path('', GetBodyMeasurementsView.as_view(), name='list-measurements'),
    path('create/', CreateBodyMeasurementView.as_view(), name='create-measurement'),
    path('calculate-body-fat/men/', CalculateBodyFatMenView.as_view(), name='calculate-body-fat-men'),
    path('calculate-body-fat/women/', CalculateBodyFatWomenView.as_view(), name='calculate-body-fat-women'),
]


