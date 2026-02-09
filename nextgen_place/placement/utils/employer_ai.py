from difflib import SequenceMatcher
from placement.models import EmployerProfile


def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def detect_duplicate_company(profile):
    duplicates = []

    for existing in EmployerProfile.objects.exclude(id=profile.id):

        # Exact match checks
        if profile.company_email == existing.company_email:
            duplicates.append(existing.company_name)

        if profile.company_website == existing.company_website:
            duplicates.append(existing.company_name)

        # Name similarity check (warning only)
        if similarity(profile.company_name, existing.company_name) > 0.85:
            duplicates.append(existing.company_name)

    return list(set(duplicates))