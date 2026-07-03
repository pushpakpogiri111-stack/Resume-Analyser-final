const express = require('express');
const cors = require('cors');
const multer = require('multer');
const pdfParse = require('pdf-parse');
const { OpenAI } = require('openai');
const dotenv = require('dotenv');
const fs = require('fs');
const path = require('path');

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

// Serve static frontend files
app.use(express.static(path.join(__dirname, '../frontend')));

const upload = multer({ dest: 'uploads/' });
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY || "dummy_key" });

const isMockMode = process.env.OPENAI_API_KEY === 'your_openai_api_key_here' || !process.env.OPENAI_API_KEY;

// Simple in-memory storage
let sessionData = { resume_text: "" };

// In-memory user storage (in production, use a database)
let users = {};
let sessions = {}; // token -> user mapping

// Shared skills pool and helper to extract skills from text
const SKILLS_POOL = [
    "JavaScript","React","Node.js","HTML","CSS","TypeScript","Python","Django","Flask","AWS","Docker","Kubernetes","SQL","MongoDB","GraphQL","Redux","Git","Linux","C++","Java"
];
// Build aliases for better matching (e.g., React -> react, reactjs, react.js)
const SKILL_ALIASES = {
    "JavaScript": ["javascript", "js"],
    "React": ["react", "reactjs", "react.js"],
    "Node.js": ["node", "nodejs", "node.js"],
    "HTML": ["html"],
    "CSS": ["css"],
    "TypeScript": ["typescript", "ts"],
    "Python": ["python"],
    "Django": ["django"],
    "Flask": ["flask"],
    "AWS": ["aws", "amazon web services"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "SQL": ["sql"],
    "MongoDB": ["mongodb", "mongo"],
    "GraphQL": ["graphql"],
    "Redux": ["redux"],
    "Git": ["git"],
    "Linux": ["linux"],
    "C++": ["c++", "cpp"],
    "Java": ["java"]
};

const normalizeTextForMatching = (text) => {
    if (!text) return "";
    return text.toLowerCase().replace(/[^a-z0-9+]+/g, ' ');
};

const extractSkillsFromText = (text) => {
    const found = [];
    if (!text) return found;
    const norm = normalizeTextForMatching(text);
    for (const skill of SKILLS_POOL) {
        const aliases = SKILL_ALIASES[skill] || [skill.toLowerCase()];
        for (const a of aliases) {
            const aNorm = a.toLowerCase().replace(/[^a-z0-9]+/g, ' ');
            // match alias as whole token in normalized text
            const re = new RegExp('\\b' + aNorm.split(' ').filter(Boolean).join('\\s+') + '\\b', 'i');
            if (re.test(norm)) {
                found.push(skill);
                break;
            }
        }
    }
    return found;
};

// Compute analysis from plain resume text (used by upload and test route)
const computeAnalysisFromText = (resumeText) => {
    const skillsPool = SKILLS_POOL;
    const foundSkills = extractSkillsFromText(resumeText);
    const matchedCount = foundSkills.length;
    const totalSkills = skillsPool.length;

    let ats_score = Math.round((matchedCount / totalSkills) * 100);
    if (ats_score < 20) ats_score = Math.max(10, ats_score);
    if (ats_score > 98) ats_score = 98;

    const wordCount = resumeText.split(/\s+/).filter(Boolean).length;
    const lengthScore = Math.min(100, Math.round(wordCount * 1.5));
    const chance_of_selection = Math.round((ats_score * 0.65) + (lengthScore * 0.35));

    const missing_skills = skillsPool.filter(s => !foundSkills.includes(s)).slice(0, 6);
    const suggestions = [];
    if (matchedCount === 0) suggestions.push("Add clear technical skills and keywords (e.g., JavaScript, React, Node.js).");
    else if (matchedCount < 4) suggestions.push("Highlight more hands-on skills and projects to improve ATS match.");
    else suggestions.push("Good skill coverage — add measurable achievements for each project.");
    if (wordCount < 150) suggestions.push("Expand experience descriptions with concrete outcomes and metrics.");
    else suggestions.push("Consider adding links to repos or deployed projects for reviewers.");

    return {
        ats_score,
        skills: foundSkills,
        missing_skills,
        suggestions,
        chance_of_selection
    };
};

// Helper to extract JSON from AI response
const cleanJSON = (str) => {
    let result = str.trim();
    if (result.startsWith("```json")) result = result.slice(7, -3).trim();
    else if (result.startsWith("```")) result = result.slice(3, -3).trim();
    return JSON.parse(result);
};

// Simple token generation (in production, use JWT)
const generateToken = () => Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);

