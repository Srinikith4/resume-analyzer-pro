from __future__ import annotations

import os
import uuid
from typing import Any

from flask import Flask, render_template, request, redirect, url_for, session, jsonify

# Groq official SDK
# pip install groq
from groq import Groq

from roles import ROLES, get_role_config, flatten_all_tracks, build_roadmap_for_role
from resume_parser import extract_text_from_pdf
from skill_extractor import extract_skills


# -------------------------
# App config
# -------------------------
ALLOWED_EXTENSIONS = {"pdf"}

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB

# Groq
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
# Good alternatives (if you want later):
# - "llama-3.1-8b-instant" (faster/cheaper)
# - "mixtral-8x7b-32768" (older but sometimes available)
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# -------------------------
# Helpers
# -------------------------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def normalize_skill(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def unique_norm_list(items):
    seen = set()
    out = []
    for x in items or []:
        nx = normalize_skill(x)
        if nx and nx not in seen:
            seen.add(nx)
            out.append(nx)
    return out


def match_score(detected: list[str], blueprint: list[str]) -> tuple[int, list[str], list[str]]:
    dset = set(unique_norm_list(detected))
    b = unique_norm_list(blueprint)

    matched = [x for x in b if x in dset]
    missing = [x for x in b if x not in dset]

    score = int(round((len(matched) / len(b)) * 100)) if b else 0
    return score, matched, missing


def get_analysis() -> dict[str, Any] | None:
    data = session.get("analysis")
    if not isinstance(data, dict):
        return None
    return data


def save_analysis(data: dict[str, Any]) -> None:
    session["analysis_id"] = str(uuid.uuid4())
    session["analysis"] = data


# -------------------------
# Routes
# -------------------------
@app.route("/", methods=["GET"])
def home():
    # Your home.html uses roles + roles_data for dropdown chaining
    role_keys = list(ROLES.keys())
    return render_template("home.html", roles=role_keys, roles_data=ROLES)


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    role = request.values.get("role", "").strip()
    category = request.values.get("category", "").strip()
    track = request.values.get("track", "").strip()

    cfg = get_role_config(role, category, track)
    if not cfg:
        return redirect(url_for("home"))

    title = cfg["title"]
    path = cfg["path"]
    blueprint = unique_norm_list(cfg["skills"])

    detected_skills: list[str] = []
    score = None
    matched: list[str] = []
    missing: list[str] = []
    resume_text_preview = ""

    if request.method == "POST":
        file = request.files.get("resume")

        if not file or file.filename == "":
            return render_template(
                "analyze.html",
                title=title,
                path=path,
                role=role,
                category=category,
                track=track,
                blueprint=blueprint,
                score=score,
                matched=matched,
                missing=missing,
                detected=detected_skills,
                preview=resume_text_preview,
                error="Please upload a PDF resume.",
            )

        if not allowed_file(file.filename):
            return render_template(
                "analyze.html",
                title=title,
                path=path,
                role=role,
                category=category,
                track=track,
                blueprint=blueprint,
                score=score,
                matched=matched,
                missing=missing,
                detected=detected_skills,
                preview=resume_text_preview,
                error="Only PDF files are allowed.",
            )

        # Parse resume + extract skills
        text = extract_text_from_pdf(file) or ""
        resume_text_preview = text[:600]
        detected_skills = unique_norm_list(extract_skills(text))

        # Compare to blueprint
        score, matched, missing = match_score(detected_skills, blueprint)

        # Save into session (so /suitable, /roadmap, /ask works)
        save_analysis({
            "role": role,
            "category": category,
            "track": track,
            "title": title,
            "path": path,
            "score": score,
            "blueprint": blueprint,
            "detected": detected_skills,
            "matched": unique_norm_list(matched),
            "missing": unique_norm_list(missing),
            # keep small preview only (don’t store full resume in session)
            "preview": resume_text_preview,
        })

    return render_template(
        "analyze.html",
        title=title,
        path=path,
        role=role,
        category=category,
        track=track,
        blueprint=blueprint,
        score=score,
        matched=unique_norm_list(matched),
        missing=unique_norm_list(missing),
        detected=unique_norm_list(detected_skills),
        preview=resume_text_preview,
        error=None,
    )


