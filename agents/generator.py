import random
from faker import Faker
from .base_agent import BaseAgent 

fake = Faker()

class DataGeneratorAgent(BaseAgent):
    def __init__(self):
        pass

    def generate(self):
        """
        Generates a synthetic medical record using Rule-Based Templates.
        Now includes SSNs.
        """
        # 1. Generate Fake Entities
        name = fake.name()
        age = random.randint(18, 90)
        zip_code = fake.zipcode()
        city = fake.city()
        date = fake.date_this_decade().strftime("%Y-%m-%d")
        phone = fake.phone_number()
        email = fake.email()
        ssn = fake.ssn() # <--- NEW: Generate SSN
        
        conditions = [
            "Hypertension", "Type 2 Diabetes", "Acute Bronchitis", "Migraine", 
            "Fractured Tibia", "Influenza", "COVID-19", "Anxiety Disorder",
            "Atrial Fibrillation", "Pneumonia"
        ]
        condition = random.choice(conditions)

        # 2. Select a Random Template (Varying phrasing)
        templates = [
            # Template 1: Formal Admission with SSN
            (f"Patient {name} (SSN: {ssn}) admitted for {condition}. Contact: {phone}.",
             [("PERSON", name), ("SSN", ssn), ("CONDITION", condition), ("CONTACT", phone)]),
            
            # Template 2: Informal Note (No SSN)
            (f"Saw {name} today regarding severe {condition}. Patient is {age} years old and lives in {zip_code}.",
             [("PERSON", name), ("CONDITION", condition), ("LOCATION", zip_code)]),
            
            # Template 3: Identity Verification
            (f"Verify coverage for {name}, ID #{ssn}. Diagnosis: {condition}.",
             [("PERSON", name), ("SSN", ssn), ("CONDITION", condition)]),
             
            # Template 4: Referral
            (f"Please refer {name} to Dr. Smith. Diagnosis: {condition}. Email: {email}.",
             [("PERSON", name), ("CONDITION", condition), ("CONTACT", email)])
        ]

        text, entities = random.choice(templates)

        # 3. Construct Ground Truth Object
        ground_truth = []
        for pii_type, pii_text in entities:
            ground_truth.append({
                "text": pii_text,
                "type": pii_type
            })

        # 4. Return standard JSON format
        return {
            "text": text,
            "ground_truth": ground_truth,
            "qis": {"age": age, "zip": zip_code},
            "sensitive": condition
        }