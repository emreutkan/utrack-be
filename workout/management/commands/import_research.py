import json
import re
from django.core.management.base import BaseCommand
from workout.models import TrainingResearch
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = 'Import training research articles to the knowledge base'

    def parse_json_field(self, field_value):
        """Parse JSON field, handling escaped quotes"""
        if not field_value or field_value == 'None' or field_value == '[]' or field_value == '{}':
            return [] if '[' in str(field_value) else {}
        
        # Replace double quotes with single quotes for JSON parsing
        try:
            # Handle the case where JSON has double quotes escaped
            field_value = field_value.replace('""', '"')
            return json.loads(field_value)
        except:
            # If parsing fails, try to extract list items manually
            if field_value.startswith('[') and field_value.endswith(']'):
                # Extract items from list string
                items = re.findall(r'"([^"]+)"', field_value)
                return items if items else []
            return [] if '[' in str(field_value) else {}

    def handle(self, *args, **options):
        # Research data - removing duplicates (keeping unique titles)
        research_data = [
            {
                'title': 'Training Volume and Failure Impact on Recovery',
                'summary': 'Training to failure and high volume significantly increase recovery time. Avoiding failure allows faster recovery while maintaining growth stimulus.',
                'content': 'Training to failure leads to significantly higher acute fatigue, muscle damage, and slows recovery of strength in the days after. The failure training group was still not fully recovered at 48 hours, whereas the non-failure group had mostly recovered by 24-48 hours. Higher volume workouts cause more muscle fiber disruption and longer recovery periods.',
                'category': 'INTENSITY_GUIDELINES',
                'tags': ['failure_training', 'volume', 'recovery_time', 'rpe', 'intensity'],
                'source_title': 'Effects of Resistance Training to Muscle Failure on Acute Fatigue',
                'source_url': 'https://pubmed.ncbi.nlm.nih.gov/34881412/',
                'source_authors': [],
                'publication_date': None,
                'evidence_level': 'high',
                'confidence_score': 0.9,
                'applicable_muscle_groups': ['all'],
                'applicable_exercise_types': ['all'],
                'parameters': {'optimal_rpe_range': [7, 9], 'high_volume_threshold': 10, 'excessive_volume_threshold': 15, 'failure_recovery_extension_hours': 24},
                'is_active': True,
                'is_validated': True,
                'priority': 7
            },
            {
                'title': 'Muscle Protein Synthesis Duration',
                'summary': 'Muscle protein synthesis remains elevated for 24-48 hours after resistance training, peaking within the first day and returning to baseline by 36-48 hours.',
                'content': 'After lifting weights, muscle protein synthesis (MPS) rises significantly within 4 hours and peaks at 24 hours post-exercise. After that peak, MPS starts falling off rapidly – by 36 hours post-workout it had nearly returned to baseline levels. In trained individuals, the MPS spike may be shorter-lived (24-36 hours) compared to novices (up to 48 hours).',
                'category': 'PROTEIN_SYNTHESIS',
                'tags': ['protein_synthesis', 'anabolic_window', 'muscle_building', 'training_adaptation'],
                'source_title': 'The time course for elevated muscle protein synthesis following heavy resistance exercise',
                'source_url': 'https://pubmed.ncbi.nlm.nih.gov/8563679/',
                'source_authors': [],
                'publication_date': None,
                'evidence_level': 'high',
                'confidence_score': 0.95,
                'applicable_muscle_groups': ['all'],
                'applicable_exercise_types': ['resistance_training'],
                'parameters': {'peak_synthesis_hours': 24, 'trained_individual_duration': 30, 'untrained_individual_duration': 48, 'protein_synthesis_duration_hours': 36},
                'is_active': True,
                'is_validated': True,
                'priority': 10
            },
            {
                'title': 'Recovery Differences Between Muscle Groups',
                'summary': 'Upper-body muscles recover faster than lower-body muscles. Large compound movements require more recovery than isolation exercises.',
                'content': 'Upper-body muscles (chest, back, shoulders, arms) recovered their strength within ~72 hours and showed performance improvement, whereas lower-body muscles took closer to 96 hours for full recovery and improvement. Multi-joint exercises showed more incomplete recovery at 48 hours compared to single-joint exercises.',
                'category': 'MUSCLE_GROUPS',
                'tags': ['muscle_groups', 'upper_body', 'lower_body', 'compound_vs_isolation'],
                'source_title': 'Resistance Training Recovery: Single Vs. Multi-joint Movements',
                'source_url': 'https://www.researchgate.net/publication/271135793_Resistance_Training_Recovery_Considerations_For_Single_Vs_Multijoint_Movements_And_Upper_Vs_Lower_Body_Muscles',
                'source_authors': [],
                'publication_date': None,
                'evidence_level': 'moderate',
                'confidence_score': 0.8,
                'applicable_muscle_groups': ['chest', 'back', 'shoulders', 'arms', 'quads', 'hamstrings', 'glutes'],
                'applicable_exercise_types': ['compound', 'isolation'],
                'parameters': {'isolation_recovery_hours': 48, 'lower_body_recovery_hours': 96, 'upper_body_recovery_hours': 72, 'compound_recovery_multiplier': 1.2},
                'is_active': True,
                'is_validated': True,
                'priority': 6
            },
            {
                'title': 'Muscle Recovery Time After Weightlifting',
                'summary': 'Most muscle groups need 48-72 hours to recover from intense weightlifting, with larger muscles requiring longer recovery periods.',
                'content': 'After intense weightlifting, muscles generally need about 48–72 hours to recover sufficiently before being trained again. This recovery period allows muscle fibers to repair damage and regain strength. Upper-body muscles generally recovered faster than lower-body ones, with upper-body strength returning to baseline or better by 3 days post-workout, whereas legs took 4 days to fully rebound.',
                'category': 'MUSCLE_RECOVERY',
                'tags': ['recovery', 'rest', 'training_frequency', 'muscle_repair'],
                'source_title': 'Muscle Recovery and Anabolic Window After Weightlifting',
                'source_url': 'https://www.muscleandfitness.com/flexonline/training/be-clock-wise/',
                'source_authors': ['Muscle & Fitness Research'],
                'publication_date': None,
                'evidence_level': 'high',
                'confidence_score': 0.9,
                'applicable_muscle_groups': ['all'],
                'applicable_exercise_types': ['compound', 'isolation'],
                'parameters': {'recovery_time_hours': 48, 'high_volume_threshold': 8, 'high_volume_extra_days': 1, 'lower_body_recovery_hours': 96, 'upper_body_recovery_hours': 72},
                'is_active': True,
                'is_validated': True,
                'priority': 9
            },
            {
                'title': 'Optimal Rest Periods Between Sets',
                'summary': 'Rest periods should be adjusted based on exercise type, intensity, and training goals. Compound movements require longer rest than isolation exercises.',
                'content': 'Rest periods between sets should allow for adequate recovery of strength and energy systems. Heavy compound exercises typically require 2-5 minutes rest, while isolation exercises may only need 1-3 minutes. Insufficient rest can compromise performance and training quality.',
                'category': 'REST_PERIODS',
                'tags': ['rest_periods', 'set_recovery', 'strength', 'performance'],
                'source_title': 'Rest Period Guidelines for Resistance Training',
                'source_url': None,
                'source_authors': [],
                'publication_date': None,
                'evidence_level': 'moderate',
                'confidence_score': 0.75,
                'applicable_muscle_groups': ['all'],
                'applicable_exercise_types': ['compound', 'isolation'],
                'parameters': {'heavy_load_rest_seconds': 240, 'compound_rest_max_seconds': 300, 'compound_rest_min_seconds': 120, 'isolation_rest_max_seconds': 180, 'isolation_rest_min_seconds': 60, 'moderate_load_rest_seconds': 120},
                'is_active': True,
                'is_validated': True,
                'priority': 5
            },
            {
                'title': 'Optimal Training Frequency for Natural Lifters',
                'summary': 'Training each muscle 2-3 times per week is optimal for natural lifters to maximize muscle protein synthesis windows and growth stimulus.',
                'content': "Because natural lifters' muscles only grow for 1-2 days after each session, training each muscle more than once a week is recommended. The anabolic phase post-exercise lasts around 36-48 hours, so waiting a full seven days to train again means spending 5+ days in a baseline state rather than an elevated growth state.",
                'category': 'TRAINING_FREQUENCY',
                'tags': ['frequency', 'natural_training', 'optimization', 'muscle_growth'],
                'source_title': 'Training Frequency for Protein Synthesis and Optimal Muscle Growth',
                'source_url': 'https://www.muscleandstrength.com/articles/protein-synthesis-muscle-growth-training-frequency',
                'source_authors': [],
                'publication_date': None,
                'evidence_level': 'high',
                'confidence_score': 0.85,
                'applicable_muscle_groups': ['all'],
                'applicable_exercise_types': ['all'],
                'parameters': {'optimal_frequency_max': 3, 'optimal_frequency_min': 2, 'max_days_between_sessions': 4, 'protein_synthesis_window_hours': 48},
                'is_active': True,
                'is_validated': True,
                'priority': 8
            }
        ]
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for data in research_data:
            # Check if entry with same title already exists
            existing = TrainingResearch.objects.filter(title=data['title']).first()
            
            if existing:
                self.stdout.write(f"Skipping (already exists): {data['title']}")
                skipped_count += 1
                continue
            
            # Create entry
            TrainingResearch.objects.create(
                title=data['title'],
                summary=data['summary'],
                content=data['content'],
                category=data['category'],
                tags=data['tags'],
                source_title=data['source_title'],
                source_url=data['source_url'],
                source_authors=data['source_authors'],
                publication_date=data['publication_date'],
                evidence_level=data['evidence_level'],
                confidence_score=data['confidence_score'],
                applicable_muscle_groups=data['applicable_muscle_groups'],
                applicable_exercise_types=data['applicable_exercise_types'],
                parameters=data['parameters'],
                is_active=data['is_active'],
                is_validated=data['is_validated'],
                priority=data['priority'],
            )
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Created: {data["title"]}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nImport complete: {created_count} created, {updated_count} updated, {skipped_count} skipped'
        ))


