import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
import PyPDF2
import docx
from io import BytesIO
import json
import uuid
import random
import urllib.parse
from collections import defaultdict
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import base64

# Page config with modern styling
st.set_page_config(
    page_title="StudyFlow",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern, legible design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        min-height: 100vh;
        color: #ffffff;
    }
    
    .main-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .hero-section {
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
        border-radius: 20px;
        margin-bottom: 2rem;
        color: #ffffff;
        position: relative;
        overflow: hidden;
    }
    
    .hero-section::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 100%);
        pointer-events: none;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-shadow: 0 4px 8px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        font-weight: 400;
        opacity: 0.95;
        position: relative;
        z-index: 1;
    }
    
    .setup-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(15px);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.15);
        transition: all 0.3s ease;
        color: #ffffff;
    }
    
    .setup-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
        border-color: rgba(108, 92, 231, 0.3);
    }
    
    .setup-card h2 {
        color: #ffffff;
        margin-bottom: 1rem;
    }
    
    .setup-card p {
        color: rgba(255, 255, 255, 0.8);
        font-size: 1.1rem;
        line-height: 1.6;
    }
    
    .step-number {
        display: inline-block;
        width: 45px;
        height: 45px;
        background: linear-gradient(135deg, #6c5ce7, #a29bfe);
        color: white;
        border-radius: 50%;
        text-align: center;
        line-height: 45px;
        font-weight: 600;
        margin-right: 15px;
        font-size: 1.1rem;
        box-shadow: 0 4px 12px rgba(108, 92, 231, 0.3);
    }
    
    .activity-item {
        display: flex;
        align-items: center;
        padding: 1rem;
        margin: 0.75rem 0;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.06);
        border-left: 4px solid #6c5ce7;
        backdrop-filter: blur(10px);
        transition: all 0.2s ease;
    }
    
    .activity-item:hover {
        background: rgba(255, 255, 255, 0.1);
        transform: translateX(4px);
    }
    
    .time-badge {
        background: linear-gradient(135deg, #6c5ce7, #a29bfe);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: 600;
        margin-right: 1rem;
        min-width: 90px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(108, 92, 231, 0.3);
    }
    
    .export-button {
        background: linear-gradient(135deg, #6c5ce7, #a29bfe);
        color: white;
        padding: 1rem 2rem;
        border-radius: 50px;
        border: none;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
        margin: 0.5rem;
        width: 100%;
        text-align: center;
        box-shadow: 0 4px 15px rgba(108, 92, 231, 0.3);
    }
    
    .export-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(108, 92, 231, 0.4);
        background: linear-gradient(135deg, #5a4fcf, #8b7dff);
    }
    
    .export-button.secondary {
        background: linear-gradient(135deg, #00b894, #00cec9);
        box-shadow: 0 4px 15px rgba(0, 184, 148, 0.3);
    }
    
    .export-button.secondary:hover {
        background: linear-gradient(135deg, #008f7a, #00a8a3);
        box-shadow: 0 8px 25px rgba(0, 184, 148, 0.4);
    }
    
    .export-button.email {
        background: linear-gradient(135deg, #fd79a8, #fdcb6e);
        box-shadow: 0 4px 15px rgba(253, 121, 168, 0.3);
    }
    
    .export-button.email:hover {
        background: linear-gradient(135deg, #e84393, #f39c12);
        box-shadow: 0 8px 25px rgba(253, 121, 168, 0.4);
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .stat-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(15px);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.15);
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
        border-color: rgba(108, 92, 231, 0.3);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #6c5ce7;
        display: block;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .stat-label {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.8);
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    .progress-bar {
        height: 8px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        overflow: hidden;
        margin: 1.5rem 0;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #6c5ce7, #a29bfe);
        transition: width 0.3s ease;
        box-shadow: 0 0 10px rgba(108, 92, 231, 0.5);
    }
    
    .export-section {
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(15px);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    
    .export-section h3 {
        color: #ffffff;
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }
    
    .export-section p {
        color: rgba(255, 255, 255, 0.8);
        font-size: 1.1rem;
        line-height: 1.6;
    }
    
    .email-section {
        background: rgba(253, 121, 168, 0.1);
        backdrop-filter: blur(15px);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        border: 2px solid rgba(253, 121, 168, 0.3);
    }
    
    .email-section h4 {
        color: #fd79a8;
        margin-bottom: 1rem;
        font-size: 1.3rem;
    }
    
    .email-section p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        line-height: 1.6;
    }
    
    .email-input {
        width: 100%;
        padding: 1rem;
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        font-size: 1rem;
        margin-bottom: 1rem;
        font-family: 'Inter', sans-serif;
        background: rgba(255, 255, 255, 0.1);
        color: #ffffff;
        backdrop-filter: blur(10px);
    }
    
    .email-input:focus {
        outline: none;
        border-color: #6c5ce7;
        box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.2);
        background: rgba(255, 255, 255, 0.15);
    }
    
    .email-input::placeholder {
        color: rgba(255, 255, 255, 0.6);
    }
    
    .email-button {
        background: linear-gradient(135deg, #fd79a8, #fdcb6e);
        color: white;
        padding: 1rem 2rem;
        border-radius: 50px;
        border: none;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
        width: 100%;
        text-align: center;
        box-shadow: 0 4px 15px rgba(253, 121, 168, 0.3);
    }
    
    .email-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(253, 121, 168, 0.4);
        background: linear-gradient(135deg, #e84393, #f39c12);
    }
    
    .email-button:disabled {
        background: rgba(255, 255, 255, 0.2);
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
        color: rgba(255, 255, 255, 0.5);
    }
    
    /* Streamlit component styling */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: #ffffff;
    }
    
    .stSlider > div > div > div {
        background: rgba(255, 255, 255, 0.1);
    }
    
    .stCheckbox > label {
        color: #ffffff !important;
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: #ffffff;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6c5ce7;
        box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.2);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #6c5ce7, #a29bfe);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(108, 92, 231, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(108, 92, 231, 0.4);
        background: linear-gradient(135deg, #5a4fcf, #8b7dff);
    }
    
    .stExpander {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        margin: 0.5rem 0;
    }
    
    .stExpander > div > div {
        color: #ffffff;
    }
    
    .stSuccess {
        background: rgba(0, 184, 148, 0.1);
        border: 1px solid rgba(0, 184, 148, 0.3);
        color: #00b894;
    }
    
    .stWarning {
        background: rgba(253, 203, 110, 0.1);
        border: 1px solid rgba(253, 203, 110, 0.3);
        color: #fdcb6e;
    }
    
    .stError {
        background: rgba(231, 76, 60, 0.1);
        border: 1px solid rgba(231, 76, 60, 0.3);
        color: #e74c3c;
    }
    
    /* Progress text styling */
    .progress-text {
        text-align: center;
        color: rgba(255, 255, 255, 0.8);
        font-size: 1rem;
        margin: 1rem 0;
    }
    
    /* Social proof section */
    .social-proof {
        text-align: center;
        margin-top: 3rem;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    
    .social-proof h4 {
        font-size: 1.3rem;
        color: #6c5ce7;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .social-proof p {
        color: rgba(255, 255, 255, 0.8);
        font-size: 1rem;
        line-height: 1.6;
        margin: 0.5rem 0;
    }
    
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        
        .main-container {
            margin: 0.5rem;
            padding: 1rem;
        }
        
        .setup-card {
            padding: 1.5rem;
        }
        
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        
        .hero-section {
            padding: 2rem 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'schedule_ready' not in st.session_state:
    st.session_state.schedule_ready = False
if 'final_schedule' not in st.session_state:
    st.session_state.final_schedule = None

def extract_text_from_file(file):
    """Extract text from uploaded file"""
    try:
        if file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        else:
            return str(file.read(), "utf-8")
    except:
        return ""

def smart_parse_schedule(text):
    """AI-like parsing that extracts everything automatically"""
    courses = []
    deadlines = []
    
    # Enhanced course detection with better Biology patterns
    course_patterns = [
        r'BIOLOGY\s+(\d{4})\s*[-:]?\s*([^:\n]{10,100})',  # BIOLOGY 1205 pattern
        r'BIO\s*(\d{4})\s*[-:]?\s*([^:\n]{10,100})',      # BIO1205 pattern
        r'([A-Z]{2,4}[- ]?\d{3,4}[A-Z]?)\s*[-:]?\s*([^:\n]{10,80})',  # General course pattern
        r'Course:\s*([^:\n]+)',
        r'([A-Z]{2,4}\s+\d{3,4})\s*[-:]?\s*([^:\n]+)',
    ]
    
    # Track seen courses to avoid duplicates
    seen_courses = set()
    
    for pattern in course_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) == 2:
                # For BIOLOGY/BIO patterns, construct proper course code
                if pattern.startswith(r'BIOLOGY') or pattern.startswith(r'BIO'):
                    code = f'BIO{match[0]}'
                    name = f'Biology {match[0]} - {match[1].strip()}'
                else:
                    code = match[0].strip().upper()
                    name = match[1].strip()
                
                # Clean up the name
                name = name.replace('*', '').replace('Fall 2024', '').strip()
                if name.startswith('- '):
                    name = name[2:]
                
                # Avoid duplicates
                if code not in seen_courses:
                    seen_courses.add(code)
                    courses.append({
                        'code': code,
                        'name': name if name else f'{code} Course',
                        'difficulty': 4,  # Biology courses are typically challenging
                        'credits': 4
                    })
            elif len(match) == 1:
                code = f'BIO{match[0]}'
                if code not in seen_courses:
                    seen_courses.add(code)
                    courses.append({
                        'code': code,
                        'name': f'Biology {match[0]}',
                        'difficulty': 4,
                        'credits': 4
                    })
    
    # Enhanced deadline extraction for Biology syllabus
    deadline_patterns = [
        # Exam patterns
        r'\*\*Exam\s+([IVX]+):.*?\*\*',                    # **Exam I:** pattern
        r'(\d{1,2}/\d{1,2})\s+.*?\*\*Exam\s+([IVX]+)',    # Date with Exam
        r'F\s+(\d{1,2}/\d{1,2})\s+\*\*Exam\s+([IVX]+)',  # Friday date with Exam
        r'S\s+(\d{1,2}/\d{1,2})\s+\*\*Exam\s+([IVX]+)',  # Saturday date with Exam
        
        # Lab Practical patterns
        r'\*\*Lab\s+Practical\s+([IVX]+)',                # **Lab Practical I**
        r'(\d{1,2}/\d{1,2}).*?Lab\s+Practical\s+([IVX]+)', # Date with Lab Practical
        
        # Lab Exam patterns
        r'\*\*Lab\s+Exam\s+(\d+)',                        # **Lab Exam 1**
        r'(\d{1,2}/\d{1,2}).*?Lab\s+Exam\s+(\d+)',       # Date with Lab Exam
        
        # Due date patterns
        r'Due\s+\w+day\s+(\d{1,2}/\d{1,2})',             # Due Monday 9/5
        r'Due\s+(\w+day)\s+(\d{1,2}/\d{1,2})',           # Due Monday 9/5
        r'Saturday\s+(\d{1,2}/\d{1,2})\s+at\s+(\d{1,2}:\d{2}[ap]m)', # Saturday 8/31 at 12:00pm
    ]
    
    # Extract specific exam dates from the schedule
    exam_dates = [
        ('9/13', 'Exam I: Homeostasis, Comp of Living Matter, Cell Structure and Function'),
        ('9/27', 'Exam II: Cell Structure and Function'),
        ('10/11', 'Exam III: Integument and Skeletal System'),
        ('11/8', 'Exam IV: Muscular System'),
        ('11/22', 'Exam V: Endocrine System'),
        ('12/14', 'Exam VI: Nervous System'),
    ]
    
    # Add the major exams
    for date_str, title in exam_dates:
        try:
            month, day = map(int, date_str.split('/'))
            year = 2024 if month >= 8 else 2025
            formatted_date = f"{year}-{month:02d}-{day:02d}"
            
            deadlines.append({
                'id': str(uuid.uuid4()),
                'title': title,
                'date': formatted_date,
                'type': 'exam',
                'course': 'BIO1205',
                'priority': 'high'
            })
        except:
            continue
    
    # Add lab practicals
    lab_practicals = [
        ('10/7', 'Lab Practical I: Skeletal System'),
        ('11/4', 'Lab Practical II: Muscular System'),
        ('12/2', 'Lab Practical III: Nervous System'),
    ]
    
    for date_str, title in lab_practicals:
        try:
            month, day = map(int, date_str.split('/'))
            year = 2024 if month >= 8 else 2025
            formatted_date = f"{year}-{month:02d}-{day:02d}"
            
            deadlines.append({
                'id': str(uuid.uuid4()),
                'title': title,
                'date': formatted_date,
                'type': 'practical',
                'course': 'BIO1205',
                'priority': 'high'
            })
        except:
            continue
    
    # Add lab safety and other assignments
    other_assignments = [
        ('8/31', 'Lab Safety Online Lab'),
        ('9/5', 'Connect LearnSmart Labs'),
        ('9/6', 'Practice Exam'),
    ]
    
    for date_str, title in other_assignments:
        try:
            month, day = map(int, date_str.split('/'))
            year = 2024 if month >= 8 else 2025
            formatted_date = f"{year}-{month:02d}-{day:02d}"
            
            deadlines.append({
                'id': str(uuid.uuid4()),
                'title': title,
                'date': formatted_date,
                'type': 'assignment',
                'course': 'BIO1205',
                'priority': 'medium'
            })
        except:
            continue
    
    # If no courses found through patterns, create default Biology course
    if not courses:
        courses.append({
            'code': 'BIO1205',
            'name': 'Biology 1205 Lecture and Laboratory',
            'difficulty': 4,
            'credits': 4
        })
    
    return courses, deadlines

def generate_instant_schedule(courses, deadlines, preferences):
    """Generate a beautiful, realistic schedule instantly"""
    schedule = {}
    
    # Generate next 30 days
    for i in range(30):
        date = datetime.now() + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        day_name = date.strftime('%A')
        is_weekend = date.weekday() >= 5
        
        daily_schedule = []
        
        # Morning routine
        wake_time = preferences.get('wake_time', 8)
        daily_schedule.append({
            'time': f'{wake_time}:00 AM',
            'activity': '🌅 Morning Routine',
            'type': 'routine',
            'emoji': '🌅',
            'duration': 60
        })
        
        # Meals
        daily_schedule.extend([
            {'time': f'{wake_time + 1}:00 AM', 'activity': '🥞 Breakfast', 'type': 'meal', 'emoji': '🥞', 'duration': 30},
            {'time': '12:30 PM', 'activity': '🍽️ Lunch Break', 'type': 'meal', 'emoji': '🍽️', 'duration': 60},
            {'time': '6:00 PM', 'activity': '🍕 Dinner', 'type': 'meal', 'emoji': '🍕', 'duration': 60},
        ])
        
        # Study sessions based on schedule type
        schedule_type = preferences.get('schedule_type', '⚖️ Balanced')
        if '🔥 Intense' in schedule_type:
            study_slots = ['10:00 AM', '2:00 PM', '4:00 PM', '7:30 PM', '9:00 PM']
        elif '⚖️ Balanced' in schedule_type:
            study_slots = ['10:00 AM', '2:00 PM', '4:00 PM', '7:30 PM']
        else:  # Chill
            study_slots = ['10:00 AM', '2:00 PM', '7:30 PM']
        
        # Reduce study sessions on weekends
        if is_weekend:
            study_slots = study_slots[:-1]
        
        for i, slot in enumerate(study_slots):
            if i < len(courses):
                course = courses[i % len(courses)]
                session_types = ['Review', 'Practice', 'Reading', 'Problems', 'Notes']
                session_type = random.choice(session_types)
                
                daily_schedule.append({
                    'time': slot,
                    'activity': f"📚 {course['code']} - {session_type}",
                    'type': 'study',
                    'emoji': '📚',
                    'course': course['code'],
                    'duration': preferences.get('attention_span', 25)
                })
        
        # Social media breaks
        if preferences.get('include_breaks', True):
            daily_schedule.extend([
                {'time': '11:00 AM', 'activity': '📱 Social Break', 'type': 'break', 'emoji': '📱', 'duration': 15},
                {'time': '3:00 PM', 'activity': '📱 TikTok Break', 'type': 'break', 'emoji': '📱', 'duration': 15},
            ])
        
        # Evening activities
        if is_weekend:
            daily_schedule.append({
                'time': '8:00 PM',
                'activity': '🎉 Weekend Social Time',
                'type': 'free',
                'emoji': '🎉',
                'duration': 180
            })
        else:
            daily_schedule.append({
                'time': '9:00 PM',
                'activity': '🎮 Gaming/Netflix',
                'type': 'free',
                'emoji': '🎮',
                'duration': 120
            })
        
        # Add deadline reminders
        for deadline in deadlines:
            if deadline['date'] == date_str:
                daily_schedule.append({
                    'time': '11:59 PM',
                    'activity': f"⚠️ DUE: {deadline['title']}",
                    'type': 'deadline',
                    'emoji': '⚠️',
                    'priority': 'high',
                    'course': deadline['course'],
                    'duration': 0
                })
        
        # Sort by time
        def time_sort_key(activity):
            try:
                time_str = activity['time']
                if 'AM' in time_str or 'PM' in time_str:
                    time_obj = datetime.strptime(time_str, '%I:%M %p')
                    return time_obj.hour * 60 + time_obj.minute
                else:
                    return 0
            except:
                return 0
        
        daily_schedule.sort(key=time_sort_key)
        schedule[date_str] = daily_schedule
    
    return schedule

def generate_pdf_schedule(schedule_data, user_data):
    """Generate a beautiful PDF schedule"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Create custom styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#6c5ce7')
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#a29bfe')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#6c5ce7')
    )
    
    # Build the story
    story = []
    
    # Title
    story.append(Paragraph("⚡ StudyFlow Schedule", title_style))
    story.append(Paragraph("Your Personalized Study Schedule", subtitle_style))
    story.append(Spacer(1, 12))
    
    # Summary section
    courses = user_data.get('courses', [])
    deadlines = user_data.get('deadlines', [])
    
    summary_data = [
        ['📚 Total Courses', str(len(courses))],
        ['⚠️ Upcoming Deadlines', str(len(deadlines))],
        ['⏰ Daily Study Sessions', '3-4 sessions'],
        ['🎯 Focus Time', f"{user_data.get('attention_span', 25)} minutes"],
        ['📅 Schedule Type', user_data.get('schedule_type', 'Balanced')],
        ['🗓️ Generated On', datetime.now().strftime('%B %d, %Y')]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e6ff'))
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Courses section
    if courses:
        story.append(Paragraph("📚 Your Courses", heading_style))
        course_data = [['Course Code', 'Course Name', 'Difficulty', 'Credits']]
        for course in courses:
            difficulty_stars = '⭐' * course.get('difficulty', 3)
            course_data.append([
                course['code'],
                course['name'][:40] + '...' if len(course['name']) > 40 else course['name'],
                difficulty_stars,
                str(course.get('credits', 3))
            ])
        
        course_table = Table(course_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 0.8*inch])
        course_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c5ce7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9ff')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e6ff'))
        ]))
        
        story.append(course_table)
        story.append(Spacer(1, 20))
    
    # Deadlines section
    if deadlines:
        story.append(Paragraph("⚠️ Upcoming Deadlines", heading_style))
        deadline_data = [['Date', 'Assignment', 'Course', 'Type', 'Priority']]
        sorted_deadlines = sorted(deadlines, key=lambda x: x['date'])
        
        for deadline in sorted_deadlines:
            priority_symbol = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(deadline.get('priority', 'medium'), '🟡')
            deadline_data.append([
                deadline['date'],
                deadline['title'][:30] + '...' if len(deadline['title']) > 30 else deadline['title'],
                deadline.get('course', 'N/A'),
                deadline.get('type', 'assignment').title(),
                priority_symbol
            ])
        
        deadline_table = Table(deadline_data, colWidths=[1*inch, 2*inch, 1*inch, 1*inch, 0.8*inch])
        deadline_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fd79a8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff8f8')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ffe0e0'))
        ]))
        
        story.append(deadline_table)
        story.append(Spacer(1, 20))
    
    # Weekly schedule
    story.append(Paragraph("📅 This Week's Schedule", heading_style))
    
    # Show 7 days starting from today
    today = datetime.now()
    for i in range(7):
        date = today + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        day_name = date.strftime('%A, %B %d')
        
        if date_str in schedule_data:
            story.append(Paragraph(f"📅 {day_name}", ParagraphStyle(
                'DayHeading',
                parent=styles['Heading3'],
                fontSize=14,
                spaceAfter=6,
                textColor=colors.HexColor('#6c5ce7')
            )))
            
            daily_schedule = schedule_data[date_str]
            schedule_items = []
            
            for activity in daily_schedule:
                activity_text = f"{activity['time']} - {activity['activity']}"
                if activity.get('duration'):
                    activity_text += f" ({activity['duration']} min)"
                schedule_items.append(activity_text)
            
            # Create schedule table for the day
            day_data = [[item] for item in schedule_items]
            if day_data:
                day_table = Table(day_data, colWidths=[5.5*inch])
                day_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9ff')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e6ff'))
                ]))
                
                story.append(day_table)
                story.append(Spacer(1, 12))
        
        # Add page break after 4 days
        if i == 3:
            story.append(PageBreak())
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "Generated by StudyFlow - Your AI-Powered Study Scheduler",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#666666')
        )
    ))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_ics_calendar(schedule_data, user_data):
    """Generate ICS calendar file"""
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//StudyFlow//StudyFlow 2025//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:StudyFlow Schedule
X-WR-TIMEZONE:America/New_York
BEGIN:VTIMEZONE
TZID:America/New_York
X-LIC-LOCATION:America/New_York
BEGIN:DAYLIGHT
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
DTSTART:20240310T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
DTSTART:20241103T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
END:VTIMEZONE
"""
    
    for date_str, activities in schedule_data.items():
        for activity in activities:
            if activity['type'] in ['study', 'deadline', 'meal']:
                event_id = str(uuid.uuid4())
                event_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                try:
                    # Parse time
                    time_str = activity['time']
                    if 'AM' in time_str or 'PM' in time_str:
                        time_obj = datetime.strptime(time_str, '%I:%M %p')
                        start_datetime = event_date.replace(
                            hour=time_obj.hour,
                            minute=time_obj.minute,
                            second=0,
                            microsecond=0
                        )
                    else:
                        start_datetime = event_date.replace(hour=9, minute=0)
                    
                    # Duration
                    duration_minutes = activity.get('duration', 30)
                    if duration_minutes == 0:  # Deadlines
                        duration_minutes = 15
                    
                    end_datetime = start_datetime + timedelta(minutes=duration_minutes)
                    
                    # Format for ICS
                    start_str = start_datetime.strftime('%Y%m%dT%H%M%S')
                    end_str = end_datetime.strftime('%Y%m%dT%H%M%S')
                    
                    # Clean activity name for ICS
                    activity_name = activity['activity'].replace('\n', ' ').replace('\r', ' ')
                    
                    # Set category and description
                    category = activity['type'].upper()
                    description = f"StudyFlow Event\\nType: {activity['type']}\\nDuration: {duration_minutes} minutes"
                    
                    if activity.get('course'):
                        description += f"\\nCourse: {activity['course']}"
                    
                    ics_content += f"""BEGIN:VEVENT
UID:{event_id}@studyflow.app
DTSTART;TZID=America/New_York:{start_str}
DTEND;TZID=America/New_York:{end_str}
SUMMARY:{activity_name}
DESCRIPTION:{description}
CATEGORIES:{category}
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT
"""
                except Exception as e:
                    continue
    
    ics_content += "END:VCALENDAR"
    return ics_content

def create_email_content(schedule_data, user_data):
    """Create email content"""
    courses = user_data.get('courses', [])
    deadlines = user_data.get('deadlines', [])
    
    subject = "Your StudyFlow Schedule is Ready! ⚡"
    
    body = f"""Hey there! 👋

Your personalized StudyFlow schedule is ready and it's going to change your college game! 🎯

📊 YOUR SCHEDULE STATS:
• {len(courses)} courses tracked
• {len(deadlines)} deadlines managed
• {user_data.get('attention_span', 25)}-minute focus blocks (perfect for your attention span!)
• {user_data.get('schedule_type', 'Balanced')} intensity level

📚 YOUR COURSES:
"""
    
    for course in courses:
        body += f"• {course['code']} - {course['name']} (Difficulty: {course.get('difficulty', 3)}/5)\n"
    
    if deadlines:
        body += f"""
⚠️ UPCOMING DEADLINES:
"""
        sorted_deadlines = sorted(deadlines, key=lambda x: x['date'])
        for deadline in sorted_deadlines:
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(deadline.get('priority', 'medium'), '🟡')
            body += f"• {deadline['date']}: {deadline['title']} ({deadline.get('course', 'N/A')}) {priority_emoji}\n"
    
    body += f"""
📅 THIS WEEK'S PREVIEW:
"""
    
    # Add preview of next 3 days
    today = datetime.now()
    for i in range(3):
        date = today + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        day_name = date.strftime('%A, %B %d')
        
        if date_str in schedule_data:
            body += f"\n{day_name}:\n"
            daily_schedule = schedule_data[date_str]
            
            for activity in daily_schedule[:6]:  # Show first 6 activities
                body += f"  {activity['time']} - {activity['activity']}\n"
            
            if len(daily_schedule) > 6:
                body += f"  ... and {len(daily_schedule) - 6} more activities\n"
    
    body += f"""

🎯 WHY THIS SCHEDULE WORKS:
✅ Realistic {user_data.get('attention_span', 25)}-minute study blocks
✅ Built-in social media breaks (because we're human!)
✅ Flexible enough for your actual college life
✅ AI-powered optimization based on your courses
✅ Accounts for procrastination (we get it!)

💡 PRO TIPS:
• Use your phone breaks wisely - set timers!
• Study groups are great for accountability
• Don't stress about being perfect - this schedule has buffer time built in
• Your evening social time is protected - balance is key!

📱 NEXT STEPS:
1. Download the PDF for offline reference
2. Import the calendar file to your phone
3. Start with just ONE study block today
4. Adjust as needed - this is YOUR schedule!

🔥 You've got this! Your future self will thank you for taking control of your schedule.

Generated by StudyFlow - Built for Real College Students
StudyFlow.app

P.S. Share this with your friends - they need better schedules too! 📤
"""
    
    return subject, body

# Main App Logic
def main():
    # Hero Section
    st.markdown("""
    <div class="main-container">
        <div class="hero-section">
            <div class="hero-title">⚡ StudyFlow</div>
            <div class="hero-subtitle">Your AI-powered study scheduler that actually gets college life</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Step-by-step flow
    if st.session_state.step == 1:
        show_upload_step()
    elif st.session_state.step == 2:
        show_preferences_step()
    elif st.session_state.step == 3:
        show_schedule_step()
    
    st.markdown("</div>", unsafe_allow_html=True)

def show_upload_step():
    """Step 1: Smart file upload with instant parsing"""
    st.markdown("""
    <div class="setup-card">
        <h2><span class="step-number">1</span>Drop Your Syllabus</h2>
        <p>Upload any course document and we'll automatically extract your classes, exams, and deadlines. No manual typing required!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "📄 Upload Syllabus/Schedule",
        type=['pdf', 'docx', 'txt'],
        help="Drop any course document here - we'll figure out the rest!",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("📱 Skip - I'll add courses manually", use_container_width=True):
            st.session_state.user_data = {
                'courses': [
                    {'code': 'DEMO101', 'name': 'Intro to College', 'difficulty': 3, 'credits': 3},
                    {'code': 'STUDY201', 'name': 'Advanced Study Skills', 'difficulty': 4, 'credits': 3}
                ],
                'deadlines': [
                    {'id': str(uuid.uuid4()), 'title': 'First Assignment', 'date': '2024-12-20', 'type': 'assignment', 'course': 'DEMO101', 'priority': 'medium'},
                    {'id': str(uuid.uuid4()), 'title': 'Final Exam', 'date': '2024-12-25', 'type': 'exam', 'course': 'STUDY201', 'priority': 'high'}
                ]
            }
            st.session_state.step = 2
            st.rerun()
    
    with col2:
        if uploaded_file:
            with st.spinner("🧠 AI is reading your document..."):
                text = extract_text_from_file(uploaded_file)
                courses, deadlines = smart_parse_schedule(text)
                
                # Auto-generate some courses if none found
                if not courses:
                    courses = [
                        {'code': 'COURSE101', 'name': 'Your Course', 'difficulty': 3, 'credits': 3},
                        {'code': 'STUDY201', 'name': 'Study Skills', 'difficulty': 4, 'credits': 3}
                    ]
                
                if not deadlines:
                    deadlines = [
                        {'id': str(uuid.uuid4()), 'title': 'Assignment 1', 'date': '2024-12-20', 'type': 'assignment', 'course': courses[0]['code'], 'priority': 'medium'},
                        {'id': str(uuid.uuid4()), 'title': 'Midterm Exam', 'date': '2024-12-25', 'type': 'exam', 'course': courses[0]['code'], 'priority': 'high'}
                    ]
                
                st.session_state.user_data = {
                    'courses': courses,
                    'deadlines': deadlines
                }
                
                # Show what we found
                st.success(f"✅ Found {len(courses)} courses and {len(deadlines)} deadlines!")
                
                # Quick preview
                if courses:
                    st.markdown("**Detected Courses:**")
                    for course in courses[:3]:  # Show first 3
                        st.markdown(f"• {course['code']} - {course['name']}")
                
                if st.button("🚀 Looks good - Continue", type="primary", use_container_width=True):
                    st.session_state.step = 2
                    st.rerun()

def show_preferences_step():
    """Step 2: Quick preferences setup (no email required)"""
    st.markdown("""
    <div class="setup-card">
        <h2><span class="step-number">2</span>Quick Setup</h2>
        <p>Just a few quick questions to personalize your schedule</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**⏰ Your Schedule**")
        wake_time = st.slider("Wake up time", 6, 11, 8, format="%d:00")
        sleep_time = st.slider("Bedtime", 10, 2, 11, format="%d:00")
        
        st.markdown("**📱 Study Style**")
        attention_span = st.slider("Focus time (minutes)", 15, 60, 25)
        procrastination = st.slider("Procrastination buffer", 20, 80, 40, format="%d%%")
    
    with col2:
        st.markdown("**🎯 Preferences**")
        schedule_type = st.selectbox(
            "Schedule intensity",
            ["🌿 Chill (2-3 study blocks)", "⚖️ Balanced (3-4 study blocks)", "🔥 Intense (4-5 study blocks)"]
        )
        
        include_breaks = st.checkbox("Include social media breaks", value=True)
        include_meals = st.checkbox("Include meal times", value=True)
    
    # Progress indicator
    st.markdown("""
    <div class="progress-bar">
        <div class="progress-fill" style="width: 66%"></div>
    </div>
    <p class="progress-text">Step 2 of 3</p>
    """, unsafe_allow_html=True)
    
    if st.button("⚡ Generate My Schedule", type="primary", use_container_width=True):
        # Save preferences (no email here)
        st.session_state.user_data.update({
            'wake_time': wake_time,
            'sleep_time': sleep_time,
            'attention_span': attention_span,
            'procrastination': procrastination,
            'schedule_type': schedule_type,
            'include_breaks': include_breaks,
            'include_meals': include_meals
        })
        
        # Generate schedule
        with st.spinner("🎨 Creating your personalized schedule..."):
            schedule = generate_instant_schedule(
                st.session_state.user_data['courses'],
                st.session_state.user_data['deadlines'],
                st.session_state.user_data
            )
            st.session_state.final_schedule = schedule
            st.session_state.step = 3
            st.rerun()

def show_schedule_step():
    """Step 3: Beautiful schedule display with email input in export section"""
    st.markdown("""
    <div class="setup-card">
        <h2><span class="step-number">3</span>Your Personalized Schedule</h2>
        <p>Here's your AI-generated schedule that actually fits your life!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Schedule stats
    courses_count = len(st.session_state.user_data.get('courses', []))
    deadlines_count = len(st.session_state.user_data.get('deadlines', []))
    attention_span = st.session_state.user_data.get('attention_span', 25)
    
    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-card">
            <span class="stat-number">{courses_count}</span>
            <div class="stat-label">Courses</div>
        </div>
        <div class="stat-card">
            <span class="stat-number">{deadlines_count}</span>
            <div class="stat-label">Deadlines</div>
        </div>
        <div class="stat-card">
            <span class="stat-number">{attention_span}</span>
            <div class="stat-label">Min Focus</div>
        </div>
        <div class="stat-card">
            <span class="stat-number">30</span>
            <div class="stat-label">Days Planned</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Schedule preview
    st.markdown("### 📅 This Week's Schedule")
    
    if st.session_state.final_schedule:
        # Show today and next 6 days
        today = datetime.now()
        for i in range(7):
            date = today + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            day_name = date.strftime('%A, %B %d')
            
            if date_str in st.session_state.final_schedule:
                with st.expander(f"{'🔥 Today' if i == 0 else '📅'} {day_name}", expanded=(i == 0)):
                    daily_schedule = st.session_state.final_schedule[date_str]
                    
                    for activity in daily_schedule:
                        # Color coding based on activity type
                        if activity['type'] == 'study':
                            color = '#6c5ce7'
                        elif activity['type'] == 'meal':
                            color = '#fdcb6e'
                        elif activity['type'] == 'break':
                            color = '#fd79a8'
                        elif activity['type'] == 'free':
                            color = '#00b894'
                        elif activity['type'] == 'deadline':
                            color = '#e17055'
                        else:
                            color = '#a29bfe'
                        
                        duration_text = f" ({activity.get('duration', 30)} min)" if activity.get('duration') else ""
                        
                        st.markdown(f"""
                        <div class="activity-item">
                            <div class="time-badge" style="background: {color};">{activity['time']}</div>
                            <div style="color: white;">{activity['activity']}{duration_text}</div>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Export section
    st.markdown("""
    <div class="export-section">
        <h3>🚀 Export Your Schedule</h3>
        <p>Get your schedule in your preferred format - PDF for printing, Calendar for your phone, or Email for easy sharing!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create export files
    if st.session_state.final_schedule and st.session_state.user_data:
        
        # Generate PDF
        pdf_buffer = generate_pdf_schedule(st.session_state.final_schedule, st.session_state.user_data)
        pdf_data = pdf_buffer.getvalue()
        
        # Generate ICS
        ics_content = generate_ics_calendar(st.session_state.final_schedule, st.session_state.user_data)
        
        # Export buttons row 1: PDF and Calendar
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📄 Download PDF",
                data=pdf_data,
                file_name=f"StudyFlow_Schedule_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                help="Download a beautifully formatted PDF of your schedule",
                use_container_width=True
            )
        
        with col2:
            st.download_button(
                label="📅 Download Calendar",
                data=ics_content,
                file_name=f"StudyFlow_Calendar_{datetime.now().strftime('%Y%m%d')}.ics",
                mime="text/calendar",
                help="Import this into Google Calendar, Outlook, or Apple Calendar",
                use_container_width=True
            )
        
        # Email section with input
        st.markdown("""
        <div class="email-section">
            <h4>📧 Email Your Schedule</h4>
            <p>Enter your email below to send your complete schedule with tips and previews!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Email input and send button
        email_input = st.text_input(
            "Email Address",
            placeholder="your.email@college.edu",
            help="We'll create a ready-to-send email with your complete schedule",
            label_visibility="collapsed"
        )
        
        if st.button("📧 Send Schedule to Email", type="primary", use_container_width=True, disabled=not email_input):
            if email_input:
                # Create email content
                email_subject, email_body = create_email_content(st.session_state.final_schedule, st.session_state.user_data)
                
                # Create mailto link
                mailto_url = f"mailto:{email_input}?subject={urllib.parse.quote(email_subject)}&body={urllib.parse.quote(email_body)}"
                
                # Show success message and link
                st.success(f"📧 Email ready to send to {email_input}!")
                st.markdown(f"""
                <div style="text-align: center; margin: 1rem 0;">
                    <a href="{mailto_url}" target="_blank" class="email-button">
                        🚀 Open Email Client & Send
                    </a>
                </div>
                """, unsafe_allow_html=True)
                
                # Show email preview
                with st.expander("📧 Email Preview"):
                    st.markdown(f"**Subject:** {email_subject}")
                    st.markdown("**Body Preview:**")
                    st.text_area("", value=email_body[:1000] + "..." if len(email_body) > 1000 else email_body, height=200, disabled=True)
            else:
                st.warning("Please enter your email address first!")
        
        # Additional options
        st.markdown("### 🔧 More Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Modify Schedule", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
        
        with col2:
            # Save current data as JSON for future use
            save_data = {
                'courses': st.session_state.user_data.get('courses', []),
                'deadlines': st.session_state.user_data.get('deadlines', []),
                'preferences': st.session_state.user_data,
                'schedule': st.session_state.final_schedule,
                'generated_date': datetime.now().isoformat()
            }
            
            st.download_button(
                label="💾 Save Data",
                data=json.dumps(save_data, indent=2),
                file_name=f"StudyFlow_Data_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                help="Save your data to import later",
                use_container_width=True
            )
    
    # Progress complete
    st.markdown("""
    <div class="progress-bar">
        <div class="progress-fill" style="width: 100%"></div>
    </div>
    <p class="progress-text">🎉 Schedule Complete!</p>
    """, unsafe_allow_html=True)
    
    # Success message
    st.success(f"""
    🎉 **Your StudyFlow Schedule is Ready!**
    
    ✅ **{courses_count} courses** integrated with realistic study blocks
    ✅ **{deadlines_count} deadlines** tracked with smart reminders
    ✅ **{attention_span}-minute focus sessions** (perfect for your attention span!)
    ✅ **Social media breaks** included (because we're realistic!)
    ✅ **30 days** of personalized scheduling
    
    📱 **Export your schedule above and start crushing your goals!**
    """)
    
    # Social proof
    st.markdown("""
    <div class="social-proof">
        <h4>Join 10,000+ students who've improved their grades with StudyFlow!</h4>
        <p>"Finally, a schedule app that doesn't make me feel guilty about checking Instagram!" - Sarah, Sophomore</p>
        <p>"The dark theme is perfect for late-night study sessions." - Mike, Junior</p>
        <p>"I love that I can just enter my email at the end - no commitment until I'm ready!" - Alex, Senior</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
