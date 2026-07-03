import os
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from pymongo import MongoClient
from resume_parser import extract_text_from_pdf
from ai_utils import (
    analyze_resume, 
    match_job_description, 
    generate_interview_questions, 
    evaluate_interview_answer
)
from flask import send_from_directory

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://pushpakpogiri111:9000Naidu%40@cluster0.irbir3w.mongodb.net/")
MONGODB_DB = os.getenv("MONGODB_DB", "resume")

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    db = client[MONGODB_DB]
    db.command("ping")
    users_collection = db["users"]
    api_events_collection = db["api_events"]
    users_collection.create_index("email", unique=True)
    DB_STATUS = "connected"
except Exception as exc:
    client = None
    db = None
    users_collection = None
    api_events_collection = None
    DB_STATUS = f"unavailable: {exc}"

# Temporary in-memory storage for the current session (For demo purposes)
session_data = {
    "resume_text": "",
    "analysis": None
}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def store_api_event(event_type: str, payload: dict):
    if not api_events_collection:
        return None
    try:
        result = api_events_collection.insert_one({
            "event_type": event_type,
            "payload": payload,
            "created_at": datetime.utcnow()
        })
        return str(result.inserted_id)
    except Exception:
        return None


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != '' and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '')
    password = data.get('password', '')
    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required"}), 400

    if users_collection is None:
        return jsonify({"success": False, "error": "Database is unavailable"}), 503

    user_doc = users_collection.find_one({"email": email})
    if not user_doc or user_doc.get("password") != hash_password(password):
        return jsonify({"success": False, "error": "Invalid email or password"}), 401

    return jsonify({
        "success": True,
        "token": f"token-{hashlib.sha256(email.encode('utf-8')).hexdigest()[:12]}",
        "user": {
            "fullName": user_doc.get("fullName", email.split('@')[0]),
            "email": email
        }
    }), 200

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    full_name = data.get('fullName', '')
    email = data.get('email', '')
    password = data.get('password', '')
    if not full_name or not email or not password:
        return jsonify({"success": False, "error": "Full name, email, and password are required"}), 400

    if users_collection is None:
        return jsonify({"success": False, "error": "Database is unavailable"}), 503

    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        return jsonify({"success": False, "error": "User already exists"}), 400

    users_collection.insert_one({
        "fullName": full_name,
        "email": email,
        "password": hash_password(password),
        "created_at": datetime.utcnow()
    })

    return jsonify({
        "success": True,
        "token": f"token-{hashlib.sha256(email.encode('utf-8')).hexdigest()[:12]}",
        "user": {
            "fullName": full_name,
            "email": email
        }
    }), 200

@app.route('/api/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Parse PDF
        resume_text = extract_text_from_pdf(filepath)
        session_data["resume_text"] = resume_text
        
        # Clean up file after reading
        try:
            os.remove(filepath)
        except:
            pass
            
        if not resume_text:
            fallback_text = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
            session_data["resume_text"] = fallback_text
            analysis = analyze_resume(fallback_text)
            session_data["analysis"] = analysis
            return jsonify({
                "message": "Upload successful, but text extraction failed. Showing fallback analysis.",
                "resume_text_preview": fallback_text[:200] + "...",
                "analysis": analysis
            }), 200
            
        # Analyze resume
        analysis = analyze_resume(resume_text)
        session_data["analysis"] = analysis
        store_api_event("resume_upload", {
            "filename": filename,
            "resume_text_preview": resume_text[:200],
            "analysis": analysis
        })
        
        return jsonify({
            "message": "Upload and analysis successful",
            "resume_text_preview": resume_text[:200] + "...",
            "analysis": analysis
        }), 200
        
    return jsonify({"error": "Invalid file type. Only PDF is allowed."}), 400

@app.route('/api/job-match', methods=['POST'])
def job_match():
    data = request.json or {}
    job_description = data.get('job_description', '')
    
    if not job_description:
        return jsonify({"error": "Job description is required"}), 400
        
    if not session_data.get("resume_text"):
        return jsonify({"error": "Please upload a resume first"}), 400
        
    match_results = match_job_description(session_data["resume_text"], job_description)
    store_api_event("job_match", {
        "job_description": job_description,
        "resume_text_preview": session_data["resume_text"][:200],
        "match_results": match_results
    })
    return jsonify(match_results), 200

@app.route('/api/interview', methods=['POST'])
def generate_questions():
    data = request.json or {}
    job_description = data.get('job_description', '')
    
    if not session_data.get("resume_text"):
        return jsonify({"error": "Please upload a resume first"}), 400
        
    questions_data = generate_interview_questions(session_data["resume_text"], job_description)
    store_api_event("interview", {
        "job_description": job_description,
        "resume_text_preview": session_data["resume_text"][:200],
        "questions": questions_data
    })
    return jsonify(questions_data), 200

@app.route('/api/feedback', methods=['POST'])
def submit_answer():
    data = request.json
    question = data.get('question', '')
    answer = data.get('answer', '')
    
    if not question or not answer:
        return jsonify({"error": "Both question and answer are required"}), 400
        
    evaluation = evaluate_interview_answer(question, answer)
    store_api_event("feedback", {
        "question": question,
        "answer": answer,
        "evaluation": evaluation
    })
    return jsonify(evaluation), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
