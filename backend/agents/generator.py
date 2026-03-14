import random
import logging

logger = logging.getLogger(__name__)

try:
    from faker import Faker
    fake = Faker()
except ImportError:
    fake = None
    logger.warning("Faker not installed. DataGeneratorAgent will not work. Install with: pip install faker")


class DataGeneratorAgent:
    """
    Synthetic Data Generator — creates synthetic medical records with
    embedded PII and ground truth labels for benchmarking.

    NOTE: This agent does NOT extend BaseAgent — it uses Python's Faker
    library for deterministic data generation, no LLM calls needed.
    """

    TEMPLATES = [
        # Template 1: Formal admission with SSN
        lambda f: {
            "text": (
                f"Patient {(name := f.name())} (SSN: {(ssn := f.ssn())}) was admitted on "
                f"{(date := f.date())} to {(hospital := f.company())} Hospital in "
                f"{(city := f.city())}, {(state := f.state())}. "
                f"Diagnosis: {(condition := random.choice(['Hypertension', 'Type 2 Diabetes', 'Pneumonia', 'Chronic Kidney Disease', 'Congestive Heart Failure']))}. "
                f"Contact: {(phone := f.phone_number())}. "
                f"Attending physician: Dr. {(doctor := f.name())}."
            ),
            "ground_truth": [
                {"text": name, "type": "PERSON"},
                {"text": ssn, "type": "SSN"},
                {"text": date, "type": "DATE"},
                {"text": city, "type": "LOCATION"},
                {"text": state, "type": "LOCATION"},
                {"text": condition, "type": "CONDITION"},
                {"text": phone, "type": "CONTACT"},
                {"text": doctor, "type": "PERSON"},
            ],
            "qis": {"age": random.randint(20, 85), "zip": f.zipcode()},
            "sensitive": condition,
        },
        # Template 2: Informal clinical note
        lambda f: {
            "text": (
                f"{(name := f.name())}, a {(age := random.randint(25, 80))}-year-old "
                f"from {(city := f.city())}, presented with "
                f"{(condition := random.choice(['severe migraine', 'acute appendicitis', 'atrial fibrillation', 'major depressive disorder', 'rheumatoid arthritis']))}. "
                f"Patient was seen at {(clinic := f.company())} Clinic on {(date := f.date())}. "
                f"Follow-up scheduled with Dr. {(doctor := f.name())}."
            ),
            "ground_truth": [
                {"text": name, "type": "PERSON"},
                {"text": city, "type": "LOCATION"},
                {"text": condition, "type": "CONDITION"},
                {"text": date, "type": "DATE"},
                {"text": doctor, "type": "PERSON"},
            ],
            "qis": {"age": age, "zip": f.zipcode()},
            "sensitive": condition,
        },
        # Template 3: Identity verification
        lambda f: {
            "text": (
                f"Identity verification for {(name := f.name())}. "
                f"SSN: {(ssn := f.ssn())}. Date of Birth: {(dob := f.date_of_birth(minimum_age=18, maximum_age=90).strftime('%m/%d/%Y'))}. "
                f"Diagnosed with {(condition := random.choice(['asthma', 'epilepsy', 'osteoporosis', 'COPD', 'glaucoma']))} "
                f"at {(hospital := f.company())} Medical Center."
            ),
            "ground_truth": [
                {"text": name, "type": "PERSON"},
                {"text": ssn, "type": "SSN"},
                {"text": dob, "type": "DATE"},
                {"text": condition, "type": "CONDITION"},
            ],
            "qis": {"age": random.randint(18, 90), "zip": f.zipcode()},
            "sensitive": condition,
        },
        # Template 4: Referral letter
        lambda f: {
            "text": (
                f"Dear Dr. {(doctor := f.name())},\n\n"
                f"I am referring {(name := f.name())} for evaluation of "
                f"{(condition := random.choice(['suspected lymphoma', 'chronic fatigue syndrome', 'irritable bowel syndrome', 'sleep apnea', 'thyroid dysfunction']))}. "
                f"Patient can be reached at {(phone := f.phone_number())} or "
                f"{(email := f.email())}. "
                f"Please schedule before {(date := f.date())}.\n\n"
                f"Sincerely,\nDr. {(referring := f.name())}"
            ),
            "ground_truth": [
                {"text": doctor, "type": "PERSON"},
                {"text": name, "type": "PERSON"},
                {"text": condition, "type": "CONDITION"},
                {"text": phone, "type": "CONTACT"},
                {"text": email, "type": "CONTACT"},
                {"text": date, "type": "DATE"},
                {"text": referring, "type": "PERSON"},
            ],
            "qis": {"age": random.randint(20, 80), "zip": f.zipcode()},
            "sensitive": condition,
        },
    ]

    def generate(self, n: int = 1) -> list[dict]:
        """
        Generate n synthetic medical records with ground truth PII labels.

        Returns:
            List of dicts, each with: text, ground_truth, qis, sensitive
        """
        if fake is None:
            raise RuntimeError("Faker library not installed. Run: pip install faker")

        records = []
        for _ in range(n):
            template = random.choice(self.TEMPLATES)
            record = template(fake)
            records.append(record)

        logger.info(f"DataGeneratorAgent generated {len(records)} synthetic records")
        return records
