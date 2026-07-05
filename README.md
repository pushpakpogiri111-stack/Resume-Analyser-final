# 🚀 Skillora – AI-Powered Career Preparation Platform

**An AI-powered career preparation platform that helps job seekers optimize resumes, analyze ATS compatibility, identify skill gaps, practice AI-driven interviews, and improve hiring success.**

---

## 🎬 Project Demo

🎥 **Watch the complete project demonstration here:**

▶️ https://youtu.be/RQQhUbTDdbA

---

# 🌟 Overview

**Skillora** is a full-stack AI-powered career preparation platform designed to help students and professionals become job-ready through intelligent resume analysis and AI-powered interview preparation.

The platform leverages Artificial Intelligence to evaluate resumes against target job descriptions, calculate ATS compatibility, identify missing technical and soft skills, generate personalized interview questions, and provide detailed AI feedback on interview responses.

Whether you're preparing for internships, campus placements, or professional job opportunities, Skillora streamlines the entire job preparation journey by combining resume optimization, ATS scoring, skill-gap analysis, AI mock interviews, and personalized career guidance into one intelligent platform.

---

# 🏗️ System Architecture

```text
                     Job Seeker
                          │
                          ▼
                Authentication System
                          │
                          ▼
                 React Frontend (Vite)
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
 Resume Analyzer     AI Interview     Career Dashboard
        │                 │                 │
        └──────────────┬──┴─────────────────┘
                       ▼
                Express REST API
                       │
      ┌────────────────┼─────────────────┐
      ▼                ▼                 ▼
   MongoDB        AI Services      PDF Processing
                       │
        ┌──────────────┴───────────────┐
        ▼                              ▼
     OpenAI API                 Resume Intelligence
```

---

# ✨ Features

## 📄 AI Resume Analyzer

- Upload Resume (PDF)
- Resume Text Extraction
- Resume Summary
- ATS Compatibility Score
- Resume Quality Analysis
- Resume Recommendations

---

## 🎯 ATS Optimization

- ATS Score Calculation
- Resume Ranking
- Keyword Matching
- Resume Improvement Suggestions
- Shortlist Prediction

---

## 🧠 Skill Gap Analysis

- Extract Resume Skills
- Compare with Job Description
- Matched Skills
- Missing Skills
- Personalized Skill Recommendations

---

## 🎤 AI Mock Interview

- AI-generated Interview Questions
- Technical Interview Practice
- Behavioral Interview Questions
- AI Answer Evaluation
- Confidence Assessment
- Communication Analysis
- Technical Knowledge Rating
- Personalized Feedback

---

## 📊 Career Dashboard

- Resume Analytics
- ATS Score Visualization
- Skill Match Percentage
- Interview Performance
- Career Insights
- Progress Tracking

---

## 🤖 AI Modules

| Module | Description |
|---------|-------------|
| Resume Analyzer | Extracts and analyzes resume content |
| ATS Checker | Calculates ATS compatibility score |
| Skill Gap Detector | Identifies missing skills for target jobs |
| AI Interview Generator | Creates personalized interview questions |
| Interview Evaluator | Provides AI-powered answer evaluation |
| Career Assistant | Offers career guidance and recommendations |

---

## 🌍 User Experience

- Modern Responsive UI
- Interactive Dashboard
- Real-time AI Feedback
- Smooth Navigation
- Mobile-Friendly Design

---

## 🔐 Security

- JWT Authentication
- Secure REST APIs
- Protected Routes
- Role-Based Authorization
- Password Encryption

---

# 🚀 Tech Stack

## Frontend

- React.js
- Vite
- Tailwind CSS
- JavaScript
- Axios
- React Router DOM

---

## Backend

- Node.js
- Express.js
- MongoDB
- Mongoose
- JWT Authentication
- Multer
- bcrypt.js

---

## AI Integration

- OpenAI API
- Resume Parsing
- ATS Resume Analysis
- AI Interview Evaluation
- Intelligent Career Recommendations

---

## Development Tools

- VS Code
- Git
- GitHub
- Postman
- npm

---

# 📂 Project Structure

```text
Skillora/
│
├── client/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── context/
│   │   └── utils/
│   │
│   └── package.json
│
├── server/
│   ├── controllers/
│   ├── middleware/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── uploads/
│   ├── utils/
│   ├── config/
│   └── server.js
│
├── README.md
└── package.json
```

---

# ⚙️ Installation

## Clone the Repository

```bash
git clone https://github.com/yourusername/Skillora.git
```

Navigate into the project

```bash
cd Skillora
```

---

## Install Frontend

```bash
cd client
npm install
npm run dev
```

---

## Install Backend

```bash
cd server
npm install
npm run dev
```

---

## Environment Variables

Create a `.env` file inside the **server** directory.

```env
PORT=5000

MONGODB_URI=your_mongodb_connection_string

JWT_SECRET=your_jwt_secret

OPENAI_API_KEY=your_openai_api_key
```

---

# 📈 Project Highlights

✅ Full-Stack MERN Architecture

✅ AI-Powered Resume Analysis

✅ ATS Compatibility Scoring

✅ Resume Skill Gap Detection

✅ AI Mock Interview Platform

✅ Personalized AI Feedback

✅ Secure Authentication & Authorization

✅ RESTful API Architecture

✅ Modular Backend Design

✅ Responsive User Interface

✅ Resume PDF Processing

✅ Career Analytics Dashboard

---

# 🎯 Future Enhancements

📹 Video Interview Analysis

🗣️ Voice-Based AI Interviews

📄 AI Resume Builder

🌐 LinkedIn Profile Analysis

📚 Personalized Learning Roadmap

🏆 Coding Assessment Platform

📈 Career Progress Analytics

📱 Mobile Application

🤝 Company Recruitment Portal

---

# 👥 Team Project

**Skillora** was developed collaboratively as a team project involving frontend development, backend API implementation, database design, secure authentication, AI integration, resume parsing, ATS evaluation, interview assessment, and responsive dashboard development.

---

# 🌍 Vision

Empowering students and professionals with Artificial Intelligence to build stronger resumes, bridge skill gaps, master interviews, and unlock better career opportunities through an intelligent, accessible, and personalized career preparation platform.

---

# ⭐ Support

If you found this project interesting, consider giving it a **⭐ Star**!

**Built with ❤️ using MERN Stack & Artificial Intelligence.**