// Authentication middleware
const requireAuth = (req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1] || req.query.token;
    if (!token || !sessions[token]) {
        return res.status(401).json({ error: "Unauthorized. Please login first." });
    }
    req.user = sessions[token];
    next();
};

// AUTH ENDPOINTS
// Register
app.post('/api/register', async (req, res) => {
    try {
        const { email, password, fullName } = req.body;
        
        if (!email || !password) {
            return res.status(400).json({ error: "Email and password required" });
        }
        
        if (users[email]) {
            return res.status(400).json({ error: "User already exists" });
        }
        
        // Simple password hashing (in production, use bcrypt)
        const hashedPassword = Buffer.from(password).toString('base64');
        
        users[email] = {
            email,
            password: hashedPassword,
            fullName: fullName || email.split('@')[0],
            createdAt: new Date()
        };
        
        const token = generateToken();
        sessions[token] = { email, fullName: fullName || email.split('@')[0] };
        
        res.json({ success: true, token, user: { email, fullName: users[email].fullName } });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Login
app.post('/api/login', async (req, res) => {
    try {
        const { email, password } = req.body;
        
        if (!email || !password) {
            return res.status(400).json({ error: "Email and password required" });
        }
        
        const user = users[email];
        if (!user) {
            return res.status(401).json({ error: "Invalid email or password" });
        }
        
        // Simple password verification (in production, use bcrypt)
        const hashedPassword = Buffer.from(password).toString('base64');
        if (user.password !== hashedPassword) {
            return res.status(401).json({ error: "Invalid email or password" });
        }
        
        const token = generateToken();
        sessions[token] = { email, fullName: user.fullName };
        
        res.json({ success: true, token, user: { email, fullName: user.fullName } });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Get current user
app.get('/api/user', (req, res) => {
    const token = req.headers.authorization?.split(' ')[1] || req.query.token;
    if (!token || !sessions[token]) {
        return res.status(401).json({ error: "Not authenticated" });
    }
    res.json({ user: sessions[token], token });
});

// Logout
app.post('/api/logout', (req, res) => {
    const token = req.headers.authorization?.split(' ')[1] || req.query.token;
    if (token && sessions[token]) {
        delete sessions[token];
    }
    res.json({ success: true });
});

// 1. Upload & Analyze Resume
app.post('/api/upload', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) return res.status(400).json({ error: 'No file uploaded' });

        const dataBuffer = fs.readFileSync(req.file.path);
        const data = await pdfParse(dataBuffer);
        sessionData.resume_text = data.text;

        // Clean up temp file
        fs.unlinkSync(req.file.path);

        const prompt = `Analyze this resume and return ONLY raw JSON: { "ats_score": number(0-100), "skills": [strings], "missing_skills": [strings], "suggestions": [strings], "chance_of_selection": number(0-100) }. Resume: ${data.text.substring(0, 3000)}`;

        let analysis;
        if (isMockMode) {
            analysis = computeAnalysisFromText(data.text || "");
        } else {
            const response = await openai.chat.completions.create({
                model: "gpt-4o-mini",
                messages: [{ role: "user", content: prompt }]
            });
            analysis = cleanJSON(response.choices[0].message.content);
        }

        res.json({ analysis, resume_text_preview: data.text.substring(0, 200) });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Failed to process resume." });
    }
});

// 2. Job Match
app.post('/api/job-match', async (req, res) => {
    try {
        const { job_description } = req.body;
        if (!sessionData.resume_text) return res.status(400).json({ error: "Upload resume first" });

        const prompt = `Compare resume to job description. Return ONLY raw JSON: { "match_percentage": number(0-100), "matched_skills": [strings], "missing_skills": [strings] }. Job: ${job_description}. Resume: ${sessionData.resume_text.substring(0, 3000)}`;

        if (isMockMode) {
            // Heuristic job-match: compare extracted skills from resume and job description
            const resumeText = sessionData.resume_text || "";
            const resumeSkills = extractSkillsFromText(resumeText);
            const jobSkills = extractSkillsFromText(job_description || "");

            const matched_skills = jobSkills.filter(s => resumeSkills.includes(s));
            const missing_skills = jobSkills.filter(s => !resumeSkills.includes(s));

            let match_percentage = 0;
            if (jobSkills.length > 0) {
                const skillPerc = Math.round((matched_skills.length / jobSkills.length) * 100);
                const resumeSkillCoverage = Math.round((resumeSkills.length / SKILLS_POOL.length) * 100);
                match_percentage = Math.round((skillPerc * 0.75) + (resumeSkillCoverage * 0.25));
            } else {
                match_percentage = Math.round((resumeSkills.length / SKILLS_POOL.length) * 100);
            }

            return res.json({ match_percentage, matched_skills, missing_skills, resume_skills: resumeSkills, job_skills: jobSkills });
        }

        const response = await openai.chat.completions.create({
            model: "gpt-4o-mini",
            messages: [{ role: "user", content: prompt }]
        });

        res.json(cleanJSON(response.choices[0].message.content));
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Test helper: upload plain resume text (useful during development)
app.post('/api/upload-text', express.json(), (req, res) => {
    try {
        const { text } = req.body || {};
        if (!text) return res.status(400).json({ error: 'No text provided' });
        sessionData.resume_text = text;
        const analysis = computeAnalysisFromText(text);
        res.json({ message: 'Text uploaded and analyzed', analysis, resume_text_preview: text.substring(0,200) });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 3. Generate Interview Questions
app.post('/api/interview', async (req, res) => {
    try {
        const { job_description } = req.body || {};
        if (!sessionData.resume_text) return res.status(400).json({ error: "Upload resume first" });

        const prompt = `Generate 5 interview questions based on this resume and the target job description. Return ONLY raw JSON: { "questions": [{ "question": "string", "type": "Technical or HR" }] }. Job Description: ${job_description || 'General'}. Resume: ${sessionData.resume_text.substring(0, 3000)}`;

        if (isMockMode) {
            // Heuristic question generation based on resume and job description
            const resumeText = sessionData.resume_text || "";
            const resumeSkills = extractSkillsFromText(resumeText);
            const jobSkills = extractSkillsFromText(job_description || "");

            const primarySkills = jobSkills.length ? jobSkills.slice(0, 3) : resumeSkills.slice(0, 3);
            const questions = [];

            primarySkills.forEach(s => {
                questions.push({ question: `Can you explain your experience with ${s}? Provide an example project and your role.`, type: "Technical" });
            });

            // Add behavioral question(s) detected from resume content
            const lc = resumeText.toLowerCase();
            if (lc.includes('team') || lc.includes('lead') || lc.includes('managed')) {
                questions.push({ question: "Describe a time you led a team to deliver a project. What challenges did you face?", type: "HR" });
            }

            // Fill up to 5 questions with generic ones
            const filler = [
                { q: "How do you approach debugging complex issues?", t: "Technical" },
                { q: "Describe a time you handled a tight deadline and what you learned.", t: "HR" },
                { q: "How do you ensure code quality and maintainability?", t: "Technical" }
            ];

            let fi = 0;
            while (questions.length < 5 && fi < filler.length) {
                questions.push({ question: filler[fi].q, type: filler[fi].t });
                fi++;
            }

            return res.json({ questions, resume_skills: resumeSkills, job_skills: jobSkills, primary_skills: primarySkills });
        }

        const response = await openai.chat.completions.create({
            model: "gpt-4o-mini",
            messages: [{ role: "user", content: prompt }]
        });

        res.json(cleanJSON(response.choices[0].message.content));
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 4. Feedback
app.post('/api/feedback', async (req, res) => {
    try {
        const { question, answer } = req.body;
        const prompt = `Evaluate candidate's answer. Return ONLY raw JSON: { "confidence_score": number(0-100), "communication_score": number(0-100), "technical_depth_score": number(0-100), "suggestions": "string" }. Question: ${question}. Answer: ${answer}`;

        if (isMockMode) {
            return res.json({
                "confidence_score": 85,
                "communication_score": 90,
                "technical_depth_score": 70,
                "suggestions": "Good answer! Try to include more specific technical examples next time."
            });
        }

        const response = await openai.chat.completions.create({
            model: "gpt-4o-mini",
            messages: [{ role: "user", content: prompt }]
        });

        res.json(cleanJSON(response.choices[0].message.content));
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

const PORT = 5000;
app.listen(PORT, () => console.log(`✅ Server running on http://localhost:${PORT}`));
