# Viva Questions and Answers

**Q1. Why did you choose Random Forest?**

It handles non-linear relationships and feature interactions, resists overfitting better than one tree, needs no scaling, works well on tabular data and gives feature importance. We still compared it with Logistic Regression and a Decision Tree and report the real results.

**Q2. What is supervised learning?**

Learning from labelled examples (inputs with known outputs) so the model can predict the output for new inputs. Here the label is PASS/FAIL.

**Q3. What is classification?**

A supervised task where the output is a category (PASS or FAIL) rather than a number.

**Q4. What is Random Forest?**

An ensemble of many decision trees trained on random bootstrap samples and random feature subsets; the final prediction is the majority vote or averaged probability.

**Q5. What is a decision tree?**

A flowchart-like model that splits data by feature thresholds (e.g. attendance < 60?) until it reaches a prediction at a leaf.

**Q6. What is bagging?**

Bootstrap aggregating: train each model on a random sample drawn with replacement and combine their predictions, which reduces variance.

**Q7. What is overfitting?**

When a model memorises training data, including noise, and performs poorly on new data. Random Forest, depth limits and cross-validation reduce it.

**Q8. What is train-test split?**

Dividing data into a training part to learn from and a test part kept unseen to measure real performance. We use 80/20.

**Q9. Why use stratification?**

It keeps the PASS/FAIL ratio the same in train and test sets, so evaluation is reliable when classes are imbalanced.

**Q10. What is accuracy?**

The fraction of all predictions that are correct: (TP+TN)/total.

**Q11. What is precision?**

Of the students predicted as a class, how many truly belong to it: TP/(TP+FP).

**Q12. What is recall?**

Of the students truly in a class, how many the model found: TP/(TP+FN).

**Q13. What is F1-score?**

The harmonic mean of precision and recall; it is low if either is low.

**Q14. Why is recall important for failing students?**

The goal is to find students who will fail. A missed failing student (false negative) gets no help, while a false alarm only costs a mentoring conversation. So we monitor recall of the FAIL class.

**Q15. What is a confusion matrix?**

A table of true vs predicted classes showing TP, TN, FP and FN counts.

**Q16. What is ROC-AUC?**

The area under the ROC curve; it measures how well the model ranks passing students above failing ones across all thresholds. 0.5 is random, 1.0 is perfect.

**Q17. What is feature importance?**

A score of how much each feature reduces impurity across the forest's trees, showing which inputs influence predictions most. We compute it from the trained model, not by hand.

**Q18. Why don't Random Forest models require feature scaling?**

Trees split on thresholds of one feature at a time, so rescaling a feature does not change the ordering or the splits. (Logistic Regression does need scaling, so it is scaled in a pipeline.)

**Q19. Why did you not use final exam marks?**

The system must predict before the final exam. Using final marks would be data leakage and make the prediction useless in practice.

**Q20. What is data leakage?**

Using information in training or prediction that would not be available at real prediction time, which makes results look unrealistically good.

**Q21. Why is the dataset synthetic and does that matter?**

No real data was available and student data is sensitive. It matters because results only show the pipeline works; real data is needed for real conclusions. We state this clearly.

**Q22. Why not 100% accuracy?**

We added noise on purpose; real results depend on many hidden factors. A 100% score would signal leakage or a deterministic dataset.

**Q23. What is class imbalance and how did you handle it?**

When one class is much rarer. We used class_weight='balanced' so mistakes on the minority class cost more, and checked FAIL-class recall.

**Q24. What is GridSearchCV?**

It tries every combination of chosen hyperparameters using cross-validation and returns the best. We scored it on FAIL-class F1.

**Q25. What is cross-validation?**

Splitting training data into k folds, training on k-1 and validating on the remaining one in turn, to get a more stable estimate (we use 5 folds).

**Q26. Why use Django?**

It is a secure, batteries-included Python framework with an ORM, authentication, forms, admin and CSRF protection, and it integrates easily with Python ML libraries.

**Q27. Why use MySQL?**

It is a reliable, widely used relational database suited to structured records with relationships (student–performance–prediction).

**Q28. How is the model integrated with Django?**

ml_model.py loads random_forest_model.pkl once (cached), builds a one-row DataFrame from validated form data, calls predict and predict_proba, and views save the result through the ORM.

**Q29. What is model serialization?**

Saving a trained model object to a file so it can be reloaded later without retraining.

**Q30. Why use Joblib?**

It serialises objects with large NumPy arrays (like forests) efficiently, and it is the scikit-learn recommended approach. Only load pkl files from trusted sources.

**Q31. How are risk levels decided?**

From pass probability: >=75% low, 50–75% medium, <50% high. The thresholds are in settings.RISK_THRESHOLDS, in one place.

**Q32. What security measures are used?**

CSRF tokens, authentication with hashed passwords, login-required views, validated input, ORM (no raw SQL), secrets in .env, POST-only logout/delete.

**Q33. How is SQL injection prevented?**

All queries go through the Django ORM, which uses parameterised queries.

**Q34. What is the ER relationship?**

One Student has many StudentPerformance records and many Predictions (1:N); each Prediction links to the performance record used.

**Q35. Why save probabilities and not just PASS/FAIL?**

Probabilities show confidence and allow risk levels; a 52% pass is very different from a 95% pass.

**Q36. What are the limitations of the system?**

Synthetic training data, few features, correlation not causation, possible bias, needs retraining when conditions change, and predictions must not be treated as certain.

**Q37. What are the ethical concerns?**

Labelling students can create stigma or self-fulfilling prophecies; data privacy must be protected. Predictions are for support, not punishment, and need human judgement.

**Q38. What would you improve?**

Use real anonymised data, add SHAP explanations, e-mail alerts, role-based access, bulk upload and scheduled retraining.

**Q39. Random Forest vs Logistic Regression — which was better here?**

They were about equal in accuracy; Logistic Regression had higher FAIL recall on our synthetic data. We report this honestly. Random Forest remains the proposed model for non-linear patterns and importance scores.

