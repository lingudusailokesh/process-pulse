import os
import sys
import random
from datetime import datetime, timedelta

# Add project root and backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.models.user import User, Department
from app.models.process import ProcessDefinition, ProcessInstance, ProcessEventLog
from app.core.security import get_password_hash
from app.core.anonymizer import pseudonymize_id

def seed_database(total_completed_cases: int = 470, total_active_cases: int = 30):
    print("[*] Initializing ProcessPulse Database Schema...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Seed Departments
        departments_data = [
            {"id": "HR", "name": "Human Resources", "rate": "45.00"},
            {"id": "IT", "name": "IT Infrastructure & Security", "rate": "70.00"},
            {"id": "OPS", "name": "Business Operations", "rate": "55.00"},
            {"id": "ENG", "name": "Engineering & Technology", "rate": "80.00"},
            {"id": "SALES", "name": "Sales & Client Delivery", "rate": "65.00"},
        ]
        
        for dept in departments_data:
            existing = db.query(Department).filter(Department.department_id == dept["id"]).first()
            if not existing:
                db.add(Department(
                    department_id=dept["id"],
                    department_name=dept["name"],
                    cost_per_hour=dept["rate"]
                ))
        db.commit()
        print("[+] Departments seeded.")

        # 2. Seed Default Process Definition
        proc_def = db.query(ProcessDefinition).filter(ProcessDefinition.process_id == "ONBOARD_V1").first()
        if not proc_def:
            proc_def = ProcessDefinition(
                process_id="ONBOARD_V1",
                process_name="Enterprise Employee Onboarding & Access Provisioning",
                description="Cross-functional onboarding lifecycle spanning HR verification, manager sign-off, and IT security provisioning.",
                sla_hours_target=120.0, # 5 Days (120 hrs)
                target_cost=320.00
            )
            db.add(proc_def)
            db.commit()
        print("[+] Process Definition (ONBOARD_V1) seeded.")

        # 3. Seed Default Application Users (for RBAC)
        demo_users = [
            {"id": "USR_ADMIN", "email": "admin@deloitte.com", "name": "Lead Engagement Manager", "role": "ADMIN"},
            {"id": "USR_CONSULTANT", "email": "consultant@deloitte.com", "name": "Technology Consultant", "role": "CONSULTANT"},
            {"id": "USR_EXEC", "email": "executive@deloitte.com", "name": "Managing Director / COO", "role": "EXECUTIVE_VIEWER"},
        ]
        for u in demo_users:
            existing_user = db.query(User).filter(User.email == u["email"]).first()
            if not existing_user:
                db.add(User(
                    user_id=u["id"],
                    email=u["email"],
                    hashed_password=get_password_hash("Deloitte2026!"),
                    full_name=u["name"],
                    role=u["role"],
                    is_active=True
                ))
        db.commit()
        print("[+] Application Users seeded (Password: Deloitte2026!).")

        # Clear existing cases if reseeding
        case_count = db.query(ProcessInstance).count()
        if case_count > 50:
            print(f"[i] Database already contains {case_count} cases. Skipping case generation.")
            return

        print(f"[*] Generating {total_completed_cases} completed cases and {total_active_cases} active cases...")

        dept_ids = ["HR", "IT", "OPS", "ENG", "SALES"]
        base_start_date = datetime(2026, 1, 5, 9, 0, 0)
        
        case_counter = 1001

        # -------------------------------------------------------------
        # Generate Completed Cases across 3 Variants
        # -------------------------------------------------------------
        for i in range(total_completed_cases):
            case_id = f"CASE_ONB_{case_counter}"
            case_counter += 1
            
            # Stagger start dates over the past 60 days
            days_offset = random.randint(0, 55)
            hours_offset = random.randint(8, 17)
            case_start = base_start_date + timedelta(days=days_offset, hours=hours_offset, minutes=random.randint(0, 59))
            
            dept = random.choice(dept_ids)
            requester_pseudonym = pseudonymize_id(f"EMP_{i+100}")
            
            # Determine Variant
            variant_roll = random.random()
            
            if variant_roll < 0.62:
                # Variant 1: Standard Happy Path (62%)
                variant_id = "VAR_1_HAPPY_PATH"
                events = [
                    ("Employee Request Submitted", 1, requester_pseudonym, dept, random.uniform(0.5, 2.0), 25.0),
                    ("Manager Approval", 2, pseudonymize_id(f"MGR_{dept}"), dept, random.uniform(4.0, 14.0), 40.0),
                    ("HR Verification", 3, pseudonymize_id("HR_OFFICER"), "HR", random.uniform(8.0, 22.0), 45.0),
                    ("IT Security Approval", 4, pseudonymize_id("IT_SEC_ENG"), "IT", random.uniform(16.0, 36.0), 70.0),
                    ("Access Provisioning", 5, pseudonymize_id("IT_ADMIN"), "IT", random.uniform(14.0, 30.0), 120.0),
                    ("Onboarding Completed", 6, "SYS_AUTOMATION", dept, random.uniform(0.1, 0.5), 0.0),
                ]
            elif variant_roll < 0.86:
                # Variant 2: IT Security Rejection / Rework Loop (24%) - High Latency / SLA Breach
                variant_id = "VAR_2_IT_REWORK_LOOP"
                events = [
                    ("Employee Request Submitted", 1, requester_pseudonym, dept, random.uniform(0.5, 2.0), 25.0),
                    ("Manager Approval", 2, pseudonymize_id(f"MGR_{dept}"), dept, random.uniform(6.0, 18.0), 40.0),
                    ("HR Verification", 3, pseudonymize_id("HR_OFFICER"), "HR", random.uniform(12.0, 28.0), 45.0),
                    ("IT Security Approval", 4, pseudonymize_id("IT_SEC_ENG"), "IT", random.uniform(36.0, 68.0), 70.0, "REJECTED"),
                    ("HR Verification", 5, pseudonymize_id("HR_OFFICER"), "HR", random.uniform(16.0, 32.0), 45.0, "REWORK_TRIGGERED"),
                    ("IT Security Approval", 6, pseudonymize_id("IT_SEC_ENG"), "IT", random.uniform(24.0, 48.0), 70.0),
                    ("Access Provisioning", 7, pseudonymize_id("IT_ADMIN"), "IT", random.uniform(20.0, 44.0), 120.0),
                    ("Onboarding Completed", 8, "SYS_AUTOMATION", dept, random.uniform(0.1, 0.5), 0.0),
                ]
            else:
                # Variant 3: Manager Approval Bypass / Fast Track (14%)
                variant_id = "VAR_3_MANAGER_BYPASS"
                events = [
                    ("Employee Request Submitted", 1, requester_pseudonym, dept, random.uniform(0.5, 2.0), 25.0),
                    ("HR Verification", 2, pseudonymize_id("HR_OFFICER"), "HR", random.uniform(8.0, 20.0), 45.0),
                    ("IT Security Approval", 3, pseudonymize_id("IT_SEC_ENG"), "IT", random.uniform(14.0, 32.0), 70.0),
                    ("Access Provisioning", 4, pseudonymize_id("IT_ADMIN"), "IT", random.uniform(12.0, 26.0), 120.0),
                    ("Onboarding Completed", 5, "SYS_AUTOMATION", dept, random.uniform(0.1, 0.5), 0.0),
                ]
            
            # Calculate event timestamps
            current_time = case_start
            total_duration = 0.0
            
            instance = ProcessInstance(
                case_id=case_id,
                process_id="ONBOARD_V1",
                requester_id=requester_pseudonym,
                department_id=dept,
                start_time=case_start,
                current_status="COMPLETED",
                variant_id=variant_id
            )
            db.add(instance)
            db.flush()
            
            for ev_item in events:
                act_name = ev_item[0]
                stage_order = ev_item[1]
                actor = ev_item[2]
                ev_dept = ev_item[3]
                duration_hrs = ev_item[4]
                cost = ev_item[5]
                status = ev_item[6] if len(ev_item) > 6 else "COMPLETED"
                
                current_time += timedelta(hours=duration_hrs)
                total_duration += duration_hrs
                
                event_log = ProcessEventLog(
                    case_id=case_id,
                    activity_name=act_name,
                    stage_order=stage_order,
                    actor_id=actor,
                    department_id=ev_dept,
                    event_timestamp=current_time,
                    activity_status=status,
                    cost_incurred=cost
                )
                db.add(event_log)
            
            instance.end_time = current_time
            instance.total_duration_hours = round(total_duration, 2)
            instance.is_sla_breached = total_duration > 120.0 # SLA is 120 hrs

        # -------------------------------------------------------------
        # Generate Active / In-Progress Cases (For Live Prediction Queue)
        # -------------------------------------------------------------
        for j in range(total_active_cases):
            case_id = f"CASE_ACT_{case_counter}"
            case_counter += 1
            
            # Started recently (1 to 5 days ago)
            hours_ago = random.uniform(12, 110)
            case_start = datetime.utcnow() - timedelta(hours=hours_ago)
            dept = random.choice(dept_ids)
            requester_pseudonym = pseudonymize_id(f"EMP_ACT_{j+500}")
            
            instance = ProcessInstance(
                case_id=case_id,
                process_id="ONBOARD_V1",
                requester_id=requester_pseudonym,
                department_id=dept,
                start_time=case_start,
                current_status="IN_PROGRESS",
                variant_id="VAR_IN_PROGRESS"
            )
            db.add(instance)
            db.flush()
            
            # Active stage progress
            stages = [
                ("Employee Request Submitted", 1, requester_pseudonym, dept, random.uniform(1.0, 3.0)),
                ("Manager Approval", 2, pseudonymize_id(f"MGR_{dept}"), dept, random.uniform(8.0, 35.0)),
                ("HR Verification", 3, pseudonymize_id("HR_OFFICER"), "HR", random.uniform(12.0, 45.0)),
            ]
            
            # Assign up to 2 or 3 completed stages
            num_stages = random.choice([1, 2, 3])
            cur_t = case_start
            for s_idx in range(num_stages):
                s_name, s_order, s_actor, s_dept, s_dur = stages[s_idx]
                cur_t += timedelta(hours=s_dur)
                event_log = ProcessEventLog(
                    case_id=case_id,
                    activity_name=s_name,
                    stage_order=s_order,
                    actor_id=s_actor,
                    department_id=s_dept,
                    event_timestamp=cur_t,
                    activity_status="COMPLETED",
                    cost_incurred=40.0
                )
                db.add(event_log)

        db.commit()
        print(f"[+] Successfully seeded {total_completed_cases + total_active_cases} onboarding cases with full event histories!")

    except Exception as e:
        db.rollback()
        print(f"[-] Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
