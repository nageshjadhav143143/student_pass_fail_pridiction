# Student Pass/Fail Prediction System Using Random Forest

A Django + MySQL web application that predicts, **before the final exam**, whether a student is likely to PASS or FAIL, using a Random Forest classifier trained on attendance and academic-performance data.

> **Data notice:** the bundled dataset (`ml/student_data.csv`, 1,200 rows) and demo students are **synthetic** (computer-generated). They are not real students. Replace the CSV with real, consented, anonymised data for any real use.

## Abstract
Many students fail only because warning signs (low attendance, weak internals, backlogs) are noticed too late. This project trains a Random Forest on eight pre-exam indicators and serves it through a web dashboard that shows the predicted result, pass/fail probability, a risk level and the most influential factors, so mentors can intervene early.

## Problem Statement
Predict a student's final result (PASS/FAIL) from attendance, internal assessments, assignments, quizzes, mid-term, study hours, previous-semester percentage and backlogs, without using final-exam marks.

## Objectives
- Build and tune a Random Forest classifier and compare it with Logistic Regression and a Decision Tree.
- Prioritise identifying at-risk (FAIL) students, so recall of the FAIL class is monitored.
- Provide a secure, professional Django interface with MySQL storage, dashboards and analytics.

## Existing System
Result analysis is manual and happens after exams; at-risk students are identified by teacher intuition or after failing.

## Proposed System
An ML-based early-warning system: enter marks → get PASS/FAIL, probabilities, risk level and recommended actions, with history and analytics saved in MySQL.

## Features
Login/logout · dashboard cards · add student · prediction with validation · result page with probability ring · high-risk warning with recommended actions · searchable/filterable student list · prediction history · analytics (Chart.js) · ML model page with real metrics · Django admin · friendly error pages.

## Technology Stack
Python, Pandas, NumPy, Scikit-learn, Matplotlib, Seaborn, Joblib · Django · MySQL · HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js.

## Project Structure
```
student_prediction/
├── manage.py  requirements.txt  .env  .env.example
├── student_prediction/   settings.py urls.py wsgi.py asgi.py
├── prediction/           models.py forms.py views.py urls.py ml_model.py admin.py tests.py
│   ├── migrations/       0001_initial.py
│   └── management/commands/seed_demo.py
├── templates/            base home login dashboard add_student student_form prediction_result
│                         students prediction_history analytics model_info error .html
├── static/               css/style.css  js/script.js  charts/*.png
├── ml/                   train_model.py  student_data.csv  random_forest_model.pkl
│                         model_metrics.json  feature_importance.json
└── docs/                 PROJECT_REPORT.md  VIVA_QUESTIONS.md
```

## Machine Learning Methodology
1. **Data**: synthetic generator driven by a hidden "ability" variable plus random noise (so accuracy is not unrealistically perfect).
2. **Cleaning**: missing values, duplicates, range validation, IQR capping of `study_hours`.
3. **EDA**: summary statistics, class distribution, correlation heatmap.
4. **Split**: `train_test_split(test_size=0.2, random_state=42, stratify=y)`.
5. **Imbalance**: `class_weight="balanced"` (no resampling).
6. **Models**: Logistic Regression (scaled), Decision Tree, Random Forest.
7. **Tuning**: `GridSearchCV`, 5-fold stratified CV, scored on **F1 of the FAIL class** (not just accuracy).
8. **Evaluation**: accuracy, precision, recall, F1, ROC-AUC, confusion matrix, FAIL-class recall.
9. **Persistence**: Joblib model + JSON metrics + JSON feature importances.

No feature scaling is applied to the Random Forest: trees split on thresholds, so monotonic rescaling does not change the splits.

## Dataset Description
| Feature | Range | Meaning |
|---|---|---|
| attendance_percentage | 0–100 | Class attendance |
| internal_marks | 0–100 | Internal assessment |
| assignment_score | 0–100 | Assignments |
| quiz_score | 0–100 | Quizzes |
| midterm_score | 0–100 | Mid-term exam |
| study_hours | 0–24 | Average daily study |
| previous_sem_percentage | 0–100 | Last semester result |
| backlogs | 0+ | Pending subjects |
| **final_result** (target) | 1 = PASS, 0 = FAIL | Final-exam marks are deliberately excluded |

## Random Forest Explanation
A Random Forest is an ensemble of many decision trees. Each tree is trained on a bootstrap sample (bagging) and considers a random subset of features at each split. For a new student every tree votes; the averaged votes give `predict_proba` (pass/fail probability). Averaging many different trees reduces overfitting compared with a single tree.

## System Architecture
```
Browser (HTML/CSS/JS) → Django views → forms (validation) → ml_model.py → random_forest_model.pkl
                                   ↘ Django ORM → MySQL (Student, StudentPerformance, Prediction)
```