@app.route("/suitable", methods=["GET"])
def suitable():
    data = get_analysis()
    if not data or not data.get("detected"):
        return redirect(url_for("home"))

    detected = data["detected"]

    # score resume against ALL role tracks
    all_tracks = flatten_all_tracks()
    results = []
    for item in all_tracks:
        sc, _, _ = match_score(detected, item["skills"])
        results.append({
            "title": item["title"],
            "path": item["path"],
            "role": item["role"],
            "category": item["category"],
            "track": item["track"],
            "score": sc,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    top = results[:10]
    return render_template("suitable.html", top=top, current=data)


@app.route("/roadmap", methods=["GET"])
def roadmap():
    data = get_analysis()
    if not data:
        return redirect(url_for("home"))

    detected = set(data.get("detected", []))
    steps = build_roadmap_for_role(
        data["role"], data["category"], data["track"], detected
    )
    return render_template("roadmap.html", steps=steps, current=data)


@app.route("/ask", methods=["POST"])
def ask():
    """
    Groq AI assistant:
    - role-aware
    - blueprint + matched/missing aware
    - answers ANY question about the role: learning plan, interview, projects, resume, etc.
    """
    data = get_analysis()
    if not data:
        return jsonify({"ok": False, "answer": "Upload and analyze a resume first."}), 400

    payload = request.get_json(silent=True) or {}
    q = (payload.get("q") or "").strip()
    if not q:
        return jsonify({"ok": False, "answer": "Type a question first."}), 400

    # If Groq key not set, fall back to a helpful non-AI answer
    if not GROQ_API_KEY or not groq_client:
        missing = data.get("missing", [])
        matched = data.get("matched", [])
        title = data.get("title", "Selected Role")

        fallback = [
            f"(AI is OFF because GROQ_API_KEY is not set.)",
            f"Role: {title}",
        ]
        if "resume" in q.lower():
            fallback.append("Quick resume upgrades:")
            if missing:
                fallback.append(
                    f"- Add missing keywords in Skills: {', '.join(missing[:10])}")
            fallback.append(
                "- Add 1–2 role-relevant projects with measurable impact.")
            fallback.append("- Add ATS keywords inside experience bullets.")
        else:
            if missing:
                fallback.append(
                    f"Missing skills to learn next: {', '.join(missing[:12])}")
            if matched:
                fallback.append(
                    f"Your strong skills: {', '.join(matched[:12])}")
            fallback.append("Tip: Set GROQ_API_KEY to enable full AI chat.")
        return jsonify({"ok": True, "answer": "\n".join(fallback)})

    title = data.get("title", "Selected Role")
    path = data.get("path", "")
    score = data.get("score", 0)
    blueprint = data.get("blueprint", [])
    detected = data.get("detected", [])
    matched = data.get("matched", [])
    missing = data.get("missing", [])
    preview = data.get("preview", "")

    system_prompt = f"""
You are an expert IT career mentor + hiring manager.
Answer the user's question about the selected role in a practical, accurate, structured way.

Selected role: {title}
Path: {path}
Resume match score: {score}%

Role blueprint skills (target): {", ".join(blueprint)}
Detected in resume: {", ".join(detected)}
Matched: {", ".join(matched)}
Missing: {", ".join(missing)}

Resume preview (partial):
{preview}

Rules:
- Be crisp, no fluff. Use short headings + bullets.
- If user asks what to learn next: prioritize missing skills, give a step-by-step plan.
- If user asks interview prep: give role-specific Qs + strong answers + common mistakes.
- If user asks projects: suggest 2–3 projects tailored to the role (stack, features, metrics, resume bullets).
- If user asks resume improvements: give ATS-friendly bullet rewrites + missing keywords.
"""

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": q},
            ],
            temperature=0.35,
            max_tokens=650,
        )
        answer = (completion.choices[0].message.content or "").strip()
        if not answer:
            answer = "I couldn't generate an answer. Try asking in a different way."
        return jsonify({"ok": True, "answer": answer})

    except Exception as e:
        # show a clean message to UI
        return jsonify({
            "ok": False,
            "answer": f"AI error: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
