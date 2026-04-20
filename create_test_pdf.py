"""
Creates a sample test PDF containing realistic medical record text
with a mix of all 6 PII categories for testing DocSentry.
Run: python create_test_pdf.py
Requires: pip install reportlab
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

SAMPLE_TEXT = """
NORTHVIEW GENERAL HOSPITAL
Patient Clinical Summary Report
Department of Internal Medicine

Patient Name: Sarah Elizabeth Thornton
Date of Birth: March 14, 1982
SSN: 487-92-1065
Medical Record Number: NVH-2024-00842
Admission Date: January 7, 2025
Treating Physician: Dr. Marcus Delroy Webb

Address: 2847 Maple Creek Drive, Austin, TX 78701
Phone: (512) 884-3920
Email: sarah.thornton@gmail.com

---

CHIEF COMPLAINT & HISTORY OF PRESENT ILLNESS:

Ms. Sarah Thornton is a 42-year-old female patient presenting with a 3-week history
of progressively worsening chest pain, shortness of breath on exertion, and bilateral
ankle edema. Patient has a known history of Congestive Heart Failure (CHF) and
Type 2 Diabetes Mellitus, diagnosed in 2019 and 2021 respectively.

She was seen in the Emergency Department on January 5, 2025 by Dr. Priya Nair
(Contact: 512-774-0011) before being transferred to the general ward for monitoring.

PAST MEDICAL HISTORY:
- Congestive Heart Failure (CHF) - Stage B, diagnosed April 2019
- Type 2 Diabetes Mellitus, HbA1c 8.4%, diagnosed July 2021
- Hypertension, on lisinopril 10mg daily, since 2018
- Mild Chronic Kidney Disease (Stage 2), eGFR 68 mL/min

SOCIAL HISTORY:
Patient resides in Austin, Texas. Employed as a nurse at St. David's Medical Center,
1025 E 32nd St, Austin TX 78705. Emergency contact: James Thornton (husband),
phone: (512) 334-8821.

CURRENT MEDICATIONS:
1. Furosemide 40mg oral daily (loop diuretic for fluid retention)
2. Lisinopril 10mg oral daily (ACE inhibitor for hypertension)
3. Metformin 1000mg oral twice daily (diabetes management)
4. Carvedilol 6.25mg oral twice daily (beta-blocker for CHF)

DIAGNOSTIC RESULTS:
- CBC: Hemoglobin 11.2 g/dL (mild anemia)
- BMP: Sodium 138 mEq/L, Potassium 4.1 mEq/L, Creatinine 1.4 mg/dL
- BNP: 845 pg/mL (elevated, consistent with decompensated CHF)
- Chest X-ray: Mild cardiomegaly, bilateral pleural effusions noted
- Echocardiogram: EF 35%, global LV dysfunction

ASSESSMENT & PLAN:
1. Decompensated Congestive Heart Failure: Admit for IV diuresis; adjust furosemide
2. Type 2 Diabetes: Continue metformin; monitor glucose closely during admission
3. Hypertension: Continue lisinopril; BP goal < 130/80 mmHg
4. Chronic Kidney Disease: Monitor renal function during diuresis

REFERRALS:
Referral sent to Dr. Angela Kim (Cardiologist, NVH Cardiology Suite 4B),
Contact: angela.kim@northviewhospital.org, (512) 900-4477.
Appointment scheduled for follow-up on February 3, 2025.

ATTENDING PHYSICIAN SIGNATURE:
Dr. Marcus Delroy Webb, MD
Internal Medicine - License No. TX-48821-MD
Date: January 7, 2025
"""

def create_test_pdf(filename="test_medical_record.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    for line in SAMPLE_TEXT.strip().split('\n'):
        if line.startswith('---'):
            story.append(Spacer(1, 0.15 * inch))
        elif line.strip() == '':
            story.append(Spacer(1, 0.08 * inch))
        else:
            style = styles['Heading2'] if line.isupper() and len(line) > 5 else styles['Normal']
            story.append(Paragraph(line.strip(), style))

    doc.build(story)
    print(f"Test PDF created: {filename}")
    print("\nPII embedded (all 6 categories):")
    print("  PERSON   : Sarah Elizabeth Thornton, Dr. Marcus Delroy Webb, Dr. Priya Nair, Dr. Angela Kim, James Thornton")
    print("  SSN      : 487-92-1065")
    print("  DATE     : March 14 1982, January 7 2025, April 2019, July 2021, February 3 2025")
    print("  LOCATION : Austin TX 78701, Austin TX 78705")
    print("  CONTACT  : (512) 884-3920, sarah.thornton@gmail.com, 512-774-0011, (512) 334-8821, (512) 900-4477, angela.kim@northviewhospital.org")
    print("  CONDITION: Congestive Heart Failure, Type 2 Diabetes, Hypertension, Chronic Kidney Disease")

if __name__ == "__main__":
    try:
        create_test_pdf()
    except ImportError:
        print("reportlab not installed. Run: pip install reportlab")
        print("\nAlternatively, the text content above can be pasted manually in the Evaluation Dashboard.")
