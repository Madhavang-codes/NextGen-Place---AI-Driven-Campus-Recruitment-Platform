from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


# =====================================================
# STUDENT PROFILE
# =====================================================
class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )

    # 🔐 Student verification fields
    register_number = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True
    )

    full_name = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    department = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    academic_year = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    # ✅ PRIMARY EMAIL (USED FOR ALL NOTIFICATIONS)
    student_email = models.EmailField(
        null=True,
        blank=True,
        help_text="Email used for placement notifications"
    )

    # ❌ OPTIONAL COLLEGE EMAIL
    college_email = models.EmailField(
        unique=True,
        null=True,
        blank=True
    )

    # ✅ Verification flag
    is_verified = models.BooleanField(default=False)

    # ================= RESUME =================
    resume = models.FileField(
        upload_to="resumes/",
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx'])],
        null=True,
        blank=True
    )

    # ================= RESUME DUPLICATE CHECK =================
    resume_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="SHA256 hash of resume for duplicate detection"
    )

    # ================= AI FRAUD ANALYSIS =================
    resume_similarity_score = models.FloatField(
        default=0.0,
        help_text="Similarity percentage with other resumes"
    )

    is_resume_fake = models.BooleanField(
        default=False,
        help_text="True if resume is detected as copied or fake"
    )

    resume_warning = models.CharField(
        max_length=255,
        blank=True,
        help_text="Warning message shown to student"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # ✔ Profile completeness
    def is_profile_complete(self):
        return all([
            self.register_number,
            self.full_name,
            self.department,
            self.academic_year,
            self.student_email
        ])

    def __str__(self):
        return self.full_name or self.user.username


# =====================================================
# EMPLOYER PROFILE
# =====================================================
class EmployerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="employer_profile"
    )

    company_name = models.CharField(max_length=80, null=True, blank=True)
    location = models.CharField(max_length=40, blank=True, null=True)
    company_email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15)
    company_website = models.URLField(unique=True, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_complete(self):
        return all([
            self.company_name,
            self.company_email,
            self.company_website
        ])

    def __str__(self):
        return self.company_name or self.user.username


# =====================================================
# JOB MODEL
# =====================================================
class Job(models.Model):
    title = models.CharField(max_length=200)
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE)
    location = models.CharField(max_length=100)
    salary = models.CharField(max_length=50)
    description = models.TextField()
    job_type = models.CharField(max_length=50, null=True, blank=True)
    work_mode = models.CharField(max_length=50, null=True, blank=True)
    skills_required = models.TextField(
        help_text="Comma-separated skills (e.g. Python, Django, SQL)"
    )

    posted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posted_jobs"
    )

    # ✅ USED FOR ADMIN ANALYTICS
    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ SAFE (USED FOR DISPLAY)
    posted_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        if self.employer and self.employer.company_name:
            return f"{self.title} - {self.employer.company_name}"
        return self.title


# =====================================================
# JOB APPLICATION
# =====================================================
class JobApplication(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="job_applications"
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="job_applications"
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # ✅ REJECTION REASON
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason provided by employer when rejecting application"
    )

    applied_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-applied_date"]

    def __str__(self):
      if self.job and self.job.employer:
        return f"{self.job.title} - {self.job.employer.company_name}"
      return f"Application #{self.id}"