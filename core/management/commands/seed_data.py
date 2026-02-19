"""
V2 Seed Data — populates ALL 9 apps with realistic data for
Ramachandran Textiles & Jeyachandran Textiles.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
import random, json

from core.models import (
    Organization, Outlet, Team, Permission, Role, UserProfile, ActivityLog,
)
from projects.models import ProjectTag, Project
from tasks.models import TaskCategory, Task, TaskStep
from issues.models import Issue
from templates_lib.models import TemplateCategory, TemplateIndustry, TaskTemplate, TaskTemplateSubtask, ProjectTemplate
from forms_app.models import Form, FormResponse
from notifications.models import Notification
from reports.models import SavedReport


class Command(BaseCommand):
    help = "Seed database with comprehensive V2 data"

    # ── helpers ──────────────────────────────────────────────
    def _pick(self, lst, n=1):
        return random.sample(lst, min(n, len(lst)))

    def _rand_date(self, start=-15, end=30):
        return timezone.now() + timedelta(days=random.randint(start, end))

    # ── main ─────────────────────────────────────────────────
    def handle(self, *args, **options):
        self.stdout.write("🌱  Seeding V2 database …\n")

        # ════════════════ 1. ORGANIZATIONS ════════════════
        org1, _ = Organization.objects.get_or_create(code="RAMA", defaults={
            "name": "Ramachandran Textiles", "logo": "🏭",
            "address": "No. 25, Big Bazaar Street, Tirupur, Tamil Nadu 641601",
            "phone": "+91 98765 43210", "email": "info@ramachandrantextiles.com",
            "website": "https://ramachandrantextiles.com",
        })
        org2, _ = Organization.objects.get_or_create(code="JEYA", defaults={
            "name": "Jeyachandran Textiles", "logo": "🏬",
            "address": "No. 112, Sarada College Road, Salem, Tamil Nadu 636007",
            "phone": "+91 98765 43211", "email": "info@jeyachandrantextiles.com",
            "website": "https://jeyachandrantextiles.com",
        })
        self.stdout.write(f"  ✓ Organizations: {org1.name}, {org2.name}")

        # ════════════════ 2. OUTLETS ════════════════
        rama_outlets_data = [
            ("Attakulangara Store", "RAMA-ATK", "Attakulangara, Trivandrum 695001", "+91 471 2461234"),
            ("Attingal SM", "RAMA-ATG", "Main Road, Attingal, Trivandrum 695101", "+91 470 2621234"),
            ("Haripad Store", "RAMA-HRP", "TB Road, Haripad, Alappuzha 690514", "+91 479 2412345"),
            ("Kayamkulam Store", "RAMA-KYM", "High School Junction, Kayamkulam 690502", "+91 479 2442345"),
            ("Kollam Showroom", "RAMA-KLM", "Chinnakada, Kollam 691001", "+91 474 2742345"),
            ("Kottarakkara Store", "RAMA-KTR", "Main Road, Kottarakkara 691506", "+91 474 2522345"),
            ("Nagercoil Store", "RAMA-NGC", "Court Road, Nagercoil 629001", "+91 4652 231234"),
            ("Tirunelveli SM", "RAMA-TLV", "High Ground, Tirunelveli 627001", "+91 462 2334567"),
        ]
        jeya_outlets_data = [
            ("T Nagar Showroom", "JEYA-TNG", "Usman Road, T Nagar, Chennai 600017", "+91 44 24341234"),
            ("Pondy Bazaar Store", "JEYA-PBZ", "Pondy Bazaar, T Nagar, Chennai 600017", "+91 44 24351234"),
            ("Salem Main Store", "JEYA-SLM", "Sarada College Road, Salem 636007", "+91 427 2261234"),
            ("Coimbatore Store", "JEYA-CBE", "Oppanakara Street, Coimbatore 641001", "+91 422 2391234"),
            ("Madurai Store", "JEYA-MDU", "Town Hall Road, Madurai 625001", "+91 452 2341234"),
            ("Erode Showroom", "JEYA-ERD", "Brough Road, Erode 638001", "+91 424 2241234"),
            ("Tirupur Store", "JEYA-TPR", "Kumaran Road, Tirupur 641601", "+91 421 2241234"),
            ("Trichy Showroom", "JEYA-TCH", "Main Guard Gate, Trichy 620001", "+91 431 2411234"),
        ]

        rama_outlets, jeya_outlets = [], []
        for name, code, addr, phone in rama_outlets_data:
            o, _ = Outlet.objects.get_or_create(organization=org1, name=name, defaults={
                "code": code, "address": addr, "phone": phone})
            rama_outlets.append(o)
        for name, code, addr, phone in jeya_outlets_data:
            o, _ = Outlet.objects.get_or_create(organization=org2, name=name, defaults={
                "code": code, "address": addr, "phone": phone})
            jeya_outlets.append(o)
        self.stdout.write(f"  ✓ Outlets: {len(rama_outlets)} (RAMA) + {len(jeya_outlets)} (JEYA)")

        # ════════════════ 3. TEAMS ════════════════
        teams_data = [
            ("Maintenance", "#ef4444"), ("IT Department", "#3b82f6"),
            ("Sales Team", "#22c55e"), ("Warehouse Team", "#f59e0b"),
            ("Design & Display", "#ec4899"), ("Accounts", "#8b5cf6"),
            ("HR & Admin", "#06b6d4"), ("Quality Control", "#f97316"),
        ]
        rama_teams, jeya_teams = [], []
        for name, color in teams_data:
            t, _ = Team.objects.get_or_create(organization=org1, name=name, defaults={"color": color})
            rama_teams.append(t)
        for name, color in teams_data:
            t, _ = Team.objects.get_or_create(organization=org2, name=name, defaults={"color": color})
            jeya_teams.append(t)
        self.stdout.write(f"  ✓ Teams: {len(rama_teams)} per org")

        # ════════════════ 4. PERMISSIONS ════════════════
        perms_data = [
            ("View Dashboard", "view_dashboard", "dashboard"),
            ("View Reports", "view_reports", "reports"),
            ("Export Reports", "export_reports", "reports"),
            ("View Projects", "view_projects", "projects"),
            ("Create Project", "create_project", "projects"),
            ("Edit Project", "edit_project", "projects"),
            ("Delete Project", "delete_project", "projects"),
            ("View Tasks", "view_tasks", "tasks"),
            ("Create Task", "create_task", "tasks"),
            ("Edit Task", "edit_task", "tasks"),
            ("Delete Task", "delete_task", "tasks"),
            ("Assign Task", "assign_task", "tasks"),
            ("Change Task Status", "change_task_status", "tasks"),
            ("View Issues", "view_issues", "issues"),
            ("Create Issue", "create_issue", "issues"),
            ("Edit Issue", "edit_issue", "issues"),
            ("View Templates", "view_templates", "templates"),
            ("Create Template", "create_template", "templates"),
            ("View Forms", "view_forms", "forms"),
            ("Create Form", "create_form", "forms"),
            ("View Users", "view_users", "users"),
            ("Create User", "create_user", "users"),
            ("Edit User", "edit_user", "users"),
            ("Delete User", "delete_user", "users"),
            ("View Roles", "view_roles", "roles"),
            ("Create Role", "create_role", "roles"),
            ("Manage Outlets", "manage_outlets", "outlets"),
            ("Use AI Assistant", "use_ai", "ai"),
            ("AI Suggestions", "ai_suggestions", "ai"),
            ("Manage Settings", "manage_settings", "settings"),
        ]
        all_perms = []
        for name, codename, module in perms_data:
            p, _ = Permission.objects.get_or_create(codename=codename, defaults={
                "name": name, "description": f"{name} permission", "module": module})
            all_perms.append(p)
        self.stdout.write(f"  ✓ Permissions: {len(all_perms)}")

        # ════════════════ 5. ROLES ════════════════
        for org in [org1, org2]:
            admin_r, c = Role.objects.get_or_create(organization=org, name="Administrator",
                defaults={"description": "Full access"})
            if c: admin_r.permissions.set(all_perms)

            mgr_codes = [p for p in all_perms if p.codename not in (
                "delete_user", "delete_project", "manage_settings", "create_role")]
            mgr_r, c = Role.objects.get_or_create(organization=org, name="Manager",
                defaults={"description": "Manage tasks & team"})
            if c: mgr_r.permissions.set(mgr_codes)

            emp_codes = [p for p in all_perms if p.module in ("dashboard", "tasks", "issues", "forms", "ai")]
            emp_r, c = Role.objects.get_or_create(organization=org, name="Employee",
                defaults={"description": "Basic access"})
            if c: emp_r.permissions.set(emp_codes)

            view_codes = [p for p in all_perms if p.codename.startswith("view_")]
            vw_r, c = Role.objects.get_or_create(organization=org, name="Viewer",
                defaults={"description": "Read-only"})
            if c: vw_r.permissions.set(view_codes)
        self.stdout.write("  ✓ Roles created (4 per org)")

        # ════════════════ 6. USERS ════════════════
        colors = ["#6366f1", "#ec4899", "#8b5cf6", "#06b6d4", "#f59e0b", "#10b981", "#ef4444", "#f97316"]

        users_spec = [
            # (username, first, last, email, org, role, emp_id, dept, desig, outlet_idx, team_idx)
            ("rama_admin", "Ramesh", "Kumar", "ramesh@rama.com", org1, "Administrator", "R001", "Management", "Admin", 0, None),
            ("rama_mgr1", "Selvam", "Rajan", "selvam@rama.com", org1, "Manager", "R002", "Operations", "Ops Manager", 0, 0),
            ("rama_mgr2", "Anitha", "Devi", "anitha@rama.com", org1, "Manager", "R003", "Sales", "Sales Head", 1, 2),
            ("rama_emp1", "Priya", "Lakshmi", "priya@rama.com", org1, "Employee", "R004", "Production", "Production Lead", 2, 7),
            ("rama_emp2", "Karthik", "Raja", "karthik@rama.com", org1, "Employee", "R005", "Sales", "Sales Executive", 3, 2),
            ("rama_emp3", "Meena", "Subbu", "meena@rama.com", org1, "Employee", "R006", "Quality", "QC Inspector", 4, 7),
            ("rama_emp4", "Vijay", "Prasad", "vijay@rama.com", org1, "Employee", "R007", "IT", "IT Support", 5, 1),
            ("rama_emp5", "Deepa", "Kannan", "deepa@rama.com", org1, "Employee", "R008", "Design", "Display Artist", 6, 4),
            ("rama_emp6", "Suresh", "Babu", "suresh@rama.com", org1, "Employee", "R009", "Warehouse", "Store Keeper", 7, 3),
            ("rama_emp7", "Revathi", "Nair", "revathi@rama.com", org1, "Employee", "R010", "Accounts", "Accountant", 0, 5),

            ("jeya_admin", "Jeyaraj", "Pillai", "jeyaraj@jeya.com", org2, "Administrator", "J001", "Management", "Admin", 0, None),
            ("jeya_mgr1", "Rajan", "Murugan", "rajan@jeya.com", org2, "Manager", "J002", "Operations", "Branch Manager", 0, 0),
            ("jeya_mgr2", "Kavitha", "Sundaram", "kavitha@jeya.com", org2, "Manager", "J003", "Sales", "Regional Head", 1, 2),
            ("jeya_emp1", "Lakshmi", "Narayan", "lakshmi@jeya.com", org2, "Employee", "J004", "Weaving", "Weaver Lead", 2, 7),
            ("jeya_emp2", "Venkat", "Subramani", "venkat@jeya.com", org2, "Employee", "J005", "Sales", "Sales Manager", 3, 2),
            ("jeya_emp3", "Divya", "Bharathi", "divya@jeya.com", org2, "Employee", "J006", "Design", "Lead Designer", 4, 4),
            ("jeya_emp4", "Manoj", "Pandian", "manoj@jeya.com", org2, "Employee", "J007", "IT", "IT Coordinator", 5, 1),
            ("jeya_emp5", "Saranya", "Vel", "saranya@jeya.com", org2, "Employee", "J008", "Warehouse", "Inventory Exec", 6, 3),
            ("jeya_emp6", "Ganesh", "Iyer", "ganesh@jeya.com", org2, "Employee", "J009", "Accounts", "Sr. Accountant", 7, 5),
            ("jeya_emp7", "Nithya", "Ravi", "nithya@jeya.com", org2, "Employee", "J010", "HR", "HR Executive", 0, 6),
        ]

        profiles_map = {}   # username -> profile
        for uname, fn, ln, email, org, role_name, eid, dept, desig, o_idx, t_idx in users_spec:
            user, created = User.objects.get_or_create(username=uname, defaults={
                "first_name": fn, "last_name": ln, "email": email})
            if created:
                user.set_password("password123")
                user.save()

            outlets_list = rama_outlets if org == org1 else jeya_outlets
            teams_list = rama_teams if org == org1 else jeya_teams
            role = Role.objects.get(organization=org, name=role_name)
            profile, _ = UserProfile.objects.get_or_create(user=user, defaults={
                "organization": org, "role": role, "employee_id": eid,
                "department": dept, "designation": desig,
                "avatar_color": random.choice(colors),
                "outlet": outlets_list[o_idx],
                "team": teams_list[t_idx] if t_idx is not None else None,
                "points": random.randint(0, 500),
            })
            profiles_map[uname] = profile

        rama_profiles = [p for u, p in profiles_map.items() if u.startswith("rama")]
        jeya_profiles = [p for u, p in profiles_map.items() if u.startswith("jeya")]
        self.stdout.write(f"  ✓ Users: {len(profiles_map)}")

        # ════════════════ 7. PROJECT TAGS ════════════════
        tag_names = [
            ("Seasonal", "#f59e0b"), ("Renovation", "#3b82f6"), ("Marketing", "#ec4899"),
            ("Compliance", "#ef4444"), ("Digital", "#8b5cf6"), ("Expansion", "#22c55e"),
        ]
        for org in [org1, org2]:
            for name, color in tag_names:
                ProjectTag.objects.get_or_create(organization=org, name=name, defaults={"color": color})
        self.stdout.write("  ✓ Project tags")

        # ════════════════ 8. PROJECTS ════════════════
        projects_spec = [
            ("Pongal 2025 Collection Launch", "Plan & execute the Pongal seasonal collection across all stores", "active", org1),
            ("POS System Upgrade", "Upgrade point-of-sale hardware and software in all outlets", "active", org1),
            ("Annual Stock Audit FY-25", "Complete physical stock verification across all warehouses", "active", org1),
            ("New Nagercoil Branch Setup", "End-to-end setup of the new Nagercoil outlet", "completed", org1),
            ("Staff Training Q1-2025", "Quarterly skill development programme for all staff", "on_hold", org1),

            ("Deepavali Mega Sale 2025", "Plan the annual Deepavali sale event across all branches", "active", org2),
            ("E-commerce Portal Launch", "Develop and launch online shopping portal", "active", org2),
            ("Trichy Showroom Renovation", "Complete interior renovation of Trichy branch", "active", org2),
            ("ERP Migration", "Migrate from legacy system to cloud ERP", "on_hold", org2),
            ("Quality Certification ISO 9001", "Achieve ISO 9001 certification for manufacturing", "active", org2),
        ]

        all_projects = []
        for name, desc, status, org in projects_spec:
            profs = rama_profiles if org == org1 else jeya_profiles
            outlets_list = rama_outlets if org == org1 else jeya_outlets
            p, created = Project.objects.get_or_create(organization=org, name=name, defaults={
                "description": desc, "status": status,
                "created_by": profs[0],
                "outlet": random.choice(outlets_list),
                "start_date": (date.today() - timedelta(days=random.randint(5, 60))),
                "end_date": (date.today() + timedelta(days=random.randint(15, 120))),
            })
            if created:
                p.members.set(self._pick(profs, 4))
                tags = ProjectTag.objects.filter(organization=org)
                p.tags.set(self._pick(list(tags), 2))
            all_projects.append(p)
        self.stdout.write(f"  ✓ Projects: {len(all_projects)}")

        # ════════════════ 9. TASK CATEGORIES ════════════════
        cat_data = [
            ("Production", "#ef4444", "🏭"), ("Quality Control", "#f59e0b", "✅"),
            ("Sales & Marketing", "#3b82f6", "📈"), ("Inventory", "#8b5cf6", "📦"),
            ("HR & Admin", "#06b6d4", "👥"), ("Finance", "#10b981", "💰"),
            ("Logistics", "#f97316", "🚚"), ("Design & Display", "#ec4899", "🎨"),
            ("IT & Systems", "#6366f1", "💻"), ("Maintenance", "#84cc16", "🔧"),
        ]
        for org in [org1, org2]:
            for name, color, icon in cat_data:
                TaskCategory.objects.get_or_create(organization=org, name=name,
                    defaults={"color": color, "icon": icon})
        self.stdout.write("  ✓ Task categories")

        # ════════════════ 10. TASKS ════════════════
        rama_tasks = [
            ("Review cotton fabric quality for Q1 shipment", "high", "in_progress", "Quality Control", 0),
            ("Update barcode labels for Pongal collection", "medium", "todo", "Inventory", 0),
            ("Prepare monthly sales report — February", "high", "review", "Sales & Marketing", None),
            ("Schedule vendor meeting for silk procurement", "medium", "todo", "Production", None),
            ("Conduct annual fire safety drill", "critical", "todo", "HR & Admin", None),
            ("Design Pongal collection store banner", "high", "in_progress", "Design & Display", 0),
            ("Audit warehouse stock levels", "medium", "completed", "Inventory", 2),
            ("Client presentation — Chennai retail chain", "critical", "in_progress", "Sales & Marketing", None),
            ("Integrate biometric attendance system", "low", "on_hold", "IT & Systems", 1),
            ("Process supplier invoices — January", "high", "todo", "Finance", None),
            ("Optimize fabric cutting process", "medium", "in_progress", "Production", None),
            ("Plan logistics for Delhi exhibition", "high", "todo", "Logistics", None),
            ("Replace AC units at Attingal store", "medium", "todo", "Maintenance", None),
            ("POS terminal software update", "high", "in_progress", "IT & Systems", 1),
            ("Recruit new billing staff — Kollam", "medium", "todo", "HR & Admin", None),
            ("Prepare GST filing Q3 FY25", "critical", "review", "Finance", None),
            ("Restock fast-moving SKUs", "high", "todo", "Inventory", 2),
            ("Train sales staff on upselling", "medium", "scheduled", "HR & Admin", 4),
            ("Setup CCTV at Haripad store", "high", "in_progress", "IT & Systems", None),
            ("Arrange Thiruvonam special display", "low", "todo", "Design & Display", None),
        ]
        jeya_tasks = [
            ("Inspect Kanchipuram silk weaving quality", "high", "in_progress", "Quality Control", 0),
            ("Launch online store promotions — March", "medium", "todo", "Sales & Marketing", 1),
            ("Post job openings for Trichy branch", "medium", "in_progress", "HR & Admin", None),
            ("Negotiate eco-friendly dye pricing", "high", "todo", "Production", None),
            ("Prepare GST filing Q4 FY25", "critical", "review", "Finance", None),
            ("Redesign Salem showroom layout", "medium", "in_progress", "Design & Display", 2),
            ("Roll out barcode scanning — 3 warehouses", "high", "todo", "Inventory", 1),
            ("Customer feedback analysis — monthly", "medium", "completed", "Sales & Marketing", None),
            ("Train retail staff on new POS system", "high", "in_progress", "HR & Admin", None),
            ("Optimize delivery routes — 20% target", "medium", "todo", "Logistics", None),
            ("Update fabric testing protocols (ISO)", "low", "on_hold", "Quality Control", 4),
            ("Annual budget planning FY 2026-27", "critical", "todo", "Finance", None),
            ("Fix water leakage — Coimbatore store", "high", "in_progress", "Maintenance", None),
            ("Setup e-commerce payment gateway", "critical", "in_progress", "IT & Systems", 1),
            ("Erode branch deep cleaning schedule", "medium", "scheduled", "Maintenance", None),
            ("Stock transfer — Madurai to Trichy", "high", "todo", "Logistics", None),
            ("Social media content calendar — Q2", "medium", "todo", "Sales & Marketing", 1),
            ("Employee appraisal cycle — Q1", "high", "review", "HR & Admin", None),
            ("Backup server maintenance", "low", "todo", "IT & Systems", None),
            ("Plan Deepavali sale layout — all stores", "critical", "todo", "Design & Display", 0),
        ]

        all_tasks = []
        for task_list, org, profs, out_list, proj_list in [
            (rama_tasks, org1, rama_profiles, rama_outlets, all_projects[:5]),
            (jeya_tasks, org2, jeya_profiles, jeya_outlets, all_projects[5:]),
        ]:
            for title, prio, status, cat_name, proj_idx in task_list:
                cat = TaskCategory.objects.filter(organization=org, name=cat_name).first()
                creator = profs[0]
                proj = proj_list[proj_idx] if proj_idx is not None else None
                t, created = Task.objects.get_or_create(organization=org, title=title, defaults={
                    "description": f"Task: {title}",
                    "status": status, "priority": prio, "category": cat,
                    "created_by": creator, "project": proj,
                    "outlet": random.choice(out_list),
                    "team": random.choice(rama_teams if org == org1 else jeya_teams),
                    "due_date": self._rand_date(-5, 25),
                    "start_date": self._rand_date(-20, -1),
                    "points": random.choice([0, 5, 10, 15, 20, 25]),
                    "completed_at": timezone.now() if status == "completed" else None,
                })
                if created:
                    t.assigned_to.set(self._pick(profs, random.randint(1, 3)))
                    # add steps to some tasks
                    if random.random() < 0.4:
                        for idx, step_title in enumerate([
                            "Preparation", "Execution", "Quality Check", "Sign Off"
                        ]):
                            TaskStep.objects.create(task=t, title=step_title, order=idx,
                                is_completed=(idx == 0 and status != "todo"))
                all_tasks.append(t)

        self.stdout.write(f"  ✓ Tasks: {len(all_tasks)}")

        # ════════════════ 11. ISSUES ════════════════
        rama_issues = [
            ("AC not working in billing section — Attakulangara", "critical", "open"),
            ("Stock mismatch — Kayamkulam warehouse", "high", "open"),
            ("Customer complaint: wrong saree packed", "high", "resolved"),
            ("POS network down at Kollam Showroom", "critical", "open"),
            ("Water dripping near electrical panel — Haripad", "critical", "open"),
            ("Delivery delayed — Tirunelveli bulk order", "medium", "resolved"),
            ("Employee late attendance pattern — Attingal", "low", "ignored"),
            ("Damaged goods received from vendor", "high", "open"),
        ]
        jeya_issues = [
            ("Power outage impacting server room — Salem", "critical", "open"),
            ("Return policy dispute — unhappy customer at T Nagar", "high", "open"),
            ("Inventory sync failure between Coimbatore and Madurai", "high", "open"),
            ("Pest issue in fabric storage — Erode", "medium", "resolved"),
            ("Staff shortage during peak hours — Pondy Bazaar", "medium", "open"),
            ("Payment gateway timeout errors on website", "critical", "open"),
            ("CCTV camera offline — Trichy Showroom", "high", "open"),
            ("Wrong price tags printed — Tirupur Store", "low", "resolved"),
        ]
        all_issues = []
        for issue_list, org, profs, out_list in [
            (rama_issues, org1, rama_profiles, rama_outlets),
            (jeya_issues, org2, jeya_profiles, jeya_outlets),
        ]:
            for title, prio, status in issue_list:
                i, created = Issue.objects.get_or_create(organization=org, title=title, defaults={
                    "description": f"Issue: {title}",
                    "priority": prio, "status": status,
                    "created_by": profs[0],
                    "outlet": random.choice(out_list),
                    "team": random.choice(rama_teams if org == org1 else jeya_teams),
                    "resolved_at": timezone.now() if status == "resolved" else None,
                })
                if created:
                    i.assigned_to.set(self._pick(profs, 2))
                all_issues.append(i)
        self.stdout.write(f"  ✓ Issues: {len(all_issues)}")

        # ════════════════ 12. TEMPLATE LIBRARY ════════════════
        tpl_cats = []
        for name, color in [("Stock Check", "#22c55e"), ("Audit", "#f59e0b"), ("Cleaning", "#3b82f6"),
                             ("Compliance", "#ef4444"), ("Opening Routine", "#8b5cf6"), ("Closing Routine", "#ec4899")]:
            tc, _ = TemplateCategory.objects.get_or_create(name=name, defaults={"color": color})
            tpl_cats.append(tc)

        tpl_industries = []
        for name in ["Textiles", "Retail", "Manufacturing", "Logistics", "Food & Beverage"]:
            ti, _ = TemplateIndustry.objects.get_or_create(name=name)
            tpl_industries.append(ti)

        task_tpls = [
            ("Daily Store Opening Checklist", "Standard opening routine", "high", "Opening Routine",
             ["Unlock store", "Switch on lights & AC", "Check POS system", "Verify cash float", "Arrange display"]),
            ("Daily Store Closing Checklist", "Standard closing routine", "high", "Closing Routine",
             ["Clear billing counter", "Count cash register", "Lock display cabinets", "Switch off AC & lights", "Set alarm"]),
            ("Weekly Stock Audit", "Manual stock count for fast-movers", "medium", "Stock Check",
             ["Print stock list", "Count items per shelf", "Record discrepancies", "Update system", "Report to manager"]),
            ("Monthly Fire Safety Check", "Safety equipment inspection", "critical", "Compliance",
             ["Check fire extinguishers", "Test fire alarm", "Inspect emergency exits", "Verify first-aid kit", "Update log"]),
            ("Deep Cleaning Schedule", "Thorough store cleaning routine", "medium", "Cleaning",
             ["Dust all shelves", "Mop floors", "Clean washrooms", "Wipe glass panels", "Sanitise billing area"]),
        ]
        for org in [org1, org2]:
            for name, desc, prio, cat_name, subtask_titles in task_tpls:
                cat = next((c for c in tpl_cats if c.name == cat_name), None)
                tt, created = TaskTemplate.objects.get_or_create(organization=org, name=name, defaults={
                    "description": desc, "priority": prio, "category": cat,
                    "created_by": rama_profiles[0] if org == org1 else jeya_profiles[0],
                })
                if created:
                    tt.industries.set(tpl_industries[:2])
                    for idx, st in enumerate(subtask_titles):
                        TaskTemplateSubtask.objects.create(template=tt, title=st, order=idx)

            ProjectTemplate.objects.get_or_create(organization=org, name="New Store Launch",
                defaults={"description": "Template for launching a new retail store",
                          "created_by": rama_profiles[0] if org == org1 else jeya_profiles[0]})
        self.stdout.write("  ✓ Templates (task + project)")

        # ════════════════ 13. FORMS ════════════════
        forms_spec = [
            ("Daily Sales Report", "Submit daily sales figures", [
                {"name": "total_sales", "type": "number", "label": "Total Sales (₹)", "required": True},
                {"name": "customers_count", "type": "number", "label": "No. of Customers"},
                {"name": "top_product", "type": "text", "label": "Top Selling Product"},
                {"name": "remarks", "type": "textarea", "label": "Remarks"},
            ]),
            ("Customer Complaint Form", "Log customer complaints", [
                {"name": "customer_name", "type": "text", "label": "Customer Name", "required": True},
                {"name": "phone", "type": "text", "label": "Phone Number"},
                {"name": "complaint_type", "type": "select", "label": "Type",
                 "options": ["Product Quality", "Service", "Billing", "Delivery", "Other"]},
                {"name": "description", "type": "textarea", "label": "Description", "required": True},
            ]),
            ("Maintenance Request", "Report maintenance issues", [
                {"name": "location", "type": "text", "label": "Location / Section", "required": True},
                {"name": "issue_type", "type": "select", "label": "Issue Type",
                 "options": ["Electrical", "Plumbing", "AC/HVAC", "Furniture", "Other"]},
                {"name": "urgency", "type": "select", "label": "Urgency", "options": ["Low", "Medium", "High", "Critical"]},
                {"name": "description", "type": "textarea", "label": "Description"},
                {"name": "photo_url", "type": "text", "label": "Photo URL (optional)"},
            ]),
        ]
        for org, profs, out_list in [(org1, rama_profiles, rama_outlets), (org2, jeya_profiles, jeya_outlets)]:
            for name, desc, fields in forms_spec:
                f, created = Form.objects.get_or_create(organization=org, name=name, defaults={
                    "description": desc, "status": "published",
                    "fields_schema": fields,
                    "created_by": profs[0],
                    "outlet": random.choice(out_list),
                })
                if created:
                    f.assigned_to.set(self._pick(profs, 4))
                    sample_data = {fld["name"]: "Sample value" for fld in fields}
                    FormResponse.objects.create(form=f, submitted_by=random.choice(profs),
                        data=sample_data, status="submitted", submitted_at=timezone.now())
        self.stdout.write("  ✓ Forms + sample responses")

        # ════════════════ 14. NOTIFICATIONS ════════════════
        notif_types = [
            ("task_assigned", "New Task Assigned", "You have been assigned: {task}"),
            ("task_overdue", "Task Overdue", "The task '{task}' is past its due date"),
            ("issue_created", "New Issue Reported", "A new issue has been created: {issue}"),
            ("system", "Welcome!", "Welcome to Task Manager V2. Explore the dashboard!"),
            ("reminder", "Daily Reminder", "You have pending tasks due today"),
        ]
        for prof in list(profiles_map.values()):
            for ntype, title, msg in random.sample(notif_types, 3):
                Notification.objects.get_or_create(
                    user=prof, title=title, notification_type=ntype,
                    defaults={
                        "organization": prof.organization,
                        "message": msg.format(
                            task=random.choice(all_tasks).title if all_tasks else "N/A",
                            issue=random.choice(all_issues).title if all_issues else "N/A",
                        ),
                        "link": "/dashboard/",
                        "is_read": random.choice([True, False]),
                    })
        self.stdout.write("  ✓ Notifications")

        # ════════════════ 15. SAVED REPORTS ════════════════
        for org, profs in [(org1, rama_profiles), (org2, jeya_profiles)]:
            for rtype in ["outlet_tasks", "employee_tasks", "backlog"]:
                SavedReport.objects.get_or_create(
                    organization=org, user=profs[0], report_type=rtype,
                    defaults={"name": f"{dict(SavedReport.REPORT_TYPE_CHOICES).get(rtype, rtype)}"})
        self.stdout.write("  ✓ Saved reports")

        # ════════════════ 16. ACTIVITY LOG ════════════════
        for org, profs in [(org1, rama_profiles), (org2, jeya_profiles)]:
            activities = [
                ("created", "task", "Created a new task"),
                ("updated", "project", "Updated project status"),
                ("status_changed", "task", "Changed task status to completed"),
                ("assigned", "task", "Assigned task to team member"),
                ("created", "issue", "Reported a new issue"),
                ("login", "user", "User logged in"),
            ]
            for action, entity_type, details in activities:
                ActivityLog.objects.get_or_create(
                    organization=org, action=action, entity_type=entity_type,
                    details=details,
                    defaults={"user": random.choice(profs)})
        self.stdout.write("  ✓ Activity log entries")

        # ════════════════ DONE ════════════════
        self.stdout.write(self.style.SUCCESS("\n✅  V2 database seeded successfully!\n"))
        self.stdout.write("📋  Login credentials (all passwords: password123):")
        self.stdout.write("    rama_admin  — Ramachandran Admin")
        self.stdout.write("    rama_mgr1   — Ramachandran Manager")
        self.stdout.write("    jeya_admin  — Jeyachandran Admin")
        self.stdout.write("    jeya_mgr1   — Jeyachandran Manager\n")
