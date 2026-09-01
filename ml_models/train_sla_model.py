import os
import sys
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, accuracy_score, precision_score, recall_score

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal, engine
from app.models.process import ProcessInstance, ProcessEventLog

DEPARTMENT_LIST = ["HR", "IT", "OPS", "ENG", "SALES"]

def build_dataset_from_db():
    db = SessionLocal()
    try:
        cases = db.query(ProcessInstance).filter(
            ProcessInstance.current_status == "COMPLETED",
            ProcessInstance.total_duration_hours.isnot(None)
        ).all()

        if not cases:
            print("[!] No completed cases found in database. Generating synthetic training dataset...")
            return generate_synthetic_training_data()

        records = []
        for c in cases:
            events = sorted(c.events, key=lambda e: e.event_timestamp)
            if len(events) < 2:
                continue

            # Stage 1 duration
            s1_dur = (events[0].event_timestamp - c.start_time).total_seconds() / 3600.0
            # Stage 2 duration
            s2_dur = (events[1].event_timestamp - events[0].event_timestamp).total_seconds() / 3600.0 if len(events) > 1 else 8.0

            day_of_week = c.start_time.weekday()
            
            # Record
            records.append({
                "department_id": c.department_id,
                "stage_1_duration_hours": max(0.1, s1_dur),
                "stage_2_duration_hours": max(0.1, s2_dur),
                "day_of_week": day_of_week,
                "active_load_count": np.random.randint(15, 35),
                "is_sla_breached": 1 if c.is_sla_breached else 0
            })

        df = pd.DataFrame(records)
        return df
    finally:
        db.close()

def generate_synthetic_training_data(n_samples: int = 600):
    np.random.seed(42)
    records = []
    for _ in range(n_samples):
        dept = np.random.choice(DEPARTMENT_LIST)
        s1 = np.random.uniform(0.5, 3.0)
        # High manager approval delay on Friday or in IT/OPS increases breach risk
        dow = np.random.randint(0, 7)
        s2 = np.random.uniform(4.0, 18.0) if dow < 4 else np.random.uniform(12.0, 36.0)
        load = np.random.randint(10, 40)

        # Logic for SLA breach probability
        risk_score = 0.1
        if s2 > 15.0:
            risk_score += 0.45
        if dow >= 4: # Friday/Weekend lag
            risk_score += 0.20
        if dept in ["IT", "OPS"]:
            risk_score += 0.15
        if load > 28:
            risk_score += 0.10

        breached = 1 if np.random.random() < min(0.95, risk_score) else 0

        records.append({
            "department_id": dept,
            "stage_1_duration_hours": round(s1, 2),
            "stage_2_duration_hours": round(s2, 2),
            "day_of_week": dow,
            "active_load_count": load,
            "is_sla_breached": breached
        })

    return pd.DataFrame(records)

def train_and_save_model(model_save_path: str = None):
    if model_save_path is None:
        model_save_path = os.path.join(os.path.dirname(__file__), "sla_model.pkl")

    print("[*] Preparing training dataset...")
    df = build_dataset_from_db()
    
    # Feature Engineering (One-Hot Encoding for Departments)
    for d in DEPARTMENT_LIST:
        df[f"dept_{d}"] = (df["department_id"] == d).astype(int)

    feature_cols = [
        "stage_1_duration_hours",
        "stage_2_duration_hours",
        "day_of_week",
        "active_load_count"
    ] + [f"dept_{d}" for d in DEPARTMENT_LIST]

    X = df[feature_cols]
    y = df["is_sla_breached"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print(f"[*] Training Random Forest Classifier on {len(X_train)} training instances...")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        min_samples_split=4,
        random_state=42,
        class_weight="balanced"
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_prob)

    print("\n=======================================================")
    print("SLA BREACH PREDICTOR - MODEL EVALUATION RESULTS")
    print("=======================================================")
    print(f"Accuracy:  {acc * 100:.2f}%")
    print(f"Precision: {prec * 100:.2f}%")
    print(f"Recall:    {rec * 100:.2f}%")
    print(f"ROC-AUC:   {auc:.3f}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

    # Feature Importance
    importances = sorted(zip(feature_cols, clf.feature_importances_), key=lambda x: x[1], reverse=True)
    print("Top Feature Importances:")
    for feat, imp in importances[:5]:
        print(f" - {feat}: {imp * 100:.1f}%")
    print("=======================================================\n")

    # Serialize Model Bundle
    model_bundle = {
        "model": clf,
        "feature_cols": feature_cols,
        "department_list": DEPARTMENT_LIST,
        "metrics": {"accuracy": acc, "precision": prec, "recall": rec, "roc_auc": auc},
        "trained_at": datetime.utcnow().isoformat()
    }

    with open(model_save_path, "wb") as f:
        pickle.dump(model_bundle, f)

    print(f"[+] Trained model bundle saved successfully to: {model_save_path}")

if __name__ == "__main__":
    train_and_save_model()
