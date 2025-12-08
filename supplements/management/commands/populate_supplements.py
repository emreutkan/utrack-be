from django.core.management.base import BaseCommand
from supplements.models import Supplement

class Command(BaseCommand):
    help = 'Populates the database with comprehensive supplements list'

    def handle(self, *args, **kwargs):
        # 1. Depopulate existing supplements
        self.stdout.write('Clearing existing supplements...')
        deleted_count, _ = Supplement.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing supplements.'))

        # 2. Define new data
        supplements_data = [
            # Magnesium
            {
                "name": "Magnesium Glycinate",
                "description": "Promotes relaxation, sleep, and reduces anxiety. Best for: Insomnia, anxiety, stress relief, correcting deficiency. Least likely to cause a laxative effect.",
                "bioavailability_score": "High (well-absorbed)",
                "dosage_unit": "mg",
                "default_dosage": 200
            },
            {
                "name": "Magnesium Citrate",
                "description": "Natural laxative and general deficiency correction. Best for: Constipation relief, bowel emptying, general magnesium deficiency.",
                "bioavailability_score": "High (well-absorbed)",
                "dosage_unit": "mg",
                "default_dosage": 200
            },
            {
                "name": "Magnesium Oxide",
                "description": "Relief from heartburn and constipation (antacid/laxative). Best for: Temporary constipation and indigestion relief. Not ideal for correcting a long-term deficiency.",
                "bioavailability_score": "Poor (low absorption)",
                "dosage_unit": "mg",
                "default_dosage": 400
            },
            {
                "name": "Magnesium Malate",
                "description": "Energy production and muscle support. Best for: Fatigue, muscle pain/cramps, chronic fatigue syndrome, fibromyalgia support.",
                "bioavailability_score": "High (well-absorbed)",
                "dosage_unit": "mg",
                "default_dosage": 300
            },
            {
                "name": "Magnesium L-Threonate",
                "description": "Brain health, memory, and cognitive function. Best for: Improving memory, cognitive function, and managing certain brain disorders.",
                "bioavailability_score": "Very High (specifically crosses the blood-brain barrier)",
                "dosage_unit": "mg",
                "default_dosage": 144
            },
            {
                "name": "Magnesium Taurate",
                "description": "Supports heart health and blood sugar regulation. Best for: Blood pressure regulation, blood sugar management, and cardiovascular support.",
                "bioavailability_score": "High (well-absorbed)",
                "dosage_unit": "mg",
                "default_dosage": 125
            },
            {
                "name": "Magnesium Chloride",
                "description": "General deficiency and topical application. Best for: General deficiency, muscle soreness (when used in topical oils/lotions or baths).",
                "bioavailability_score": "Good (well-absorbed orally and in topical products)",
                "dosage_unit": "mg",
                "default_dosage": 100
            },
            {
                "name": "Magnesium Sulfate",
                "description": "Muscle relaxation (Epsom Salts) and medical use. Best for: Soaking in baths to soothe sore muscles (Epsom salts). Used clinically for conditions like pre-eclampsia and severe asthma.",
                "bioavailability_score": "Low (through skin), Good (injected/oral)",
                "dosage_unit": "g", 
                "default_dosage": 500
            },
            {
                "name": "Magnesium Lactate",
                "description": "General deficiency, gentle on the stomach. Best for: Correcting deficiency for those with sensitive digestive systems or who need large doses.",
                "bioavailability_score": "High (easily absorbed)",
                "dosage_unit": "mg",
                "default_dosage": 100
            },
            
            # Vitamin B1
            {
                "name": "Vitamin B1 (Thiamine Mononitrate/HCl)",
                "description": "Best For: General B1 deficiency, energy support.",
                "bioavailability_score": "Note: These are the standard, water-soluble forms found in 99% of multivitamins.",
                "dosage_unit": "mg",
                "default_dosage": 100
            },
            {
                "name": "Vitamin B1 (Benfotiamine)",
                "description": "Best For: Nerve health (neuropathy) and diabetes support.",
                "bioavailability_score": "Note: A fat-soluble version. It absorbs better into nerve tissues than standard thiamine.",
                "dosage_unit": "mg",
                "default_dosage": 150
            },
            
            # Vitamin B2
            {
                "name": "Vitamin B2 (Riboflavin)",
                "description": "Best For: General health, migraines, energy.",
                "bioavailability_score": "Note: The standard yellow powder in almost all B-complexes (causes bright yellow urine).",
                "dosage_unit": "mg",
                "default_dosage": 100
            },
            {
                "name": "Vitamin B2 (Riboflavin 5'-Phosphate)",
                "description": "Best For: People with digestive issues or migraines.",
                "bioavailability_score": "Note: The 'active' form. It is 'pre-digested' so your body can use it immediately.",
                "dosage_unit": "mg",
                "default_dosage": 50
            },
            
            # Vitamin B3
            {
                "name": "Vitamin B3 (Nicotinic Acid)",
                "description": "Best For: Cholesterol management (under doctor supervision) and circulation.",
                "bioavailability_score": "Note: Causes 'Niacin Flush' (red, itchy skin) for about 30 minutes. This is normal but uncomfortable.",
                "dosage_unit": "mg",
                "default_dosage": 500
            },
            {
                "name": "Vitamin B3 (Niacinamide)",
                "description": "Best For: Skin health (acne/rosacea) and general B3 status.",
                "bioavailability_score": "Note: No flush. This is the form usually found in multivitamins and skincare.",
                "dosage_unit": "mg",
                "default_dosage": 500
            },
            {
                "name": "Vitamin B3 (Inositol Hexanicotinate)",
                "description": "Best For: People who want the circulatory benefits of Nicotinic Acid without the itch.",
                "bioavailability_score": "Note: A slow-release form that avoids the skin flushing reaction.",
                "dosage_unit": "mg",
                "default_dosage": 500
            },
            
            # Vitamin B5
            {
                "name": "Vitamin B5 (Calcium Pantothenate)",
                "description": "Best For: General stress support, energy, adrenal health.",
                "bioavailability_score": "Note: The standard, stable salt form found in almost every supplement.",
                "dosage_unit": "mg",
                "default_dosage": 500
            },
            {
                "name": "Vitamin B5 (Pantethine)",
                "description": "Best For: Cholesterol support.",
                "bioavailability_score": "Note: A more expensive, active derivative often sold specifically for heart health/lipids.",
                "dosage_unit": "mg",
                "default_dosage": 300
            },
            
            # Vitamin B6
            {
                "name": "Vitamin B6 (Pyridoxine HCl)",
                "description": "Best For: General maintenance, nausea relief.",
                "bioavailability_score": "Note: The cheapest and most common form. Your liver must convert it to be used.",
                "dosage_unit": "mg",
                "default_dosage": 50
            },
            {
                "name": "Vitamin B6 (P-5-P)",
                "description": "Best For: Mood support, morning sickness, PMS.",
                "bioavailability_score": "Note: The active form. Better if you want to avoid potential nerve toxicity from high doses of the HCl form.",
                "dosage_unit": "mg",
                "default_dosage": 50
            },
            
            # Vitamin B7
            {
                "name": "Vitamin B7 (D-Biotin)",
                "description": "Best For: Hair, skin, and nail strength.",
                "bioavailability_score": "Note: 'D-Biotin' is the only biologically active form found in nature and supplements.",
                "dosage_unit": "mcg",
                "default_dosage": 5000
            },
            
            # Vitamin B9
            {
                "name": "Vitamin B9 (Folic Acid)",
                "description": "Best For: General pregnancy prevention (neural tube defects).",
                "bioavailability_score": "Note: Synthetic. Very stable and cheap, but some people (with MTHFR gene) cannot process it well.",
                "dosage_unit": "mcg",
                "default_dosage": 400
            },
            {
                "name": "Vitamin B9 (L-Methylfolate)",
                "description": "Best For: People with MTHFR gene mutation, depression support, pregnancy.",
                "bioavailability_score": "Note: The active form. It bypasses the body's conversion process and goes straight to work. Usually more expensive.",
                "dosage_unit": "mcg",
                "default_dosage": 400
            },
            
            # Vitamin B12
            {
                "name": "Vitamin B12 (Cyanocobalamin)",
                "description": "Best For: General B12 maintenance.",
                "bioavailability_score": "Note: Synthetic. Cheap and stable. The body must remove the tiny cyanide molecule to use it (safe, but extra work for the body).",
                "dosage_unit": "mcg",
                "default_dosage": 1000
            },
            {
                "name": "Vitamin B12 (Methylcobalamin)",
                "description": "Best For: Sleep, nerve health, and energy.",
                "bioavailability_score": "Note: Natural/Active. Often sold as sublingual (under the tongue) drops or lozenges. Better retention in the body.",
                "dosage_unit": "mcg",
                "default_dosage": 1000
            },
            {
                "name": "Vitamin B12 (Adenosylcobalamin)",
                "description": "Best For: Muscle fatigue and cellular energy (mitochondria).",
                "bioavailability_score": "Note: Another active form, often paired with Methylcobalamin in high-end supplements.",
                "dosage_unit": "mcg",
                "default_dosage": 1000
            },

            # Vitamin D
            {
                "name": "Vitamin D3 (Cholecalciferol)",
                "description": "Best For: Raising blood levels. Standard Gold Standard. The form your skin naturally makes from sunlight.",
                "bioavailability_score": "High. Significantly more effective at raising Vitamin D levels than D2.",
                "dosage_unit": "IU",
                "default_dosage": 2000
            },
            {
                "name": "Vitamin D3 (Vegan Cholecalciferol)",
                "description": "Best For: Strict Vegan/Vegetarian. Identical biological activity to standard D3 but 100% plant-based (from Lichen).",
                "bioavailability_score": "High. Matches the efficacy of animal-based D3.",
                "dosage_unit": "IU",
                "default_dosage": 2000
            },
            {
                "name": "Vitamin D2 (Ergocalciferol)",
                "description": "Best For: Medical / Old School use. Often prescribed by doctors for massive weekly doses. Found in fungi/yeast.",
                "bioavailability_score": "Lower. Breaks down faster in the body and is less potent than D3. Generally considered inferior for long-term maintenance.",
                "dosage_unit": "IU",
                "default_dosage": 2000
            },

            # Vitamin C
            {
                "name": "Vitamin C (Ascorbic Acid)",
                "description": "Best For: Short-term immune boosts. Standard / Cheap. The most common pure form. Acidic.",
                "bioavailability_score": "Standard. Water-soluble. Excess is peed out quickly. Can cause heartburn/diarrhea in high doses ('bowel tolerance').",
                "dosage_unit": "mg",
                "default_dosage": 500
            },
            {
                "name": "Vitamin C (Sodium Ascorbate)",
                "description": "Best For: High-dosing (megadosing). Stomach Friendly. Bonded with sodium to neutralize acidity.",
                "bioavailability_score": "Good. Easier on the digestive system than plain Ascorbic Acid.",
                "dosage_unit": "mg",
                "default_dosage": 500
            },
            {
                "name": "Vitamin C (Calcium Ascorbate)",
                "description": "Best For: Gentle / Bone Support. Often sold as 'Ester-C.' Neutralizes acid and provides a small amount of calcium.",
                "bioavailability_score": "Good. Stays in white blood cells slightly longer than plain acid. Very gentle on sensitive stomachs.",
                "dosage_unit": "mg",
                "default_dosage": 500
            },
            {
                "name": "Vitamin C (Liposomal Vitamin C)",
                "description": "Best For: Maximum Absorption. Best for those who need high doses but hate swallowing pills. Encapsulated in tiny fat bubbles.",
                "bioavailability_score": "Very High. Bypasses the digestive destruction. Delivers C directly to cells.",
                "dosage_unit": "mg",
                "default_dosage": 1000
            },
            {
                "name": "Vitamin C (Ascorbyl Palmitate)",
                "description": "Best For: Fat-Soluble Support (skin protection and cognitive health). A unique form that can reach fatty tissues.",
                "bioavailability_score": "Specialized. Unlike all others (which are water-soluble), this is fat-soluble.",
                "dosage_unit": "mg",
                "default_dosage": 250
            },

            # Vitamin K2
            {
                "name": "Vitamin K2 (MK-4 / Menaquinone-4)",
                "description": "Best For: Bone & Tissue Health. Found in animal fats (butter, egg yolks). Good for directing calcium to bones.",
                "bioavailability_score": "Short (Hours). It disappears from the blood very quickly. You generally need to take it 3 times a day to maintain levels.",
                "dosage_unit": "mcg",
                "default_dosage": 45000 # MK-4 is often dosed in high amounts (e.g. 45mg) for therapeutic use, or smaller for general
            },
            {
                "name": "Vitamin K2 (MK-7 / Menaquinone-7)",
                "description": "Best For: Artery & Heart Health. Sourced from fermentation (Natto). The 'Gold Standard' for keeping calcium out of arteries and putting it into bones.",
                "bioavailability_score": "Very High (Days). It stays in your bloodstream for days, building up steady levels with just one dose a day.",
                "dosage_unit": "mcg",
                "default_dosage": 100
            }
        ]

        # 3. Populate new data
        count = 0
        for item in supplements_data:
            obj = Supplement.objects.create(
                name=item['name'],
                description=item['description'],
                bioavailability_score=item['bioavailability_score'],
                dosage_unit=item.get('dosage_unit', 'mg'),
                default_dosage=item.get('default_dosage'),
                is_active=True
            )
            count += 1
            self.stdout.write(self.style.SUCCESS(f'Created: {obj.name}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully populated {count} supplements.'))
