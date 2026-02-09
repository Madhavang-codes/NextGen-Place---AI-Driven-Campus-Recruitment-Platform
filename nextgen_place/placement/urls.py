from django.urls import path
from django.shortcuts import redirect
from . import views


def admin_login_redirect(request):
    return redirect("/admin/login/?next=/admin-dashboard/")


urlpatterns = [

    # ================= BASIC =================
    path("", views.home, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ================= STUDENT =================
    path(
        "student-verification/",
        views.student_verification,
        name="student_verification"
    ),
    path(
        "student-dashboard/",
        views.student_dashboard,
        name="student_dashboard"
    ),
    path(
        "upload-resume/",
        views.upload_resume,
        name="upload_resume"
    ),
    path(
        "apply-job/<int:job_id>/",
        views.apply_job,
        name="apply_job"
    ),

    # ================= JOBS =================
    path(
        "jobs/",
        views.job_list,
        name="jobs"
    ),
    path(
        "jobs/post/",
        views.post_job,
        name="post_job"
    ),

    # ================= EMPLOYER =================
    path(
        "employer-dashboard/",
        views.employer_dashboard,
        name="employer_dashboard"
    ),
    path(
        "complete-employer-profile/",
        views.complete_employer_profile,
        name="complete_employer_profile"
    ),

    # ================= VIEW APPLICANTS =================
    path(
        "view-applicants/<int:job_id>/",
        views.view_applicants,
        name="view_applicants"
    ),

    path("delete-job/<int:job_id>/", views.delete_job, name="delete_job"),
    # ================= APPROVE / REJECT =================
    path(
        "application/<int:application_id>/approve/",
        views.approve_application,
        name="approve_application"
    ),
    path(
        "application/<int:application_id>/reject/",
        views.reject_application,
        name="reject_application"
    ),

    # ================= ADMIN =================

    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard"
    ),

    path(
        "dashboard/delete-student/<int:student_id>/",
        views.confirm_delete_student,
        name="confirm_delete_student"
    ),

    path(
        "admin/delete-employer/<int:user_id>/",
        views.delete_employer,
        name="delete_employer"
    ),


    # ================= STEP-2 (NEW) =================
    path(
        "admin-login/",
        admin_login_redirect,
        name="admin_login_redirect"
    ),
]