import re

# Add synonyms so matching is more reliable
ALIASES = {
    "springboot": "spring boot",
    "restapis": "rest api",
    "restful": "rest api",
    "nodejs": "node",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "dotnet": ".net",
    "aspnet": "asp.net",
    "machinelearning": "machine learning",
    "deeplearning": "deep learning",
    "powerbi": "power bi",
}

# A general skill bank (the app detects these)
SKILL_BANK = sorted(set([
    # languages
    "java", "python", "javascript", "typescript", "c#", "go", "php", "kotlin", "dart",
    # web/backend
    "spring", "spring boot", "hibernate", "jpa", ".net", "asp.net", "entity framework",
    "node", "express", "django", "flask", "laravel", "rest api", "microservices",
    # data
    "sql", "mysql", "postgresql", "mongodb", "redis", "etl", "spark", "airflow", "kafka",
    "pandas", "numpy", "scikit-learn", "statistics", "data analysis", "data visualization", "feature engineering",
    # ai
    "machine learning", "deep learning", "pytorch", "tensorflow", "nlp", "transformers", "spacy",
    "model deployment", "data preprocessing", "tokenization",
    # cloud/devops
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "linux", "ci/cd", "jenkins",
    "monitoring", "logging", "iam", "ec2", "s3", "vpc", "cloudwatch",
    # frontend
    "html", "css", "react", "redux", "angular", "rxjs", "ui design", "responsive design",
    # testing/security
    "selenium", "playwright", "api testing", "automation testing", "junit", "testng", "jira",
    "network security", "wireshark", "owasp", "incident response", "vulnerability assessment",
    # tools
    "git", "maven", "gradle", "firebase", "android", "android sdk", "tableau", "power bi", "excel"
]))


def normalize_text(text: str) -> str:
    t = text.lower()
    # remove punctuation but keep . and # for .net and c#
    t = re.sub(r"[^a-z0-9\.\#\s]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    # apply alias replacements on compact tokens too
    compact = t.replace(" ", "")
    for k, v in ALIASES.items():
        if k in compact:
            t += " " + v
    return t


def extract_skills(text: str):
    t = normalize_text(text)

    found = []
    for skill in SKILL_BANK:
        # word-boundary-ish match
        pattern = r"(^|\s)" + re.escape(skill) + r"(\s|$)"
        if re.search(pattern, t):
            found.append(skill)

    return sorted(set(found))
