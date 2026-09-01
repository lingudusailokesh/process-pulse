import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.process import ProcessInstance, ProcessEventLog
from app.schemas.prediction import CasePredictionRequest, CasePredictionResponse, BatchTriageItem

DEPARTMENT_LIST = ["HR", "IT", "OPS", "ENG", "SALES"]

class SlaPredictorService:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.ML_MODEL_PATH
        self.bundle = None
        self._load_or_initialize_model()

    def _load_or_initialize_model(self):
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    self.bundle = pickle.load(f)
                return
            except Exception as e:
                print(f"⚠️ Failed to load model artifact from {self.model_path}: {e}")
        
        # Fallback: train on the fly if needed
        self._train_in_memory_fallback()

    def _train_in_memory_fallback(self):
        from sklearn.ensemble import RandomForestClassifier
        np.random.seed(42)
        records = []
        for _ in range(300):
            dept = np.random.choice(DEPARTMENT_LIST)
            s1 = np.random.uniform(0.5, 3.0)
            s2 = np.random.uniform(4.0, 30.0)
            dow = np.random.randint(0, 7)
            load = np.random.randint(10, 40)
            breach = 1 if (s2 > 16.0 or (dow >= 4 and s2 > 10.0)) else 0
            records.append({
                "stage_1_duration_hours": s1,
                "stage_2_duration_hours": s2,
                "day_of_week": dow,
                "active_load_count": load,
                "dept_HR": 1 if dept == "HR" else 0,
                "dept_IT": 1 if dept == "IT" else 0,
                "dept_OPS": 1 if dept == "OPS" else 0,
                "dept_ENG": 1 if dept == "ENG" else 0,
                "dept_SALES": 1 if dept == "SALES" else 0,
                "is_sla_breached": breach
            })
        df = pd.DataFrame(records)
        feature_cols = [
            "stage_1_duration_hours", "stage_2_duration_hours", "day_of_week", "active_load_count",
            "dept_HR", "dept_IT", "dept_OPS", "dept_ENG", "dept_SALES"
        ]
        clf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        clf.fit(df[feature_cols], df["is_sla_breached"])
        self.bundle = {
            "model": clf,
            "feature_cols": feature_cols,
            "department_list": DEPARTMENT_LIST
        }

    def predict_case(self, req: CasePredictionRequest) -> CasePredictionResponse:
        """
        Runs ML inference to estimate the SLA breach probability of a specific case instance.
        """
        # Feature validation
        s1_dur = max(0.0, min(float(req.stage_1_duration_hours), 200.0))
        s2_dur = max(0.0, min(float(req.stage_2_duration_hours), 200.0))
        dow = max(0, min(int(req.day_of_week), 6))
        load = max(0, min(int(req.active_load_count), 500))

        clf = self.bundle["model"]
        feature_cols = self.bundle["feature_cols"]

        row = {
            "stage_1_duration_hours": s1_dur,
            "stage_2_duration_hours": s2_dur,
            "day_of_week": dow,
            "active_load_count": load,
        }
        for d in DEPARTMENT_LIST:
            row[f"dept_{d}"] = 1 if req.department_id == d else 0

        X = pd.DataFrame([row])[feature_cols]
        prob = float(clf.predict_proba(X)[0][1])

        # Risk stratification
        if prob >= 0.75:
            risk_level = "CRITICAL"
            action = "Trigger automated manager escalation and fast-track IT security review."
        elif prob >= 0.50:
            risk_level = "HIGH"
            action = "Alert HR Shared Services to verify credential specs prior to IT submission."
        elif prob >= 0.25:
            risk_level = "MEDIUM"
            action = "Monitor stage transition; send reminder if pending > 24 hours."
        else:
            risk_level = "LOW"
            action = "Standard progression; case on schedule within target SLA."

        # Risk factor explanations
        factors = []
        if s2_dur > 15.0:
            factors.append(f"Manager approval delay ({s2_dur:.1f}h) exceeds standard 8h benchmark.")
        if dow in [4, 5, 6]:
            factors.append("Case submitted approaching weekend, accumulating cross-department queue latency.")
        if req.department_id in ["IT", "OPS"]:
            factors.append(f"Department '{req.department_id}' historically experiences highest rework loops.")
        if not factors:
            factors.append("Operational latencies are within nominal parameters.")

        return CasePredictionResponse(
            case_id=req.case_id,
            department_id=req.department_id,
            sla_breach_probability=round(prob, 3),
            risk_level=risk_level,
            predicted_breach=prob >= 0.50,
            top_risk_factors=factors,
            suggested_action=action
        )

    def get_live_triage_queue(self, db: Session, process_id: str = "ONBOARD_V1") -> List[BatchTriageItem]:
        """
        Evaluates all active, in-progress cases in real time and ranks them by breach risk.
        Computes accurate, timezone-consistent elapsed hours from case start time.
        """
        from datetime import datetime, timezone

        active_cases = db.query(ProcessInstance).filter(
            ProcessInstance.process_id == process_id,
            ProcessInstance.current_status == "IN_PROGRESS"
        ).all()

        if not active_cases:
            return []

        triage_items: List[BatchTriageItem] = []
        
        for c in active_cases:
            events = sorted(c.events, key=lambda e: e.event_timestamp)
            current_stage = events[-1].activity_name if events else "Initiated"
            
            s1_dur = 1.0
            s2_dur = 8.0
            if len(events) >= 1:
                s1_dur = max(0.5, (events[0].event_timestamp - c.start_time).total_seconds() / 3600.0)
            if len(events) >= 2:
                s2_dur = max(0.5, (events[1].event_timestamp - events[0].event_timestamp).total_seconds() / 3600.0)

            # Accurate timezone-consistent elapsed time calculation
            # Compare naive timestamps or aware timestamps consistently
            if c.start_time.tzinfo is None:
                # Use UTC naive now for comparison
                now_cmp = datetime.now(timezone.utc).replace(tzinfo=None)
            else:
                now_cmp = datetime.now(timezone.utc)

            elapsed_seconds = (now_cmp - c.start_time).total_seconds()
            elapsed_hours = max(0.0, elapsed_seconds / 3600.0)

            # Cap or guard if start time was in future due to clock skew
            if elapsed_hours <= 0.0:
                elapsed_hours = s1_dur + s2_dur

            req = CasePredictionRequest(
                case_id=c.case_id,
                department_id=c.department_id,
                stage_1_duration_hours=round(s1_dur, 2),
                stage_2_duration_hours=round(s2_dur, 2),
                day_of_week=c.start_time.weekday(),
                active_load_count=len(active_cases)
            )
            pred = self.predict_case(req)

            triage_items.append(BatchTriageItem(
                case_id=c.case_id,
                department_id=c.department_id,
                current_stage=current_stage,
                elapsed_hours=round(float(elapsed_hours), 1),
                breach_probability=pred.sla_breach_probability,
                risk_level=pred.risk_level,
                suggested_action=pred.suggested_action
            ))

        # Sort descending by breach probability (highest risk first)
        triage_items.sort(key=lambda x: x.breach_probability, reverse=True)
        return triage_items
