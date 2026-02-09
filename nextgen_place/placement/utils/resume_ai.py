from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .resume_text import extract_resume_text
from placement.models import StudentProfile


def check_resume_originality(current_profile):
    current_text = extract_resume_text(current_profile.resume.path)

    other_profiles = StudentProfile.objects.exclude(id=current_profile.id).exclude(resume__isnull=True)

    texts = [current_text]
    profiles = []

    for profile in other_profiles:
        texts.append(extract_resume_text(profile.resume.path))
        profiles.append(profile)

    if len(texts) == 1:
        return 0.0, False  # no comparison

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform(texts)

    similarities = cosine_similarity(vectors[0:1], vectors[1:])[0]
    max_similarity = max(similarities) * 100

    is_fake = max_similarity > 70  # 🔴 THRESHOLD

    return round(max_similarity, 2), is_fake