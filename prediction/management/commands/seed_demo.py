"""Create SYNTHETIC demo students (random rows of ml/student_data.csv) and predict them.
Usage: python manage.py seed_demo --count 30
"""
import random

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from prediction import ml_model
from prediction.models import Prediction, Student, StudentPerformance

FIRST = ["Aarav", "Diya", "Rahul", "Ananya", "Vikram", "Sneha", "Karthik", "Meera", "Rohan",
         "Priya", "Arjun", "Kavya", "Nikhil", "Isha", "Suresh", "Pooja", "Manoj", "Riya"]
LAST = ["Kumar", "Sharma", "Reddy", "Patel", "Nair", "Gowda", "Singh", "Rao", "Iyer", "Das"]
DEPTS = ["CSE", "ISE", "ECE", "MECH"]


class Command(BaseCommand):
    help = "Create synthetic demo students with predictions (NOT real student data)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=30)

    def handle(self, *args, **opts):
        csv = settings.ML_DIR / "student_data.csv"
        if not csv.exists():
            self.stderr.write("ml/student_data.csv not found - run python ml/train_model.py first.")
            return
        rows = pd.read_csv(csv).sample(opts["count"], random_state=7)
        rng = random.Random(7)
        made = 0
        for i, (_, r) in enumerate(rows.iterrows(), start=1):
            usn = f"1DM23CS{i:03d}"
            if Student.objects.filter(usn=usn).exists():
                continue
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            student = Student.objects.create(
                name=name, usn=usn, email=f"{usn.lower()}@example.com",
                department=rng.choice(DEPTS), semester=rng.choice([3, 4, 5, 6]),
                section=rng.choice("ABC"))
            feats = {f: r[f] for f in ml_model.FEATURES}
            feats["backlogs"] = int(feats["backlogs"])
            perf = StudentPerformance.objects.create(student=student, **feats)
            Prediction.objects.create(student=student, performance=perf, **ml_model.predict(feats))
            made += 1
        self.stdout.write(self.style.SUCCESS(f"Created {made} synthetic demo students."))
