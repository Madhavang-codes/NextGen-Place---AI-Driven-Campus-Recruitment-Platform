from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.db import IntegrityError
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.core.mail import send_mail
from django.conf import settings
import hashlib
from .utils.job_parser import parse_job_fields
from django.contrib import messages
from .models import Job, JobApplication, StudentProfile, EmployerProfile
from .utils.resume_parser import extract_skills
from django.db.models import Count, Q





# ================= ROLE CHECKS =================
def is_student(user):
    return hasattr(user, "student_profile")

def is_employer(user):
    return hasattr(user, "employer_profile")

def is_admin(user):
    return user.is_staff or user.is_superuser


# ================= HOME =================
def home(request):
    return render(request, "index.html")


# ================= REGISTER =================
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role")

        if not username or not password or not role:
            return render(request, "register.html", {"error": "All fields are required"})

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {"error": "Username already exists"})

        user = User.objects.create_user(username=username, password=password)

        if role == "student":
            StudentProfile.objects.create(user=user)
        else:
            EmployerProfile.objects.create(user=user)

        return redirect("login")

    return render(request, "register.html")


# ================= LOGIN =================
def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password")
        )

        if not user:
            return render(request, "login.html", {"error": "Invalid credentials"})

        login(request, user)

        if is_admin(user):
            return redirect("admin_dashboard")

        if is_employer(user):
            return redirect("employer_dashboard")

        if not user.student_profile.is_verified:
            return redirect("student_verification")

        return redirect("student_dashboard")

    return render(request, "login.html")


# ================= LOGOUT =================
def logout_view(request):
    logout(request)
    return redirect("login")


# ================= JOB LIST =================
@login_required
def job_list(request):
    jobs = Job.objects.all().order_by("-posted_date")

    for job in jobs:
        parse_job_fields(job)   # ✅ attach dynamic fields

    return render(request, "job_list.html", {"jobs": jobs})


# ================= STUDENT VERIFICATION =================
@login_required
@user_passes_test(is_student)
def student_verification(request):
    profile = request.user.student_profile

    if profile.is_verified:
        return redirect("student_dashboard")

    if request.method == "POST":
        profile.register_number = request.POST.get("register_number")
        profile.full_name = request.POST.get("full_name")
        profile.department = request.POST.get("department")
        profile.academic_year = request.POST.get("academic_year")
        profile.student_email = request.POST.get("student_email")
        profile.is_verified = True
        profile.save()

        return redirect("student_dashboard")

    return render(request, "student_verification.html")


# ================= UPLOAD RESUME =================
@login_required
@user_passes_test(is_student)
def upload_resume(request):
    profile = request.user.student_profile

    if request.method == "POST":
        resume = request.FILES.get("resume")
        profile.resume = resume

        resume_bytes = resume.read()
        resume_hash = hashlib.sha256(resume_bytes).hexdigest()
        resume.seek(0)

        profile.resume_hash = resume_hash

        duplicate = StudentProfile.objects.filter(
            resume_hash=resume_hash
        ).exclude(user=request.user).first()

        if duplicate:
            profile.is_resume_fake = True
            profile.resume_similarity_score = 100.0
            profile.resume_warning = (
                "⚠ This resume matches another student's resume. "
                "Job recommendations are blocked."
            )
        else:
            profile.is_resume_fake = False
            profile.resume_similarity_score = 0.0
            profile.resume_warning = ""

        profile.save()
        return redirect("student_dashboard")

    return render(request, "upload_resume.html")


# ================= STUDENT DASHBOARD =================
@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    profile = request.user.student_profile

    # -------------------------------
    # 1. Verification checks
    # -------------------------------
    if not profile.is_verified:
        return redirect("student_verification")

    if not profile.resume:
        return redirect("upload_resume")

    # -------------------------------
    # 2. Extract skills from resume (AI layer)
    # -------------------------------
    raw_skills = extract_skills(profile.resume.path)

    # normalize → set for fast matching
    student_skills = {
        skill.strip().lower()
        for skill in raw_skills
        if skill.strip()
    }

    # -------------------------------
    # 3. Applied jobs
    # -------------------------------
    applied_jobs = JobApplication.objects.filter(user=request.user)
    applied_ids = applied_jobs.values_list("job_id", flat=True)

    # -------------------------------
    # 4. Recommend jobs based on skill intersection
    # -------------------------------
    recommended_jobs = []

    for job in Job.objects.exclude(id__in=applied_ids):

        job_skills = {
            s.strip().lower()
            for s in job.skills_required.replace("/", ",").split(",")
            if s.strip()
        }

        matched_skills = student_skills & job_skills

        if not matched_skills:
            continue

    # -------------------------------
    # Attach matched skills
    # -------------------------------
        job.matched_skills = sorted(matched_skills)

        parse_job_fields(job)

    # -------------------------------
    # Append ONCE
    # -------------------------------
        recommended_jobs.append(job)
    # -------------------------------
    # 5. Render dashboard
    # -------------------------------
    return render(request, "student_dashboard.html", {
        "student": profile,
        "recommended_jobs": recommended_jobs,
        "applied_jobs": applied_jobs,
        "warning": profile.resume_warning,
    })


