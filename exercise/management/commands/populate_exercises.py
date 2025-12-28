import json
import os
from django.core.management.base import BaseCommand
from exercise.models import Exercise
from django.conf import settings

class Command(BaseCommand):
    help = 'Populates the database with exercises from exercise_list.json. Checks for new/missing exercises by name and adds them.'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'exercise_list.json')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Get all existing exercise names from database (case-insensitive)
        existing_exercises = {ex.name.lower(): ex for ex in Exercise.objects.all()}
        
        created_count = 0
        updated_count = 0
        
        for item in data:
            exercise_name = item['name']
            exercise_name_lower = exercise_name.lower()
            
            # Check if exercise exists by name (case-insensitive)
            if exercise_name_lower in existing_exercises:
                # Exercise exists, update it
                obj = existing_exercises[exercise_name_lower]
                obj.name = item['name']
                obj.description = item.get('description', '')
                obj.primary_muscle = item['primary_muscle']
                obj.secondary_muscles = item.get('secondary_muscles', [])
                obj.equipment_type = item['equipment_type']
                obj.category = item.get('category', 'compound')
                obj.difficulty_level = item.get('difficulty_level', 'beginner')
                obj.instructions = item.get('instructions', '')
                obj.safety_tips = item.get('safety_tips', '')
                obj.is_active = item.get('is_active', True)
                obj.save()
                updated_count += 1
                self.stdout.write(f'Updated: {obj.name}')
            else:
                # Exercise doesn't exist, create new one
                obj = Exercise.objects.create(
                    name=item['name'],
                    description=item.get('description', ''),
                    primary_muscle=item['primary_muscle'],
                    secondary_muscles=item.get('secondary_muscles', []),
                    equipment_type=item['equipment_type'],
                    category=item.get('category', 'compound'),
                    difficulty_level=item.get('difficulty_level', 'beginner'),
                    instructions=item.get('instructions', ''),
                    safety_tips=item.get('safety_tips', ''),
                    is_active=item.get('is_active', True),
                )
                created_count += 1
                existing_exercises[exercise_name_lower] = obj
                self.stdout.write(self.style.SUCCESS(f'Created: {obj.name}'))

        self.stdout.write(self.style.SUCCESS(
            f'Successfully processed exercises. Created {created_count} new ones, updated {updated_count} existing ones.'
        ))
