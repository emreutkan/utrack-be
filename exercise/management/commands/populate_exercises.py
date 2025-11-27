import json
import os
from django.core.management.base import BaseCommand
from exercise.models import Exercise
from django.conf import settings

class Command(BaseCommand):
    help = 'Populates the database with exercises from exercise_list.json'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'exercise_list.json')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        with open(file_path, 'r') as f:
            data = json.load(f)

        count = 0
        for index, item in enumerate(data, start=1):
            # update_or_create checks 'id' and updates fields if exists, or creates new
            # We explicitly set the ID to the loop counter (1, 2, 3...)
            
            obj, created = Exercise.objects.update_or_create(
                id=index, 
                defaults={
                    'name': item['name'],
                    'description': item.get('description', ''),
                    'primary_muscle': item['primary_muscle'],
                    'secondary_muscles': item.get('secondary_muscles', []),
                    'equipment_type': item['equipment_type'],
                    'category': item.get('category', 'compound'),
                    'difficulty_level': item.get('difficulty_level', 'beginner'),
                    'instructions': item.get('instructions', ''),
                    'safety_tips': item.get('safety_tips', ''),
                    'is_active': item.get('is_active', True),
                }
            )
            
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Created [{index}]: {obj.name}'))
            else:
                self.stdout.write(f'Updated [{index}]: {obj.name}')

        self.stdout.write(self.style.SUCCESS(f'Successfully processed exercises. Created {count} new ones.'))
