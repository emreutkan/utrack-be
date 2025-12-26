from django.core.management.base import BaseCommand
from workout.models import TrainingResearch
from django.utils import timezone

class Command(BaseCommand):
    help = 'Add body measurement tips to the knowledge base'

    def handle(self, *args, **options):
        # Men's measurement tips
        men_tips = TrainingResearch.objects.create(
            title="Body Measurement Guide - Men (US Navy Method)",
            summary="How to accurately measure your body for US Navy body fat calculation. Proper technique ensures accurate results.",
            content="""For Men - US Navy Body Fat Measurement Guide

Height: Measure barefoot, standing against a wall. Ensure you're standing straight with heels, glutes, and shoulders touching the wall. Use a flat object (like a book) on top of your head, mark the wall, and measure from floor to mark.

Neck: Measure just below the larynx (Adam's apple). The tape should be slightly angled down toward the front. Keep your head straight and shoulders down—do not "flare" your traps. Take measurement at the narrowest point.

Waist: Measure horizontally at the level of your navel (belly button). Critical: Take the measurement after a normal, relaxed exhalation. Do not suck in your stomach or push it out. The tape should be snug but not compressing the skin.

All measurements should be in centimeters (cm) for the US Navy formula.""",
            category='BODY_MEASUREMENTS',
            tags=['body_fat', 'measurements', 'men', 'us_navy', 'body_composition'],
            source_title="US Navy Body Fat Calculator Guidelines",
            source_url="https://www.navy-prt.com/body-fat-calculator/",
            evidence_level='high',
            confidence_score=0.95,
            applicable_muscle_groups=['all'],
            applicable_exercise_types=['all'],
            parameters={
                'required_measurements': ['height', 'weight', 'waist', 'neck'],
                'measurement_units': 'cm',
                'gender': 'male'
            },
            is_active=True,
            is_validated=True,
            priority=10
        )
        
        # Women's measurement tips
        women_tips = TrainingResearch.objects.create(
            title="Body Measurement Guide - Women (US Navy Method)",
            summary="How to accurately measure your body for US Navy body fat calculation. Proper technique ensures accurate results.",
            content="""For Women - US Navy Body Fat Measurement Guide

Height: Measure barefoot, standing against a wall. Ensure you're standing straight with heels, glutes, and shoulders touching the wall. Use a flat object (like a book) on top of your head, mark the wall, and measure from floor to mark.

Neck: Measure just below the larynx. Keep your head straight and shoulders down. Take measurement at the narrowest point.

Waist (Natural Waist): Measure at the narrowest point of the abdomen (usually halfway between the navel and the breastbone). Critical: Take the measurement after a normal, relaxed exhalation. Do not suck in your stomach or push it out.

Hips: Measure at the widest part of the buttocks/glutes. Ensure the tape is perfectly horizontal all the way around. Stand with feet together and measure at the fullest point.

All measurements should be in centimeters (cm) for the US Navy formula.""",
            category='BODY_MEASUREMENTS',
            tags=['body_fat', 'measurements', 'women', 'us_navy', 'body_composition'],
            source_title="US Navy Body Fat Calculator Guidelines",
            source_url="https://www.navy-prt.com/body-fat-calculator/",
            evidence_level='high',
            confidence_score=0.95,
            applicable_muscle_groups=['all'],
            applicable_exercise_types=['all'],
            parameters={
                'required_measurements': ['height', 'weight', 'waist', 'neck', 'hips'],
                'measurement_units': 'cm',
                'gender': 'female'
            },
            is_active=True,
            is_validated=True,
            priority=10
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully added measurement tips to knowledge base')
        )


