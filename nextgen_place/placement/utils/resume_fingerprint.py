import hashlib

def generate_resume_hash(file_path):
    hasher = hashlib.sha256()

    with open(file_path, "rb") as f:
        hasher.update(f.read())

    return hasher.hexdigest()