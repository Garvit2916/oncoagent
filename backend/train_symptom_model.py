"""
Train production Ensemble ML Model on clinical symptom features
from lung_cancer_enhanced.csv and serialize to backend/models/lung_cancer_ultra_model_v3.pkl
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score, confusion_matrix

def train():
    data_path = os.path.join(os.path.dirname(__file__), "data", "lung_cancer_enhanced.csv")
    output_path = os.path.join(os.path.dirname(__file__), "models", "lung_cancer_ultra_model_v3.pkl")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Loading dataset from: {data_path}")
    df = pd.read_csv(data_path)
    
    # 23 primary clinical, lifestyle, and symptom features
    clinical_features = [
        "Age", "Gender", "Air_Pollution", "Alcohol_Use", "Dust_Allergy", 
        "Occupational_Hazards", "Genetic_Risk", "Chronic_Lung_Disease", 
        "Balanced_Diet", "Obesity", "Smoking", "Passive_Smoker", 
        "Chest_Pain", "Coughing_Blood", "Fatigue", "Weight_Loss", 
        "Shortness_Breath", "Wheezing", "Swallowing_Difficulty", 
        "Clubbing_Nails", "Frequent_Cold", "Dry_Cough", "Snoring"
    ]
    
    X_df = df[clinical_features].copy()
    if "Gender" in X_df.columns:
        X_df["Gender"] = X_df["Gender"].map({"Male": 1, "Female": 0}).fillna(1).astype(int)
        
    X_df = X_df.fillna(X_df.median())
    y = df["Result"].astype(int)
    
    print(f"Features: {len(clinical_features)}, Records: {len(X_df)}, Class Distribution: {np.bincount(y)}")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_df, y, test_size=0.2, random_state=42, stratify=y
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    rf = RandomForestClassifier(
        n_estimators=150, max_depth=7, min_samples_split=4, random_state=42, class_weight="balanced"
    )
    gb = GradientBoostingClassifier(
        n_estimators=100, learning_rate=0.08, max_depth=4, random_state=42
    )
    lr = LogisticRegression(
        C=1.0, max_iter=1000, random_state=42, class_weight="balanced"
    )
    
    ensemble = VotingClassifier(
        estimators=[("rf", rf), ("gb", gb), ("lr", lr)],
        voting="soft"
    )
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_auc = cross_val_score(ensemble, X_train_scaled, y_train, cv=cv, scoring="roc_auc")
    cv_acc = cross_val_score(ensemble, X_train_scaled, y_train, cv=cv, scoring="accuracy")
    print(f"5-Fold CV ROC-AUC: {cv_auc.mean():.4f} (+/- {cv_auc.std():.4f})")
    print(f"5-Fold CV Accuracy: {cv_acc.mean():.4f} (+/- {cv_acc.std():.4f})")
    
    ensemble.fit(X_train_scaled, y_train)
    rf.fit(X_train_scaled, y_train)
    
    y_pred = ensemble.predict(X_test_scaled)
    y_prob = ensemble.predict_proba(X_test_scaled)[:, 1]
    
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    
    print("\n--- Test Set Evaluation ---")
    print(f"Accuracy : {acc * 100:.2f}%")
    print(f"ROC-AUC  : {auc * 100:.2f}%")
    print(f"Precision: {prec * 100:.2f}%")
    print(f"Recall   : {rec * 100:.2f}%")
    print(f"F1 Score : {f1 * 100:.2f}%")
    print("Confusion Matrix:\n", cm)
    
    importances = rf.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    top_features = [(clinical_features[i], round(float(importances[i]), 4)) for i in sorted_idx[:10]]
    print("\nTop 10 Feature Importances:")
    for feat, imp in top_features:
        print(f"  {feat:25}: {imp:.4f}")
        
    artifact = {
        "ensemble": ensemble,
        "rf": rf,
        "scaler": scaler,
        "features": clinical_features,
        "feature_medians": X_df.median().to_dict(),
        "metrics": {
            "accuracy": round(float(acc), 4),
            "roc_auc": round(float(auc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1": round(float(f1), 4),
            "cv_roc_auc_mean": round(float(cv_auc.mean()), 4),
            "cv_acc_mean": round(float(cv_acc.mean()), 4),
        },
        "top_features": top_features,
        "target_names": ["Low Risk / Benign", "High Risk / Malignant"],
    }
    
    with open(output_path, "wb") as f:
        pickle.dump(artifact, f)
        
    print(f"\nSuccessfully saved trained model artifact to: {output_path}")

if __name__ == "__main__":
    train()
