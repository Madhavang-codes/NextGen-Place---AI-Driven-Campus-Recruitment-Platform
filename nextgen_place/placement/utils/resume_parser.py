import re
from PyPDF2 import PdfReader
from docx import Document


# =========================================================
# MASTER SKILL DATABASE (EXPANDABLE)
# =========================================================

COMMON_SKILLS = {
    # Programming Languages
    "python", "java", "c", "go", "ruby", "php", "swift", "kotlin",

    # Web Technologies
    "html", "css", "javascript", "typescript",
    "react", "angular", "vue", "nextjs", "nodejs", "express",

    # Backend Frameworks
    "django", "flask", "fastapi", "spring", "laravel",

    # Databases
    "sql", "mysql", "postgresql", "mongodb", "sqlite", "oracle",
    "redis", "firebase",

    # Data Science & AI
    "numpy", "pandas", "scipy", "matplotlib", "seaborn",
    "scikit-learn", "tensorflow", "keras", "pytorch",
    "nlp", "machine learning", "deep learning",

    # DevOps & Cloud
    "docker", "kubernetes", "aws", "azure", "gcp",
    "jenkins", "ci/cd",

    # Version Control & Tools
    "git", "github", "gitlab", "bitbucket",
    "linux", "bash", "powershell",

    # Testing
    "unit testing", "pytest", "junit", "selenium",

    # Mobile Development
    "android", "ios", "flutter", "react native",

    # Other Skills
    "api", "rest", "graphql", "microservices",
    "data structures", "algorithms", "oop","MS Excel","Powerpoint"
}


# =====================================================
# SKILL ALIASES (REAL RESUME VARIATIONS)
# =====================================================
SKILL_ALIASES = {
    # Data Science
    "numpy": ["numpy", "np"],
    "pandas": ["pandas"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "c++": ["c++","cpp","c plus plus"],
    
    # Machine Learning
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl"],
    "artificial intelligence": ["artificial intelligence", "ai"],

    # Programming Concepts
    "data structures": ["data structures", "ds"],
    "algorithms": ["algorithms", "algo"],
    "oop": ["oop", "object oriented programming"],
    "C# / .NET": [
        "c#",
        "c#.net",
        "C#.Net",
        "C#.NET"
        "c# .net",
        "c#. net",
        ".net",
        "dotnet",
        "asp.net"
    ],
    # ==============================
# OFFICE & PRODUCTIVITY SKILLS
# ==============================

    "ms excel": [
            "ms excel",
            "excel",
            "microsoft excel",
            "excel spreadsheet",
            "excel sheets",
            "advanced excel",
            "basic excel",
            "excel formulas",
            "excel functions"
    ],




    # Office Tools
    "excel": ["excel", "ms excel", "microsoft excel"],
    "powerpoint": ["powerpoint", "ppt", "ms powerpoint"],
     "Basic Computer Skills": [
        "basic computer skills",
        "basic computer knowledge",
        "computer basics",
        "computer fundamentals"],

    # Web / API
    "api": ["api", "rest api", "apis"],
    "rest": ["rest", "restful"],
}


# =====================================================
# EXTRACT RAW TEXT FROM RESUME
# =====================================================
def extract_text(file_path):
    text = ""

    try:
        # PDF Resume
        if file_path.lower().endswith(".pdf"):
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() or ""

        # DOCX Resume
        elif file_path.lower().endswith(".docx"):
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + " "

    except Exception as e:
        print("Resume parsing error:", e)

    return text.lower()


# =====================================================
# EXTRACT SKILLS FROM RESUME (FINAL LOGIC)
# =====================================================
def extract_skills(resume_path):
    text = extract_text(resume_path).lower()

    detected_skills = set()

    # --------------------------------------------------
    # 1️⃣ Match COMMON_SKILLS (safe single-word skills)
    # --------------------------------------------------
    for skill in COMMON_SKILLS:
        skill = skill.lower()
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text):
            detected_skills.add(skill)

    # --------------------------------------------------
    # 2️⃣ Match SKILL_ALIASES (symbols + multi-word skills)
    # --------------------------------------------------
    for canonical_skill, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            alias = alias.lower()
            if alias in text:          # 🔥 IMPORTANT FIX
                detected_skills.add(canonical_skill)
                break

    return sorted(detected_skills)