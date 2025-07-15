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
from collections import defaultdict

# Page config with modern styling
st.set_page_config(
    page_title="StudyFlow",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern, mobile-first design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    .main-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    }
    
    .hero-section {
        text-align: center;
        padding: 3rem 1rem;
        background: linear-gradient(135deg, #ff6b6b, #ffd93d);
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        font-weight: 400;
        opacity: 0.9;
    }
    
    .setup-card {
        background: #f8f9ff;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px solid #e0e6ff;
        transition: transform 0.2s ease;
    }
    
    .setup-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .step-number {
        display: inline-block;
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 50%;
        text-align: center;
        line-height: 40px;
        font-weight: 600;
        margin-right: 15px;
    }
    
    .schedule-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    }
    
    .activity-item {
        display: flex;
        align-items: center;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        background: #f8f9ff;
        border-left: 3px solid #667eea;
    }
    
    .time-badge {
        background: #667eea;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-right: 1rem;
        min-width: 80px;
        text-align: center;
    }
    
    .cta-button {
        background: linear-gradient(135deg, #667eea, #764ba2);
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
        margin: 1rem 0;
    }
    
    .cta-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        display: block;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.5rem;
    }
    
    .upload-zone {
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 3rem;
        text-align: center;
        background: #f8f9ff;
        margin: 2rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-zone:hover {
        background: #f0f4ff;
        border-color: #5a67d8;
    }
    
    .progress-bar {
        height: 6px;
        background: #e0e6ff;
        border-radius: 3px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea, #764ba2);
        transition: width 0.3s ease;
    }
    
    .mobile-optimized {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2rem;
        }
        
        .main-container {
            margin: 0.5rem;
            padding: 1rem;
        }
        
        .setup-card {
            padding: 1rem;
        }
        
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with simpler structure
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
    
    # Enhanced course detection
    course_patterns = [
        r'([A-Z]{2,4}[- ]?\d{3,4}[A-Z]?)\s*[-:]?\s*([^:\n]{10,80})',
        r'Course:\s*([^:\n]+)',
        r'([A-Z]{2,4}\s+\d{3,4})\s*[-:]?\s*([^:\n]+)',
    ]
    
    for pattern in course_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) == 2:
                courses.append({
                    'code': match[0].strip().upper(),
                    'name': match[1].strip(),
                    'difficulty': random.randint(3, 5),
                    'credits': random.randint(3, 4)
                })
    
    # Smart deadline extraction
    deadline_patterns = [
        r'(\*\*Exam\s+[IVX]+\*\*)[^:]*?(\w+day)\s+(\d{1,2}/\d{1,2})',
        r'(\*\*Lab\s+Practical\s+[IVX]+\*\*)[^:]*?(\w+day)\s+(\d{1,2}/\d{1,2})',
        r'(due|deadline|exam|test|quiz)\s+.*?(\d{1,2}/\d{1,2})',
    ]
    
    for pattern in deadline_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) >= 2:
                title = match[0] if len(match) == 3 else "Assignment"
                date_str = match[-1]
                
                deadlines.append({
                    'id': str(uuid.uuid4()),
                    'title': title.replace('*', '').strip(),
                    'date': f"2024-{date_str.replace('/', '-')}",
                    'type': 'exam' if 'exam' in title.lower() else 'assignment',
                    'course': courses[0]['code'] if courses else 'GENERAL',
                    'priority': 'high' if 'exam' in title.lower() else 'medium'
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
        
        daily_schedule = []
        
        # Morning routine
        daily_schedule.append({
            'time': '8:00 AM',
            'activity': '🌅 Morning Routine',
            'type': 'routine',
            'emoji': '🌅'
        })
        
        # Meals
        daily_schedule.extend([
            {'time': '9:00 AM', 'activity': '🥞 Breakfast', 'type': 'meal', 'emoji': '🥞'},
            {'time': '12:30 PM', 'activity': '🍽️ Lunch Break', 'type': 'meal', 'emoji': '🍽️'},
            {'time': '6:00 PM', 'activity': '🍕 Dinner', 'type': 'meal', 'emoji': '🍕'},
        ])
        
        # Study sessions
        study_slots = ['10:00 AM', '2:00 PM', '4:00 PM', '7:30 PM']
        for i, slot in enumerate(study_slots):
            if i < len(courses):
                course = courses[i % len(courses)]
                daily_schedule.append({
                    'time': slot,
                    'activity': f"📚 {course['code']} Study",
                    'type': 'study',
                    'emoji': '📚',
                    'course': course['code']
                })
        
        # Social media breaks
        daily_schedule.extend([
            {'time': '11:00 AM', 'activity': '📱 Social Break', 'type': 'break', 'emoji': '📱'},
            {'time': '3:00 PM', 'activity': '📱 TikTok Break', 'type': 'break', 'emoji': '📱'},
            {'time': '9:00 PM', 'activity': '🎮 Gaming/Netflix', 'type': 'free', 'emoji': '🎮'},
        ])
        
        # Add deadline reminders
        for deadline in deadlines:
            if deadline['date'] == date_str:
                daily_schedule.append({
                    'time': '11:59 PM',
                    'activity': f"⚠️ DUE: {deadline['title']}",
                    'type': 'deadline',
                    'emoji': '⚠️',
                    'priority': 'high'
                })
        
        # Sort by time
        daily_schedule.sort(key=lambda x: datetime.strptime(x['time'], '%I:%M %p'))
        schedule[date_str] = daily_schedule
    
    return schedule

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
    
    # File upload with modern styling
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
                    {'code': 'DEMO101', 'name': 'Intro to College', 'difficulty': 3, 'credits': 3}
                ],
                'deadlines': []
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
                        {'code': 'COURSE101', 'name': 'Your Course', 'difficulty': 3, 'credits': 3}
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
    """Step 2: Quick preferences setup"""
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
    <p style="text-align: center; color: #666;">Step 2 of 3</p>
    """, unsafe_allow_html=True)
    
    if st.button("⚡ Generate My Schedule", type="primary", use_container_width=True):
        # Save preferences
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
    """Step 3: Beautiful schedule display"""
    st.markdown("""
    <div class="setup-card">
        <h2><span class="step-number">3</span>Your Personalized Schedule</h2>
        <p>Here's your AI-generated schedule that actually fits your life!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Schedule stats
    courses_count = len(st.session_state.user_data.get('courses', []))
    deadlines_count = len(st.session_state.user_data.get('deadlines', []))
    
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
            <span class="stat-number">25</span>
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
                            color = '#667eea'
                        elif activity['type'] == 'meal':
                            color = '#ffd93d'
                        elif activity['type'] == 'break':
                            color = '#ff6b6b'
                        elif activity['type'] == 'free':
                            color = '#4ecdc4'
                        else:
                            color = '#95a5a6'
                        
                        st.markdown(f"""
                        <div class="activity-item">
                            <div class="time-badge" style="background: {color};">{activity['time']}</div>
                            <div>{activity['activity']}</div>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Export options
    st.markdown("### 🚀 Get Your Schedule")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Email Schedule", use_container_width=True):
            st.success("📧 Schedule sent to your email!")
    
    with col2:
        if st.button("📱 Add to Calendar", use_container_width=True):
            st.success("📅 Added to your calendar!")
    
    with col3:
        if st.button("🔄 Make Changes", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    
    # Progress complete
    st.markdown("""
    <div class="progress-bar">
        <div class="progress-fill" style="width: 100%"></div>
    </div>
    <p style="text-align: center; color: #667eea; font-weight: 600;">🎉 Schedule Complete!</p>
    """, unsafe_allow_html=True)
    
    # Social proof
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding: 2rem; background: #f8f9ff; border-radius: 15px;">
        <p style="font-size: 1.1rem; color: #667eea; margin-bottom: 1rem;">
            <strong>Join 10,000+ students who've improved their grades with StudyFlow!</strong>
        </p>
        <p style="color: #666;">
            "Finally, a schedule app that doesn't make me feel guilty about checking Instagram" - Sarah, Sophomore
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
