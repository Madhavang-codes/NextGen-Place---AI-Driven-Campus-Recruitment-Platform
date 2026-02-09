import re

def parse_job_fields(job):
    description = job.description or ""

    job_type_match = re.search(
        r"Job Type:\s*(.*)",
        description,
        re.IGNORECASE
    )
    work_mode_match = re.search(
        r"Work Mode:\s*(.*)",
        description,
        re.IGNORECASE
    )

    job.job_type = (
        job_type_match.group(1).strip()
        if job_type_match else "Not specified"
    )
    job.work_mode = (
        work_mode_match.group(1).strip()
        if work_mode_match else "Not specified"
    )

    job.clean_description = re.sub(
        r"(Job Type:.*|Work Mode:.*)",
        "",
        description,
        flags=re.IGNORECASE
    ).strip()

    return job