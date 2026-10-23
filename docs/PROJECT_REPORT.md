# Project Report Content — Student Pass/Fail Prediction System Using Random Forest

## 1. Introduction
Academic failure affects students, families and institutions. This project builds a web-based system that predicts PASS/FAIL before final exams so that support can be given early.

## 2. Background
Machine learning can learn patterns from past student data. Classification algorithms such as Random Forest work well on tabular academic data. Django offers a secure web framework and MySQL a reliable relational store.

## 3. Problem Statement
Given attendance and internal academic indicators, predict whether a student will pass or fail the final examination, without using the final-exam marks.

## 4. Objectives
1. Build a Random Forest classifier for pass/fail prediction.
2. Compare it with Logistic Regression and Decision Tree using accuracy, precision, recall and F1.
3. Prioritise detection of at-risk (FAIL) students.
4. Deliver a secure Django + MySQL interface with dashboards, history and analytics.

## 5. Literature Survey
(Summarise 4–6 papers you read yourself; suggested topics to search.)
- Breiman, L. (2001). *Random Forests.* Machine Learning, 45(1), 5–32.
- Cortez, P. & Silva, A. (2008). *Using data mining to predict secondary school student performance.* (UCI Student Performance dataset.)
- Romero, C. & Ventura, S. (2010). *Educational data mining: a review of the state of the art.* IEEE Trans. SMC-C.
- Pedregosa et al. (2011). *Scikit-learn: Machine Learning in Python.* JMLR 12.
- Papers on early-warning systems and learning analytics in higher education.
Write 3–4 lines per paper: objective, method, result, gap your project addresses.

## 6. Existing System
Manual result analysis after exams; subjective teacher judgement; no probability or risk estimate; no stored history.

## 7. Proposed System
Automated prediction with Random Forest, probability scores, risk levels, recommended actions, student history and analytics in a web dashboard.

## 8. System Requirements
Functional: login, add student, predict, view result, list/filter students, history, analytics, model information. Non-functional: security, usability, responsiveness, maintainability.

## 9. Hardware Requirements
Dual-core processor or better, 4 GB RAM (8 GB recommended), 2 GB free disk, internet for CDN assets.

## 10. Software Requirements
Windows/Linux/macOS · Python 3.10+ · Django · MySQL 8 · scikit-learn, pandas, numpy, matplotlib, seaborn, joblib · VS Code · modern web browser.

## 11. System Architecture
Presentation (HTML/CSS/JS) → Application (Django views/forms) → ML layer (`ml_model.py` + Joblib model) → Data layer (Django ORM + MySQL). Training is an offline script.

## 12. Data Flow Diagram
- Level 0: User → [Prediction System] → Result.
- Level 1: User → (1) Login → (2) Enter details → (3) Validate → (4) Load model & predict → (5) Save to DB → (6) Display result; (7) History/Analytics read from DB.
Draw these with boxes and arrows in your report.

## 13. ER Diagram
Entities: STUDENT, STUDENT_PERFORMANCE, PREDICTION. STUDENT 1—N STUDENT_PERFORMANCE; STUDENT 1—N PREDICTION; STUDENT_PERFORMANCE 1—N PREDICTION.

## 14. Database Design
| Table | Key fields |
|---|---|
| Student | student_id PK, name, usn (unique), email, department, semester, section, created_at |
| StudentPerformance | performance_id PK, student FK, attendance_percentage, internal_marks, assignment_score, quiz_score, midterm_score, study_hours, previous_sem_percentage, backlogs, created_at |
| Prediction | prediction_id PK, student FK, performance FK, prediction, pass_probability, fail_probability, risk_level, prediction_date |

## 15. Dataset
1,200 synthetic records (`student_data.csv`), 8 features + target. About 65% PASS and 35% FAIL. Generated from a latent "ability" variable with noise; it is **not** real student data and this must be stated in the report.

## 16. Data Preprocessing
Missing-value check, duplicate removal, range validation, IQR capping for study hours, feature/target separation, stratified 80/20 split, class imbalance handled with `class_weight="balanced"`. No scaling for tree models.

## 17. Exploratory Data Analysis
Summary statistics, class-distribution chart, correlation heatmap (`static/charts/`). Attendance, internal marks and previous-semester percentage correlate positively with passing; backlogs correlate negatively.

## 18. Machine Learning Algorithm
Supervised binary classification. Models compared: Logistic Regression, Decision Tree, Random Forest.

## 19. Random Forest Algorithm
1. Draw a bootstrap sample for each tree. 2. Grow the tree, choosing the best split among a random subset of features at each node. 3. Repeat for N trees. 4. Predict by majority vote / average probability. Feature importance = mean decrease in impurity attributed to each feature.

## 20. Model Training
`GridSearchCV` over n_estimators, max_depth, min_samples_split, min_samples_leaf, max_features; 5-fold stratified CV; scoring = F1 of FAIL class. Best parameters are saved in `model_metrics.json`. Model saved with Joblib.

## 21. Model Evaluation
Metrics: accuracy, precision, recall, F1, ROC-AUC, confusion matrix. Included run (240 test records): Random Forest accuracy 0.842, precision 0.877, recall 0.877, F1 0.877, FAIL recall 0.776; Logistic Regression accuracy 0.842, FAIL recall 0.835; Decision Tree accuracy 0.792. (Copy the latest numbers from the ML Model page after your own training.)

## 22. Results
Internal marks, attendance and previous-semester percentage were the most important features. Random Forest performed comparably to Logistic Regression on this synthetic data and better than a single Decision Tree. Report the real numbers; do not adjust them.

## 23. Django Implementation
Project `student_prediction`, app `prediction`. Models → migrations → forms (validation) → views (login required) → templates → static files. `ml_model.py` loads the cached model and returns prediction, probabilities and risk. Saves use `transaction.atomic()`.

## 24. Testing
Automated: 15 tests in `prediction/tests.py` (risk thresholds, model output, login protection, prediction flow, validation, filters, cascade delete, missing-model error). Manual: boundary values (0, 100, 24 hours), empty form, invalid text, duplicate USN, mobile layout.

## 25. Advantages
Early identification, probabilities, explainable importance, quick predictions, maintainable code.

## 26. Limitations
Synthetic data, limited features, no causal reasoning, possible bias, requires retraining for policy changes.

## 27. Future Scope
Real data integration, SHAP explanations, SMS/e-mail alerts, role-based access, bulk CSV upload, automated retraining, cloud deployment.

## 28. Conclusion
The system demonstrates a complete ML-to-web pipeline and an early-warning workflow, evaluated honestly with recall-focused metrics.

## 29. References
1. Breiman, L. Random Forests, Machine Learning, 2001.
2. Pedregosa et al. Scikit-learn, JMLR, 2011.
3. Django Documentation — https://docs.djangoproject.com
4. MySQL Reference Manual — https://dev.mysql.com/doc
5. Cortez & Silva, student performance data mining, 2008.
6. Chart.js Documentation — https://www.chartjs.org
