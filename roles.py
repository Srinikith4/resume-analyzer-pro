from __future__ import annotations


def _cfg(title: str, path: str, skills: list[str]):
    return {"title": title, "path": path, "skills": skills}


ROLES = {
    "Developer": {
        "Web Developer": {
            "Java": _cfg(
                "Java Web Developer",
                "Developer → Web Developer → Java",
                ["java", "spring", "spring boot", "rest api", "jpa", "hibernate", "maven",
                 "git", "sql", "mysql", "html", "css", "javascript", "docker", "aws"]
            ),
            "Python": _cfg(
                "Python Web Developer",
                "Developer → Web Developer → Python",
                ["python", "flask", "django", "rest api", "sql", "postgresql",
                 "git", "html", "css", "javascript", "docker", "aws"]
            ),
            "MERN": _cfg(
                "MERN Stack Developer",
                "Developer → Web Developer → MERN",
                ["javascript", "typescript", "react", "node", "express",
                 "mongodb", "rest api", "git", "html", "css", "docker", "aws"]
            ),
        },
        "Mobile Developer": {
            "Android": _cfg(
                "Android Developer",
                "Developer → Mobile Developer → Android",
                ["kotlin", "android", "jetpack", "mvvm", "rest api",
                 "git", "firebase", "sqlite", "testing"]
            ),
            "Flutter": _cfg(
                "Flutter Developer",
                "Developer → Mobile Developer → Flutter",
                ["dart", "flutter", "state management",
                 "rest api", "git", "firebase", "ui", "testing"]
            ),
        },
        "Backend Developer": {
            "Java": _cfg(
                "Java Backend Developer",
                "Developer → Backend Developer → Java",
                ["java", "spring boot", "microservices", "rest api", "sql", "postgresql",
                 "redis", "kafka", "docker", "kubernetes", "aws", "git", "testing"]
            ),
            "Python": _cfg(
                "Python Backend Developer",
                "Developer → Backend Developer → Python",
                ["python", "fastapi", "django", "rest api", "sql", "postgresql",
                 "redis", "celery", "docker", "aws", "git", "testing"]
            ),
        },
    },

    "Data": {
        "Data Analyst": {
            "General": _cfg(
                "Data Analyst",
                "Data → Data Analyst → General",
                ["excel", "sql", "python", "pandas", "numpy", "power bi",
                 "tableau", "statistics", "data analysis", "data visualization"]
            ),
        },
        "Data Scientist": {
            "ML": _cfg(
                "Data Scientist",
                "Data → Data Scientist → ML",
                ["python", "pandas", "numpy", "statistics", "machine learning", "scikit-learn",
                 "feature engineering", "model evaluation", "sql", "data visualization"]
            ),
        },
        "Data Engineer": {
            "Cloud": _cfg(
                "Data Engineer",
                "Data → Data Engineer → Cloud",
                ["python", "sql", "etl", "airflow", "spark", "data warehousing",
                 "aws", "s3", "redshift", "glue", "kafka", "docker"]
            ),
        },
    },

    "AI/ML": {
        "ML Engineer": {
            "General": _cfg(
                "ML Engineer",
                "AI/ML → ML Engineer → General",
                ["python", "machine learning", "scikit-learn", "pandas", "numpy",
                 "model deployment", "fastapi", "docker", "aws", "mlops", "git"]
            )
        },
        "NLP Engineer": {
            "Transformers": _cfg(
                "NLP Engineer",
                "AI/ML → NLP Engineer → Transformers",
                ["python", "nlp", "transformers", "pytorch", "huggingface",
                 "tokenization", "model fine-tuning", "evaluation", "docker", "api"]
            )
        },
    },

    "Cloud/DevOps": {
        "DevOps Engineer": {
            "AWS": _cfg(
                "DevOps Engineer",
                "Cloud/DevOps → DevOps Engineer → AWS",
                ["linux", "git", "docker", "kubernetes", "ci/cd",
                 "github actions", "terraform", "aws", "monitoring", "logging"]
            )
        },
        "Cloud Engineer": {
            "AWS": _cfg(
                "Cloud Engineer",
                "Cloud/DevOps → Cloud Engineer → AWS",
                ["aws", "iam", "ec2", "s3", "vpc", "lambda",
                 "cloudwatch", "terraform", "linux", "networking"]
            )
        },
    },

    "Security": {
        "Cybersecurity Analyst": {
            "SOC": _cfg(
                "Cybersecurity Analyst",
                "Security → Cybersecurity Analyst → SOC",
                ["networking", "linux", "siem", "incident response", "logs",
                 "threat analysis", "vulnerability", "security basics"]
            )
        }
    },

    "QA": {
        "QA Engineer": {
            "Automation": _cfg(
                "QA Automation Engineer",
                "QA → QA Engineer → Automation",
                ["testing", "test cases", "selenium", "api testing",
                 "postman", "python", "java", "git", "ci/cd"]
            )
        }
    },

    "Product": {
        "Business Analyst": {
            "IT": _cfg(
                "Business Analyst (IT)",
                "Product → Business Analyst → IT",
                ["requirements", "user stories", "sql", "excel",
                 "communication", "agile", "jira", "process"]
            )
        }
    },
}


def get_role_config(role: str, category: str, track: str):
    try:
        cfg = ROLES[role][category][track]
        return {"role": role, "category": category, "track": track, **cfg}
    except Exception:
        return None


def flatten_all_tracks():
    out = []
    for role, cats in ROLES.items():
        for cat, tracks in cats.items():
            for track, cfg in tracks.items():
                out.append({
                    "role": role,
                    "category": cat,
                    "track": track,
                    "title": cfg["title"],
                    "path": cfg["path"],
                    "skills": cfg["skills"],
                })
    return out


def build_roadmap_for_role(role: str, category: str, track: str, detected_set: set[str]):
    cfg = get_role_config(role, category, track)
    if not cfg:
        return []

    # Difficulty buckets (tune later)
    easy = {"html", "css", "sql", "excel", "git",
            "python", "java", "javascript", "statistics", "networking", "linux"}
    medium = {"pandas", "numpy", "rest api", "spring", "spring boot",
              "flask", "django", "react", "node", "docker", "power bi", "tableau",
              "fastapi", "express", "mongodb", "postgresql", "mysql"}
    hard = {"kubernetes", "microservices", "kafka", "spark", "airflow",
            "mlops", "terraform", "transformers", "pytorch", "data warehousing",
            "feature engineering", "model deployment", "model evaluation", "ci/cd"}

    # Realistic weeks (instead of silly "days")
    # Easy: 1–2 weeks, Medium: 2–4 weeks, Hard: 4–8 weeks
    steps = []
    for s in cfg["skills"]:
        sl = s.strip().lower()

        if sl in easy:
            level = 1
            weeks = 2
        elif sl in medium:
            level = 2
            weeks = 4
        elif sl in hard:
            level = 3
            weeks = 8
        else:
            level = 2
            weeks = 4

        steps.append({
            "skill": sl,
            "level": level,
            "level_label": "Easy" if level == 1 else ("Intermediate" if level == 2 else "Advanced"),
            "weeks": weeks,
            "has": sl in detected_set
        })

    # Skills you already have first, then by difficulty, then by weeks
    steps.sort(key=lambda x: (not x["has"], x["level"], x["weeks"]))
    return steps