# ================= APPLY JOB =================
@login_required
@user_passes_test(is_student)
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    JobApplication.objects.get_or_create(
        user=request.user,
        job=job
    )
    return redirect("student_dashboard")

# ================= EMPLOYER =================
@login_required
@user_passes_test(is_employer)
def employer_dashboard(request):
    employer_profile = request.user.employer_profile

    return render(request, "employer_dashboard.html", {
        "jobs": Job.objects.filter(employer=employer_profile),
        "profile_complete": employer_profile.is_complete
    })


@login_required
@user_passes_test(is_employer)
def complete_employer_profile(request):
    profile = request.user.employer_profile
    error = None

    if request.method == "POST":
        profile.company_name = request.POST.get("company_name")
        profile.location = request.POST.get("location")
        profile.company_email = request.POST.get("company_email")
        profile.phone_number = request.POST.get("phone_number") 
        profile.company_website = request.POST.get("company_website")

        try:
            profile.save()
            return redirect("employer_dashboard")
        except IntegrityError:
            error = "Company email or website already exists."

    return render(request, "complete_employer_profile.html", {"error": error})



@login_required
@user_passes_test(is_employer)
def post_job(request):
    employer_profile = request.user.employer_profile

    if not employer_profile.is_complete:
        return redirect("complete_employer_profile")

    if request.method == "POST":
        Job.objects.create(
            title=request.POST.get("title"),
            employer=employer_profile,   # ✅ FIX IS HERE
            location=employer_profile.location, # ✅ FIX IS HERE
            salary=request.POST.get("salary"),
            description=request.POST.get("description"),
            job_type=request.POST.get("job_type"),
            work_mode=request.POST.get("work_mode"),
            skills_required=request.POST.get("skills_required"),
            posted_by=request.user
        )
        return redirect("employer_dashboard")

    return render(request, "post_job.html")
# ================= VIEW APPLICANTS =================
@login_required
@user_passes_test(is_employer)
def view_applicants(request, job_id):
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    applications = JobApplication.objects.filter(job=job)

    return render(request, "view_applicants.html", {
        "job": job,
        "applications": applications
    })

# ================= DELETE JOB =================
@login_required
@user_passes_test(is_employer)
def delete_job(request, job_id):
    job = get_object_or_404(
        Job,
        id=job_id,
        employer=request.user.employer_profile
    )

    if request.method == "POST":
        job.delete()
        messages.success(request, "Job deleted successfully.")
        return redirect("employer_dashboard")

    return redirect("employer_dashboard")

