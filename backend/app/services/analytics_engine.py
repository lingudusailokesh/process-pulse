import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models.process import ProcessInstance, ProcessEventLog, ProcessDefinition
from app.models.user import Department
from app.schemas.analytics import OverviewKPIs, BottleneckStage, DepartmentMetric, SlaDistribution

def calculate_bottleneck_severity_index(stage_duration: float, total_duration: float, rework_rate: float) -> float:
    """
    Computes the deterministic Bottleneck Severity Index (BSI).
    Formula: BSI = (Stage Duration / Total Process Duration) * (1 + Rework Rate)
    """
    if total_duration <= 0 or stage_duration <= 0:
        return 0.0
    bsi = (stage_duration / total_duration) * (1.0 + rework_rate)
    return round(float(bsi), 3)

class AnalyticsEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_overview_kpis(self, process_id: str = "ONBOARD_V1") -> OverviewKPIs:
        """
        Calculates high-level executive operational KPIs across all completed cases deterministically.
        """
        proc_def = self.db.query(ProcessDefinition).filter(ProcessDefinition.process_id == process_id).first()
        target_sla = proc_def.sla_hours_target if proc_def else 120.0

        instances = self.db.query(ProcessInstance).filter(ProcessInstance.process_id == process_id).all()
        total_cases = len(instances)
        
        if total_cases == 0:
            return OverviewKPIs(
                total_cases=0, completed_cases=0, active_cases=0,
                avg_cycle_time_hours=0.0, median_cycle_time_hours=0.0, p90_cycle_time_hours=0.0,
                sla_compliance_rate_percent=100.0, sla_breach_rate_percent=0.0,
                rework_case_rate_percent=0.0, total_financial_waste_usd=0.0,
                case_sla_breach_waste_usd=0.0, stage_operational_waste_usd=0.0,
                sla_target_hours=target_sla
            )

        completed = [inst for inst in instances if inst.current_status == "COMPLETED" and inst.total_duration_hours is not None]
        active = [inst for inst in instances if inst.current_status == "IN_PROGRESS"]

        if not completed:
            return OverviewKPIs(
                total_cases=total_cases, completed_cases=0, active_cases=len(active),
                avg_cycle_time_hours=0.0, median_cycle_time_hours=0.0, p90_cycle_time_hours=0.0,
                sla_compliance_rate_percent=100.0, sla_breach_rate_percent=0.0,
                rework_case_rate_percent=0.0, total_financial_waste_usd=0.0,
                case_sla_breach_waste_usd=0.0, stage_operational_waste_usd=0.0,
                sla_target_hours=target_sla
            )

        durations = np.array([c.total_duration_hours for c in completed])
        avg_dur = float(np.mean(durations))
        median_dur = float(np.median(durations))
        p90_dur = float(np.percentile(durations, 90))

        breached_count = sum(1 for c in completed if c.is_sla_breached)
        breach_rate = (breached_count / len(completed)) * 100.0
        compliance_rate = 100.0 - breach_rate

        # Rework detection from variants
        rework_count = sum(1 for c in completed if c.variant_id == "VAR_2_IT_REWORK_LOOP")
        rework_rate = (rework_count / len(completed)) * 100.0

        # Case-level SLA breach penalty: excess hours above target SLA * blended hourly rate ($65/hr)
        case_excess_hours = np.maximum(0, durations - target_sla)
        case_sla_breach_waste = float(np.sum(case_excess_hours) * 65.0)

        # Calculate stage-level bottleneck delay costs for full metric reconciliation
        bottlenecks = self.get_bottlenecks(process_id=process_id)
        stage_waste_total = float(sum(b.financial_cost_of_delay_usd for b in bottlenecks))

        # Total consolidated operational delay waste is the sum of stage delays
        total_waste = stage_waste_total if stage_waste_total > 0 else case_sla_breach_waste

        return OverviewKPIs(
            total_cases=total_cases,
            completed_cases=len(completed),
            active_cases=len(active),
            avg_cycle_time_hours=round(avg_dur, 2),
            median_cycle_time_hours=round(median_dur, 2),
            p90_cycle_time_hours=round(p90_dur, 2),
            sla_compliance_rate_percent=round(compliance_rate, 2),
            sla_breach_rate_percent=round(breach_rate, 2),
            rework_case_rate_percent=round(rework_rate, 2),
            total_financial_waste_usd=round(total_waste, 2),
            case_sla_breach_waste_usd=round(case_sla_breach_waste, 2),
            stage_operational_waste_usd=round(stage_waste_total, 2),
            sla_target_hours=target_sla
        )

    def get_bottlenecks(self, process_id: str = "ONBOARD_V1") -> List[BottleneckStage]:
        """
        Analyzes individual process stages to compute median duration, rework rates, 
        financial delay costs, and the Bottleneck Severity Index (BSI).
        """
        # Load event logs into Pandas DataFrame
        events = self.db.query(ProcessEventLog).join(ProcessInstance).filter(
            ProcessInstance.process_id == process_id,
            ProcessInstance.current_status == "COMPLETED"
        ).all()

        if not events:
            return []

        data = [{
            "case_id": e.case_id,
            "activity_name": e.activity_name,
            "department_id": e.department_id,
            "event_timestamp": e.event_timestamp,
            "activity_status": e.activity_status,
            "cost_incurred": e.cost_incurred
        } for e in events]

        df = pd.DataFrame(data)
        df = df.sort_values(by=["case_id", "event_timestamp"])

        # Calculate stage durations by taking diff between adjacent events per case
        df["prev_timestamp"] = df.groupby("case_id")["event_timestamp"].shift(1)
        df["duration_hours"] = (df["event_timestamp"] - df["prev_timestamp"]).dt.total_seconds() / 3600.0
        # Fill first stage duration with an estimated reasonable baseline or 1.0 hr
        df["duration_hours"] = df["duration_hours"].fillna(1.0)

        # Department metadata lookup
        dept_lookup = {d.department_id: {"name": d.department_name, "rate": float(d.cost_per_hour)} 
                       for d in self.db.query(Department).all()}

        # Total process median duration for BSI calculation
        case_totals = df.groupby("case_id")["duration_hours"].sum()
        median_total_proc_duration = float(case_totals.median()) if not case_totals.empty else 100.0
        total_unique_cases = df["case_id"].nunique()

        results = []
        for activity, act_group in df.groupby("activity_name"):
            # Exclude final completion marker
            if "Complete" in activity:
                continue

            durations = act_group["duration_hours"].values
            median_dur = float(np.median(durations))
            avg_dur = float(np.mean(durations))
            p90_dur = float(np.percentile(durations, 90))

            # Rework count = occurrences beyond 1 per case
            act_counts = act_group.groupby("case_id").size()
            rework_cases = (act_counts > 1).sum()
            rework_rate = float(rework_cases / total_unique_cases) if total_unique_cases > 0 else 0.0

            bsi = calculate_bottleneck_severity_index(median_dur, median_total_proc_duration, rework_rate)

            # Department and rate
            dept_id = act_group["department_id"].iloc[0]
            dept_info = dept_lookup.get(dept_id, {"name": dept_id, "rate": 50.0})
            dept_name = dept_info["name"]
            dept_rate = dept_info["rate"]

            # Excess duration compared to a standard 16-hour benchmark
            benchmark_target = 16.0
            excess_hours = np.maximum(0, durations - benchmark_target)
            total_excess = float(np.sum(excess_hours))
            cost_of_delay = float(total_excess * dept_rate)

            is_critical = bsi >= 0.28 or rework_rate >= 0.15

            results.append(BottleneckStage(
                stage_name=activity,
                department_id=dept_id,
                department_name=dept_name,
                median_duration_hours=round(median_dur, 2),
                avg_duration_hours=round(avg_dur, 2),
                p90_duration_hours=round(p90_dur, 2),
                rework_count=int(rework_cases),
                rework_rate_percent=round(rework_rate * 100.0, 2),
                bottleneck_severity_index=bsi,
                total_excess_hours=round(total_excess, 2),
                financial_cost_of_delay_usd=round(cost_of_delay, 2),
                is_critical_bottleneck=is_critical
            ))

        # Sort descending by Bottleneck Severity Index (BSI)
        results.sort(key=lambda x: x.bottleneck_severity_index, reverse=True)
        return results

    def get_department_metrics(self, process_id: str = "ONBOARD_V1") -> List[DepartmentMetric]:
        """
        Computes department-level throughput, breach contribution, and operational cost.
        """
        cases = self.db.query(ProcessInstance).filter(
            ProcessInstance.process_id == process_id,
            ProcessInstance.current_status == "COMPLETED"
        ).all()

        if not cases:
            return []

        dept_lookup = {d.department_id: {"name": d.department_name, "rate": float(d.cost_per_hour)} 
                       for d in self.db.query(Department).all()}

        dept_groups: Dict[str, List[ProcessInstance]] = {}
        for c in cases:
            dept_groups.setdefault(c.department_id, []).append(c)

        metrics = []
        for dept_id, dept_cases in dept_groups.items():
            durations = [c.total_duration_hours for c in dept_cases if c.total_duration_hours is not None]
            med_dur = float(np.median(durations)) if durations else 0.0
            avg_dur = float(np.mean(durations)) if durations else 0.0

            breached = sum(1 for c in dept_cases if c.is_sla_breached)
            breach_rate = (breached / len(dept_cases)) * 100.0 if dept_cases else 0.0

            dept_info = dept_lookup.get(dept_id, {"name": dept_id, "rate": 50.0})
            total_cost = sum(dur * dept_info["rate"] for dur in durations)

            metrics.append(DepartmentMetric(
                department_id=dept_id,
                department_name=dept_info["name"],
                total_cases_handled=len(dept_cases),
                median_handling_hours=round(med_dur, 2),
                avg_handling_hours=round(avg_dur, 2),
                sla_breach_rate_percent=round(breach_rate, 2),
                hourly_rate_usd=dept_info["rate"],
                total_operational_cost_usd=round(total_cost, 2)
            ))

        metrics.sort(key=lambda x: x.sla_breach_rate_percent, reverse=True)
        return metrics

    def get_sla_distribution(self, process_id: str = "ONBOARD_V1") -> SlaDistribution:
        """
        Returns SLA compliance breakdown by department and variant.
        """
        cases = self.db.query(ProcessInstance).filter(
            ProcessInstance.process_id == process_id,
            ProcessInstance.current_status == "COMPLETED"
        ).all()

        total = len(cases)
        if total == 0:
            return SlaDistribution(
                within_sla_count=0, breached_sla_count=0, compliance_rate_percent=100.0,
                breach_rate_percent=0.0, breaches_by_department={}, breaches_by_variant={}
            )

        breached = [c for c in cases if c.is_sla_breached]
        within = [c for c in cases if not c.is_sla_breached]

        by_dept: Dict[str, int] = {}
        for c in breached:
            by_dept[c.department_id] = by_dept.get(c.department_id, 0) + 1

        by_variant: Dict[str, int] = {}
        for c in breached:
            v_name = c.variant_id or "STANDARD"
            by_variant[v_name] = by_variant.get(v_name, 0) + 1

        return SlaDistribution(
            within_sla_count=len(within),
            breached_sla_count=len(breached),
            compliance_rate_percent=round((len(within) / total) * 100.0, 2),
            breach_rate_percent=round((len(breached) / total) * 100.0, 2),
            breaches_by_department=by_dept,
            breaches_by_variant=by_variant
        )