## Database Design / ER Diagram
```
STUDENT (1) ────< (N) STUDENT_PERFORMANCE (1) ────< (N) PREDICTION
   └───────────────────────────< (N) ───────────────────┘
```
- **Student**: student_id (PK), name, usn (unique), email, department, semester, section, created_at
- **StudentPerformance**: performance_id (PK), student (FK), 8 feature columns, created_at
- **Prediction**: prediction_id (PK), student (FK), performance (FK), prediction, pass_probability, fail_probability, risk_level, prediction_date

One student can have many performance records and predictions.

## Workflow
Login → enter student + marks → server-side validation → model predicts → Student/Performance/Prediction saved in one database transaction → result page → history and analytics update.

## Installation (from zero)

**1. Install** Python 3.10+ and MySQL Server 8.

**2. Virtual environment**
```
python -m venv venv
```
**3. Activate** — Windows: `venv\Scripts\activate` · macOS/Linux: `source venv/bin/activate`

**4. Dependencies**
```
pip install -r requirements.txt
```
*(If `mysqlclient` fails on Windows: `pip install pymysql cryptography` — the project falls back to it automatically.)*

**5. Create the MySQL database**
```sql
CREATE DATABASE student_prediction_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
(e.g. `mysql -u root -p` then paste the line.)

**6. Configure `.env`** — set `DB_PASSWORD` (and `SECRET_KEY`). Settings read them with `os.getenv(...)`:
```python
DATABASES = {"default": {"ENGINE": "django.db.backends.mysql", "NAME": os.getenv("DB_NAME"),
  "USER": os.getenv("DB_USER"), "PASSWORD": os.getenv("DB_PASSWORD"),
  "HOST": os.getenv("DB_HOST"), "PORT": os.getenv("DB_PORT")}}
```
For a quick test without MySQL only, set `DB_ENGINE=sqlite` in `.env`.

**7. Migrations**
```
python manage.py makemigrations
python manage.py migrate
```
**8. Create admin user**
```
python manage.py createsuperuser
```
**9. Train the model** (regenerates the model for *your* scikit-learn version)
```
python ml/train_model.py
```
**10. Run**
```
python manage.py runserver
```
Open http://127.0.0.1:8000 · optional demo data: `python manage.py seed_demo --count 30` · tests: `python manage.py test`.

## Security
CSRF protection, Django authentication and PBKDF2 password hashing, login required on all data pages, server-side validation, ORM only (no raw SQL → SQL-injection safe), secrets and DB credentials in `.env` (git-ignored), POST-only logout/delete. Before deployment set `DEBUG=False`, a strong `SECRET_KEY`, correct `ALLOWED_HOSTS`, HTTPS and `SECURE_COOKIES=True`. Student records are personal data: restrict access and use only with consent.

## Risk Levels
Defined once in `settings.py` → `RISK_THRESHOLDS`. Pass probability ≥ 75% = LOW · 50–75% = MEDIUM · < 50% = HIGH.

## Model Evaluation (results of the included run, 240 test students, synthetic data)
| Algorithm | Accuracy | Precision | Recall | F1 | FAIL recall |
|---|---|---|---|---|---|
| Logistic Regression | 0.842 | 0.903 | 0.845 | 0.873 | 0.835 |
| Decision Tree | 0.792 | 0.867 | 0.800 | 0.832 | 0.776 |
| Random Forest | 0.842 | 0.877 | 0.877 | 0.877 | 0.776 |

Random Forest ties Logistic Regression on accuracy and is slightly lower on FAIL recall. This is reported honestly: the synthetic data is close to linear, which suits Logistic Regression. Random Forest is kept as the proposed model for non-linear modelling and built-in feature importance. Exact numbers can change slightly with your scikit-learn version. The **ML Model** page always shows the values stored in `model_metrics.json`.

**Why FAIL recall matters:** the purpose is to find students who will fail. A missed failing student (false negative) gets no help; a false alarm only costs a conversation. So recall of the FAIL class is monitored alongside precision.

## Screenshots
`[ Login ]  [ Dashboard ]  [ Prediction form ]  [ Result ]  [ Students ]  [ Analytics ]  [ ML Model ]` — add your own screenshots here.

## Advantages
Early warning · transparent probabilities · feature importance · no retraining at request time · simple stack.

## Limitations
Synthetic training data; predictions reflect patterns, not individuals; no causal explanation; a small feature set; model must be retrained when the grading policy changes; ethical risk of labelling students.

## Future Enhancements
Real institutional data, per-student SHAP explanations, e-mail alerts to mentors, role-based access (teacher/HOD), CSV bulk upload, periodic retraining, XGBoost comparison.

## Conclusion
The system shows how a Random Forest can be integrated into a Django/MySQL application as an early-warning tool, with honest evaluation and responsible-use safeguards.