# ================= APPROVE APPLICATION =================
@login_required
@user_passes_test(is_employer)
def approve_application(request, application_id):
    application = get_object_or_404(
        JobApplication,
        id=application_id,
        job__posted_by=request.user
    )

    # ✅ FIX: define job once
    job = application.job

    application.status = "approved"
    application.save()

    email = application.user.student_profile.student_email
    if email:
        send_mail(
            "🎉 Placement Selection Notification",
            f"Dear {application.user.username},\n\n"
            f"🎉 Congratulations! 🎉\n\n"
            f"We are delighted to inform you that you have been "
            f"SUCCESSFULLY SELECTED for the position of\n\n"
            f"👉 {job.title} at {job.employer.company_name}.\n\n"
            f"Our HR team will contact you shortly with further instructions "
            f"regarding the next steps in the recruitment process.\n\n"
            f"Please keep an eye on your email for further updates.\n\n"
            f"Best Wishes,\n"
            f"Placement Cell\n"
            f"{job.employer.company_name}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )

    return redirect("view_applicants", job_id=job.id)


# ================= REJECT APPLICATION =================
@login_required
@user_passes_test(is_employer)
def reject_application(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)

    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()

        # ✅ Fallback if empty
        if not reason:
            reason = "Not specified by employer"

        application.status = "rejected"
        application.rejection_reason = reason
        application.save()

        student = application.user
        job = application.job

        to_email = (
            student.student_profile.student_email
            if hasattr(student, "student_profile") and student.student_profile.student_email
            else student.email
        )

        if to_email:
            send_mail(
                subject="Job Application Rejected – NextGen Place",
                message=f"""
Dear {student.username},

We regret to inform you that your application for the position
"{job.title}" has been rejected.

Reason:
{reason}

Thank you for your interest.
You may apply for other opportunities on NextGen Place.

Regards,
{job.employer.company_name}
NextGen Place Team
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )

        messages.success(request, "Application rejected and email sent.")

    return redirect("view_applicants", job.id)



# ================= ADMIN DASHBOARD (ANALYTICS) =================

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):

    # ================= BASIC COUNTS =================
    total_users = User.objects.count()
    total_jobs = Job.objects.count()
    total_applications = JobApplication.objects.count()

    # ================= DEPARTMENT-WISE PLACEMENT SUCCESS =================
    department_stats = (
        StudentProfile.objects
        .values("department")
        .annotate(
            student_count=Count("id"),
            approved_count=Count(
                "user__job_applications",
                filter=Q(user__job_applications__status="approved")
            ),
            rejected_count=Count(
                "user__job_applications",
                filter=Q(user__job_applications__status="rejected")
            ),
        )
    )

    for dept in department_stats:
        total = dept["student_count"]
        approved = dept["approved_count"]
        dept["success_percentage"] = round((approved / total) * 100, 1) if total > 0 else 0

    # ================= APPLICATION STATISTICS =================
    approved_count = JobApplication.objects.filter(status="approved").count()
    rejected_count = JobApplication.objects.filter(status="rejected").count()
    pending_count = JobApplication.objects.filter(status="pending").count()

    # ============================================================
    # ✅ TOP 3 COMPANIES BY JOB POSTS
    # ============================================================
    top_companies = (
        Job.objects
        .values("employer__company_name")
        .annotate(job_count=Count("id"))
        .order_by("-job_count")[:3]
    )

    # ============================================================
    # ✅ TOP 2 IN-DEMAND SKILLS
    # ============================================================
    skill_counter = {}

    for job in Job.objects.all():
        skills = job.skills_required.split(",")
        for skill in skills:
            skill = skill.strip().lower()
            if skill:
                skill_counter[skill] = skill_counter.get(skill, 0) + 1

    top_skills = sorted(
        skill_counter.items(),
        key=lambda x: x[1],
        reverse=True
    )[:2]

    # ============================================================
    # ✅ ALL REGISTERED STUDENTS
    # ============================================================
    students = (
        StudentProfile.objects
        .select_related("user")
        .order_by("user__date_joined")
    )

    # ============================================================
    # ✅ ALL REGISTERED EMPLOYERS
    # ============================================================
    employers = (
        EmployerProfile.objects
        .select_related("user")
        .order_by("-created_at")
    )

    # ================= RENDER =================
    return render(request, "admin_dashboard.html", {

        # COUNTS
        "total_users": total_users,
        "total_jobs": total_jobs,
        "total_applications": total_applications,

        # APPLICATION STATUS
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "pending_count": pending_count,

        # DEPARTMENT ANALYTICS
        "department_stats": department_stats,

        # ANALYTICS
        "top_companies": top_companies,
        "top_skills": top_skills,

        # TABLE DATA
        "students": students,
        "employers": employers,
    })


# ================= DELETE STUDENT =================
@login_required
@user_passes_test(is_admin)
def confirm_delete_student(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)

    if student.user == request.user:
        return HttpResponseForbidden("You cannot delete your own account.")

    if request.method == "POST":
        student.user.delete()
        return redirect("admin_dashboard")

    return render(request, "confirm_delete_student.html", {"student": student})


#---------------------------
#DELETE STUDENTS
#----------------------
@login_required
@user_passes_test(is_admin)
def delete_student(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.delete()   # 🔥 Deletes EVERYTHING related
        return redirect("admin_dashboard")

    return render(request, "confirm_delete_student.html", {
        "student_user": user
    })

#---------------------
#Delete_employer
#____________________
@user_passes_test(lambda u: u.is_superuser)
def delete_employer(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.delete()  # 🔥 deletes employer profile + jobs via cascade

    return redirect("admin_dashboard")