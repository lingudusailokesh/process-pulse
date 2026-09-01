import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
import pm4py
from app.models.process import ProcessEventLog, ProcessInstance
from app.schemas.process_mining import DFGResponse, DFGNode, DFGEdge, VariantsResponse, ProcessVariant

class ProcessMinerService:
    def __init__(self, db: Session):
        self.db = db

    def get_event_log_dataframe(self, process_id: str = "ONBOARD_V1") -> pd.DataFrame:
        """
        Extracts chronological event stream from MySQL and formats into standard PM4Py format.
        """
        events = self.db.query(ProcessEventLog).join(ProcessInstance).filter(
            ProcessInstance.process_id == process_id,
            ProcessInstance.current_status == "COMPLETED"
        ).order_by(ProcessEventLog.case_id, ProcessEventLog.event_timestamp.asc()).all()

        if not events:
            return pd.DataFrame(columns=["case:concept:name", "concept:name", "time:timestamp", "department_id"])

        data = [{
            "case:concept:name": str(e.case_id),
            "concept:name": str(e.activity_name),
            "time:timestamp": e.event_timestamp,
            "department_id": str(e.department_id),
            "activity_status": str(e.activity_status)
        } for e in events]

        df = pd.DataFrame(data)
        df["time:timestamp"] = pd.to_datetime(df["time:timestamp"])
        return df

    def get_directly_follows_graph(self, process_id: str = "ONBOARD_V1") -> DFGResponse:
        """
        Constructs Directly-Follows Graph (DFG) nodes and edges for Cytoscape.js visualization.
        """
        df = self.get_event_log_dataframe(process_id)
        if df.empty:
            return DFGResponse(process_id=process_id, total_cases=0, nodes=[], edges=[])

        total_cases = df["case:concept:name"].nunique()

        # Compute DFG via PM4Py
        dfg, start_activities, end_activities = pm4py.discover_dfg(df)

        # Compute stage duration and execution counts per activity
        df["prev_timestamp"] = df.groupby("case:concept:name")["time:timestamp"].shift(1)
        df["duration_hours"] = (df["time:timestamp"] - df["prev_timestamp"]).dt.total_seconds() / 3600.0
        df["duration_hours"] = df["duration_hours"].fillna(1.0)

        activity_stats = df.groupby("concept:name").agg(
            execution_count=("case:concept:name", "count"),
            unique_cases_count=("case:concept:name", "nunique"),
            median_duration=("duration_hours", "median"),
            avg_duration=("duration_hours", "mean"),
            dept=("department_id", "first")
        ).to_dict(orient="index")

        nodes: List[DFGNode] = []
        for act_name, stats in activity_stats.items():
            is_start = act_name in start_activities
            is_end = act_name in end_activities or "Complete" in act_name
            is_bottleneck = stats["median_duration"] > 25.0

            nodes.append(DFGNode(
                id=act_name.replace(" ", "_").lower(),
                label=act_name,
                department_id=stats["dept"],
                unique_cases_count=int(stats["unique_cases_count"]),
                execution_count=int(stats["execution_count"]),
                avg_duration_hours=round(float(stats["avg_duration"]), 2),
                median_duration_hours=round(float(stats["median_duration"]), 2),
                is_start=is_start,
                is_end=is_end,
                is_bottleneck=is_bottleneck
            ))

        # Compute edge transition durations
        # Create transitions dataframe
        df["next_activity"] = df.groupby("case:concept:name")["concept:name"].shift(-1)
        df["next_timestamp"] = df.groupby("case:concept:name")["time:timestamp"].shift(-1)
        df["transition_hours"] = (df["next_timestamp"] - df["time:timestamp"]).dt.total_seconds() / 3600.0

        transitions_df = df.dropna(subset=["next_activity"])
        edge_metrics = transitions_df.groupby(["concept:name", "next_activity"]).agg(
            trans_count=("case:concept:name", "count"),
            avg_hours=("transition_hours", "mean"),
            median_hours=("transition_hours", "median")
        ).reset_index()

        edges: List[DFGEdge] = []
        for _, row in edge_metrics.iterrows():
            source = str(row["concept:name"])
            target = str(row["next_activity"])
            source_id = source.replace(" ", "_").lower()
            target_id = target.replace(" ", "_").lower()
            
            # Detect loop / rework (e.g. IT -> HR)
            is_loop = ("IT" in source and "HR" in target) or (source == target)

            edges.append(DFGEdge(
                id=f"{source_id}__to__{target_id}",
                source=source_id,
                target=target_id,
                transition_count=int(row["trans_count"]),
                avg_transition_hours=round(float(row["avg_hours"]), 2),
                median_transition_hours=round(float(row["median_hours"]), 2),
                is_rework_loop=is_loop
            ))

        return DFGResponse(
            process_id=process_id,
            total_cases=total_cases,
            nodes=nodes,
            edges=edges
        )

    def get_process_variants(self, process_id: str = "ONBOARD_V1") -> VariantsResponse:
        """
        Discovers and ranks all unique process execution path variants.
        """
        df = self.get_event_log_dataframe(process_id)
        if df.empty:
            return VariantsResponse(process_id=process_id, total_variants_discovered=0, variants=[])

        total_cases = df["case:concept:name"].nunique()

        # Group activities by case into ordered trace tuples
        traces = df.groupby("case:concept:name")["concept:name"].apply(tuple).reset_index()
        
        # Merge total duration from ProcessInstance
        case_durations = {
            c.case_id: {"duration": c.total_duration_hours or 0.0, "breached": c.is_sla_breached}
            for c in self.db.query(ProcessInstance).filter(
                ProcessInstance.process_id == process_id,
                ProcessInstance.current_status == "COMPLETED"
            ).all()
        }

        traces["total_duration"] = traces["case:concept:name"].apply(lambda cid: case_durations.get(cid, {}).get("duration", 0.0))
        traces["is_breached"] = traces["case:concept:name"].apply(lambda cid: case_durations.get(cid, {}).get("breached", False))

        variant_groups = traces.groupby("concept:name")
        
        variants: List[ProcessVariant] = []
        var_idx = 1
        for trace_tuple, group in variant_groups:
            count = len(group)
            pct = (count / total_cases) * 100.0
            durations = group["total_duration"].values
            avg_dur = float(np.mean(durations)) if len(durations) > 0 else 0.0
            med_dur = float(np.median(durations)) if len(durations) > 0 else 0.0
            breached_count = group["is_breached"].sum()
            breach_rate = (breached_count / count) * 100.0 if count > 0 else 0.0

            # Determine description
            path_list = list(trace_tuple)
            is_happy = "Manager Approval" in path_list and "REWORK_TRIGGERED" not in str(path_list) and len(path_list) == 6
            if is_happy:
                desc = "Standard 6-stage compliant onboarding pathway (Happy Path)."
            elif "HR Verification" in path_list and path_list.count("HR Verification") > 1:
                desc = "IT Security Rejection Loop causing bounce-back to HR verification."
            elif "Manager Approval" not in path_list:
                desc = "Direct Fast-track path bypassing Manager Approval (Compliance Risk)."
            else:
                desc = f"Alternative operational pathway with {len(path_list)} steps."

            variants.append(ProcessVariant(
                variant_id=f"VAR_{var_idx}",
                path=path_list,
                case_count=count,
                percentage=round(pct, 2),
                avg_duration_hours=round(avg_dur, 2),
                median_duration_hours=round(med_dur, 2),
                sla_breach_rate_percent=round(breach_rate, 2),
                is_happy_path=is_happy,
                description=desc
            ))
            var_idx += 1

        # Sort variants by case count descending
        variants.sort(key=lambda v: v.case_count, reverse=True)

        return VariantsResponse(
            process_id=process_id,
            total_variants_discovered=len(variants),
            variants=variants
        )
