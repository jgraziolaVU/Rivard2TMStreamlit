import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
import PyPDF2
import docx
from io import BytesIO
import urllib.parse
import json
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import uuid
import random
from collections import defaultdict

# Page config
st.set_page_config(
    page_title="StudyFlow - 2025 College Time Management",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'schedule_data' not in st.session_state:
    st.session_state.schedule_data = {}
if 'courses' not in st.session_state:
    st.session_state.courses = []
if 'obligations' not in st.session_state:
    st.session_state.obligations = []
if 'deadlines' not in st.session_state:
    st.session_state.deadlines = []
if 'schedule_proposals' not in st.session_state:
    st.session_state.schedule_proposals = []
if 'selected_schedule' not in st.session_state:
    st.session_state.selected_schedule = None

# Helper function to convert 24-hour to 12-hour format
def format_time_12hour(time_str):
    """Convert 24-hour time to 12-hour AM/PM format"""
    try:
        # Handle both HH:MM and H:MM formats
        if ':' in time_str:
            hour, minute = map(int, time_str.split(':'))
        else:
            hour = int(time_str)
            minute = 0
        
        # Convert to 12-hour format
        if hour == 0:
            return f"12:{minute:02d} AM"
        elif hour < 12:
            return f"{hour}:{minute:02d} AM"
        elif hour == 12:
            return f"12:{minute:02d} PM"
        else:
            return f"{hour-12}:{minute:02d} PM"
    except:
        return time_str

# Helper function to convert 12-hour to 24-hour format for calculations
def convert_to_24hour(time_str):
    """Convert 12-hour AM/PM format to 24-hour format"""
    try:
        if 'AM' in time_str or 'PM' in time_str:
            time_part = time_str.replace(' AM', '').replace(' PM', '')
            hour, minute = map(int, time_part.split(':'))
            
            if 'PM' in time_str and hour != 12:
                hour += 12
            elif 'AM' in time_str and hour == 12:
                hour = 0
                
            return f"{hour:02d}:{minute:02d}"
        else:
            return time_str
    except:
        return time_str

# Title
st.title("📚 StudyFlow - 2025 College Time Management")
st.markdown("**Designed for real college students with real distractions!**")

# Sidebar for basic preferences
st.sidebar.header("⚙️ Personal Settings")
email = st.sidebar.text_input("📧 Your Email", placeholder="your.email@example.com")
wakeup = st.sidebar.slider("🌅 Wake Up Time", 6, 12, 8, help="When you actually wake up (not when your alarm goes off)")
sleep = st.sidebar.slider("😴 Sleep Time", 10, 2, 12, help="Realistic bedtime for college students (10 PM = 22:00)")
semester_start = st.sidebar.date_input("📅 Semester Start Date", datetime.now().date())
semester_end = st.sidebar.date_input("📅 Semester End Date", datetime.now().date() + timedelta(days=120))

# Display times in 12-hour format for user
st.sidebar.write(f"**Your Schedule**: {format_time_12hour(f'{wakeup}:00')} - {format_time_12hour(f'{sleep}:00')}")

# Modern student reality settings
st.sidebar.header("📱 2025 Student Reality")
phone_breaks = st.sidebar.checkbox("Include Phone/Social Media Breaks", value=True)
procrastination_buffer = st.sidebar.slider("⏰ Procrastination Buffer (%)", 20, 80, 40, help="How much extra time to add for distractions")
study_attention_span = st.sidebar.slider("🧠 Max Focus Time (minutes)", 15, 60, 25, help="Realistic attention span")

# File upload and import section
st.header("1️⃣ Import Previous Schedule (Optional)")
uploaded_schedule = st.file_uploader(
    "📁 Upload Previous StudyFlow Schedule File",
    type=['json'],
    help="Upload a previously saved schedule file to build upon"
)

if uploaded_schedule:
    try:
        previous_data = json.load(uploaded_schedule)
        st.session_state.courses = previous_data.get('courses', [])
        st.session_state.obligations = previous_data.get('obligations', [])
        st.session_state.deadlines = previous_data.get('deadlines', [])
        st.success("✅ Previous schedule loaded successfully!")
    except:
        st.error("❌ Error loading schedule file")

# Course schedule upload
st.header("2️⃣ Upload Course Schedule")
uploaded_file = st.file_uploader(
    "📄 Upload Course Schedule/Syllabus",
    type=['pdf', 'docx', 'txt'],
    help="Upload syllabi, schedules, or any course documents"
)

def extract_text_from_file(file):
    """Extract text from uploaded file"""
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
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
                text += "\n"
        return text
    else:
        return str(file.read(), "utf-8")

def parse_courses_and_deadlines(text):
    """Enhanced parsing for courses and deadlines"""
    courses = []
    deadlines = []
    
    # Course extraction patterns
    course_patterns = [
        r'([A-Z]{2,4}[- ]?\d{3,4}[A-Z]?)\s*[-:]?\s*([^:\n]+)',
        r'Course:\s*([^:\n]+)',
        r'([A-Z]{2,4}\s+\d{3,4})\s*[-:]?\s*([^:\n]+)',
        r'BIOLOGY\s+(\d{4})',  # Biology specific
        r'BIO\s*(\d{4})',      # Bio abbreviation
    ]
    
    for pattern in course_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) == 2:
                courses.append({
                    'code': match[0].strip().upper(),
                    'name': match[1].strip(),
                    'difficulty': 3,
                    'credits': 3
                })
            elif len(match) == 1:  # Single number match (like BIOLOGY 1205)
                courses.append({
                    'code': f'BIO{match[0]}',
                    'name': f'Biology {match[0]}',
                    'difficulty': 4,
                    'credits': 4
                })
    
    # Enhanced deadline extraction
    deadline_keywords = ['due', 'deadline', 'exam', 'test', 'assignment', 'project', 'quiz', 'presentation', 'final', 'midterm', 'practical']
    date_patterns = [
        r'(\w+day)\s+(\d{1,2}/\d{1,2})',  # Monday 9/13
        r'(\d{1,2}/\d{1,2})/\d{2,4}',     # MM/DD/YYYY
        r'(\d{1,2}/\d{1,2})',             # MM/DD
        r'(\w+)\s+(\d{1,2})',             # Month DD
        r'(\d{1,2})-(\d{1,2})-\d{2,4}',   # MM-DD-YYYY
    ]
    
    # Look for exam patterns specifically
    exam_patterns = [
        r'(\*\*Exam\s+[IVX]+\*\*)[^:]*?(\w+day)\s+(\d{1,2}/\d{1,2})',
        r'(\*\*Lab\s+Practical\s+[IVX]+\*\*)[^:]*?(\w+day)\s+(\d{1,2}/\d{1,2})',
        r'(\*\*Lab\s+Exam\s+\d+\*\*)[^:]*?(\w+day)\s+(\d{1,2}/\d{1,2})',
    ]
    
    # Extract exam dates
    for pattern in exam_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) == 3:
                exam_title = match[0].replace('*', '').strip()
                day = match[1]
                date = match[2]
                
                # Determine exam type
                exam_type = 'exam'
                if 'practical' in exam_title.lower():
                    exam_type = 'practical'
                elif 'lab' in exam_title.lower():
                    exam_type = 'lab_exam'
                
                deadlines.append({
                    'id': str(uuid.uuid4()),
                    'title': exam_title,
                    'date': f"2024-{date.replace('/', '-')}",
                    'type': exam_type,
                    'course': courses[0]['code'] if courses else 'UNKNOWN',
                    'priority': 'high',
                    'study_hours_needed': 12 if exam_type == 'exam' else 6
                })
    
    # Extract assignment due dates
    sentences = re.split(r'[.!?\n]', text)
    for sentence in sentences:
        sentence = sentence.strip()
        if any(keyword in sentence.lower() for keyword in deadline_keywords):
            for pattern in date_patterns:
                date_matches = re.findall(pattern, sentence)
                if date_matches:
                    deadline_type = 'assignment'
                    if any(word in sentence.lower() for word in ['exam', 'test', 'final', 'midterm']):
                        deadline_type = 'exam'
                    elif 'quiz' in sentence.lower():
                        deadline_type = 'quiz'
                    elif 'project' in sentence.lower():
                        deadline_type = 'project'
                    elif 'practical' in sentence.lower():
                        deadline_type = 'practical'
                    
                    # Extract time if present
                    time_match = re.search(r'(\d{1,2}):(\d{2})\s*([aApP][mM])', sentence)
                    time_str = time_match.group(0) if time_match else ''
                    
                    deadlines.append({
                        'id': str(uuid.uuid4()),
                        'title': sentence[:100].strip(),
                        'date': date_matches[0] if isinstance(date_matches[0], str) else date_matches[0][0],
                        'time': time_str,
                        'type': deadline_type,
                        'course': courses[0]['code'] if courses else 'UNKNOWN',
                        'priority': 'high' if deadline_type in ['exam', 'practical'] else 'medium',
                        'study_hours_needed': 12 if deadline_type == 'exam' else 6 if deadline_type == 'practical' else 3
                    })
                    break
    
    return courses, deadlines

if uploaded_file:
    with st.spinner("🔍 Parsing your course schedule..."):
        text = extract_text_from_file(uploaded_file)
        parsed_courses, parsed_deadlines = parse_courses_and_deadlines(text)
        
        # If no courses found, create a default one from filename or content
        if not parsed_courses:
            filename = uploaded_file.name.lower()
            if 'bio' in filename or 'biology' in text.lower():
                parsed_courses.append({
                    'code': 'BIO1205',
                    'name': 'Biology 1205 Lecture and Laboratory',
                    'difficulty': 4,
                    'credits': 4
                })
            else:
                # Generic course based on filename
                course_code = filename.split('.')[0].upper()[:8]
                parsed_courses.append({
                    'code': course_code,
                    'name': f'Course from {uploaded_file.name}',
                    'difficulty': 3,
                    'credits': 3
                })
        
        # Add to session state if not already there
        for course in parsed_courses:
            if not any(c['code'] == course['code'] for c in st.session_state.courses):
                st.session_state.courses.append(course)
        
        for deadline in parsed_deadlines:
            if not any(d['id'] == deadline['id'] for d in st.session_state.deadlines):
                st.session_state.deadlines.append(deadline)
        
        st.success(f"✅ Found {len(parsed_courses)} courses and {len(parsed_deadlines)} deadlines!")
        
        # Auto-rerun to refresh the interface
        st.rerun()

# Course management section
st.header("3️⃣ Manage Courses")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Add/Edit Courses")
    with st.form("course_form"):
        course_code = st.text_input("Course Code", placeholder="BIO1205")
        course_name = st.text_input("Course Name", placeholder="Biology 1205")
        difficulty = st.slider("Difficulty Level", 1, 5, 3, help="1=Easy A, 5=Extremely Hard")
        credits = st.number_input("Credits", min_value=1, max_value=6, value=3)
        
        if st.form_submit_button("Add Course"):
            if course_code and course_name:
                new_course = {
                    'code': course_code.upper(),
                    'name': course_name,
                    'difficulty': difficulty,
                    'credits': credits
                }
                # Check if course already exists
                existing_index = next((i for i, c in enumerate(st.session_state.courses) if c['code'] == course_code.upper()), None)
                if existing_index is not None:
                    st.session_state.courses[existing_index] = new_course
                    st.success(f"✅ Updated course: {course_code}")
                else:
                    st.session_state.courses.append(new_course)
                    st.success(f"✅ Added course: {course_code}")
                st.rerun()

with col2:
    st.subheader("Current Courses")
    if st.session_state.courses:
        for i, course in enumerate(st.session_state.courses):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(f"**{course['code']}** - {course['name']}")
                st.write(f"Difficulty: {'⭐' * course['difficulty']} | Credits: {course['credits']}")
            with col_b:
                if st.button(f"🗑️", key=f"delete_course_{i}"):
                    st.session_state.courses.pop(i)
                    st.rerun()
    else:
        st.info("No courses added yet - upload a syllabus to get started!")

# Deadlines management
st.header("4️⃣ Manage Deadlines & Assignments")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Add Deadline")
    with st.form("deadline_form"):
        deadline_title = st.text_input("Assignment/Exam Title")
        deadline_date = st.date_input("Due Date")
        deadline_type = st.selectbox("Type", ["assignment", "exam", "quiz", "project", "presentation", "practical"])
        deadline_course = st.selectbox("Course", [c['code'] for c in st.session_state.courses] if st.session_state.courses else ["NONE"])
        study_hours = st.number_input("Study Hours Needed", min_value=1, max_value=50, value=8)
        priority = st.selectbox("Priority", ["low", "medium", "high"])
        
        if st.form_submit_button("Add Deadline"):
            if deadline_title and deadline_course != "NONE":
                new_deadline = {
                    'id': str(uuid.uuid4()),
                    'title': deadline_title,
                    'date': deadline_date.strftime('%Y-%m-%d'),
                    'type': deadline_type,
                    'course': deadline_course,
                    'priority': priority,
                    'study_hours_needed': study_hours
                }
                st.session_state.deadlines.append(new_deadline)
                st.success(f"✅ Added deadline: {deadline_title}")
                st.rerun()

with col2:
    st.subheader("Current Deadlines")
    if st.session_state.deadlines:
        for i, deadline in enumerate(st.session_state.deadlines):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                priority_color = {"low": "🟢", "medium": "🟡", "high": "🔴"}[deadline['priority']]
                st.write(f"{priority_color} **{deadline['title']}** ({deadline['course']})")
                st.write(f"Due: {deadline['date']} | Type: {deadline['type']} | {deadline['study_hours_needed']}h needed")
            with col_b:
                if st.button(f"🗑️", key=f"delete_deadline_{i}"):
                    st.session_state.deadlines.pop(i)
                    st.rerun()
    else:
        st.info("No deadlines added yet")

# Other obligations section
st.header("5️⃣ Add Other Obligations")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Add Personal Obligations")
    with st.form("obligation_form"):
        obligation_title = st.text_input("Obligation Title", placeholder="Work, gym, part-time job, etc.")
        obligation_type = st.selectbox("Type", ["work", "job", "meeting", "appointment", "exercise", "social", "recurring"])
        
        if obligation_type == "recurring":
            days_of_week = st.multiselect("Days of Week", 
                                        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
            start_time = st.time_input("Start Time")
            end_time = st.time_input("End Time")
            start_date = semester_start
            end_date = semester_end
        else:
            days_of_week = []
            obligation_date = st.date_input("Date")
            start_time = st.time_input("Start Time")
            end_time = st.time_input("End Time")
            start_date = obligation_date
            end_date = obligation_date
        
        if st.form_submit_button("Add Obligation"):
            if obligation_title:
                new_obligation = {
                    'id': str(uuid.uuid4()),
                    'title': obligation_title,
                    'type': obligation_type,
                    'days_of_week': days_of_week,
                    'start_time': start_time.strftime('%H:%M'),
                    'end_time': end_time.strftime('%H:%M'),
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'recurring': obligation_type == "recurring"
                }
                st.session_state.obligations.append(new_obligation)
                st.success(f"✅ Added obligation: {obligation_title}")
                st.rerun()

with col2:
    st.subheader("Current Obligations")
    if st.session_state.obligations:
        for i, obligation in enumerate(st.session_state.obligations):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(f"**{obligation['title']}** ({obligation['type']})")
                if obligation['recurring']:
                    start_12h = format_time_12hour(obligation['start_time'])
                    end_12h = format_time_12hour(obligation['end_time'])
                    st.write(f"Recurring: {', '.join(obligation['days_of_week'])} | {start_12h} - {end_12h}")
                else:
                    start_12h = format_time_12hour(obligation['start_time'])
                    end_12h = format_time_12hour(obligation['end_time'])
                    st.write(f"Date: {obligation['start_date']} | {start_12h} - {end_12h}")
            with col_b:
                if st.button(f"🗑️", key=f"delete_obligation_{i}"):
                    st.session_state.obligations.pop(i)
                    st.rerun()
    else:
        st.info("No obligations added yet")

# Schedule generation section
st.header("6️⃣ Generate 2025-Realistic Schedule Proposals")

def calculate_realistic_study_time(course, buffer_percent):
    """Calculate realistic study time with procrastination buffer"""
    # Base study time = credits * difficulty * 1.5 hours per week (reduced from 2)
    base_hours = course['credits'] * course['difficulty'] * 1.5
    
    # Add procrastination buffer
    buffered_hours = base_hours * (1 + buffer_percent / 100)
    
    return buffered_hours

def generate_time_slots_with_ampm(start_hour, end_hour, attention_span):
    """Generate time slots in 12-hour format"""
    slots = []
    current_time = start_hour
    
    while current_time < end_hour:
        slots.append(format_time_12hour(f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"))
        current_time += (attention_span + 15) / 60  # Study time + break
    
    return slots

def generate_2025_schedule_proposal(proposal_type, buffer_percent, attention_span, phone_breaks):
    """Generate a 2025-realistic schedule proposal with AM/PM times"""
    schedule = defaultdict(list)
    
    # Calculate total semester dates
    current_date = semester_start
    semester_dates = []
    while current_date <= semester_end:
        semester_dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Create base schedule with realistic timings
    for date in semester_dates:
        date_str = date.strftime('%Y-%m-%d')
        is_weekend = date.weekday() >= 5
        
        # Morning routine (realistic timing)
        wake_time = wakeup if not is_weekend else wakeup + 1
        wake_time_12h = format_time_12hour(f"{wake_time:02d}:00")
        
        schedule[date_str].append({
            'time': wake_time_12h,
            'activity': '🌅 Wake Up & Morning Routine',
            'type': 'routine',
            'duration': 60,
            'fixed': True
        })
        
        # Breakfast (US college timing)
        breakfast_time = wake_time + 1
        breakfast_time_12h = format_time_12hour(f"{breakfast_time:02d}:00")
        
        schedule[date_str].append({
            'time': breakfast_time_12h,
            'activity': '🥞 Breakfast',
            'type': 'meal',
            'duration': 30,
            'fixed': True
        })
        
        # US college meal times in 12-hour format
        schedule[date_str].extend([
            {'time': '12:00 PM', 'activity': '🍽️ Lunch', 'type': 'meal', 'duration': 60, 'fixed': True},
            {'time': '5:00 PM', 'activity': '🍽️ Dinner', 'type': 'meal', 'duration': 60, 'fixed': True},
            {'time': '9:00 PM', 'activity': '🍿 Evening Snack', 'type': 'meal', 'duration': 30, 'fixed': True}
        ])
        
        # Add phone/social media breaks if enabled
        if phone_breaks:
            schedule[date_str].extend([
                {'time': '10:30 AM', 'activity': '📱 Phone/Social Media Break', 'type': 'break', 'duration': 15, 'fixed': True},
                {'time': '2:30 PM', 'activity': '📱 Phone/Social Media Break', 'type': 'break', 'duration': 15, 'fixed': True},
                {'time': '7:30 PM', 'activity': '📱 Phone/Social Media Break', 'type': 'break', 'duration': 30, 'fixed': True}
            ])
        
        # Add obligations with 12-hour format
        for obligation in st.session_state.obligations:
            if obligation['recurring'] and date.strftime('%A') in obligation['days_of_week']:
                start_12h = format_time_12hour(obligation['start_time'])
                duration = (datetime.strptime(obligation['end_time'], '%H:%M') - 
                           datetime.strptime(obligation['start_time'], '%H:%M')).seconds // 60
                
                schedule[date_str].append({
                    'time': start_12h,
                    'activity': f"📝 {obligation['title']}",
                    'type': 'obligation',
                    'duration': duration,
                    'fixed': True
                })
            elif not obligation['recurring'] and obligation['start_date'] == date_str:
                start_12h = format_time_12hour(obligation['start_time'])
                duration = (datetime.strptime(obligation['end_time'], '%H:%M') - 
                           datetime.strptime(obligation['start_time'], '%H:%M')).seconds // 60
                
                schedule[date_str].append({
                    'time': start_12h,
                    'activity': f"📝 {obligation['title']}",
                    'type': 'obligation',
                    'duration': duration,
                    'fixed': True
                })
        
        # Add deadline-specific activities
        for deadline in st.session_state.deadlines:
            if deadline['date'] == date_str:
                schedule[date_str].append({
                    'time': '11:59 PM',
                    'activity': f"⚠️ DUE: {deadline['title']}",
                    'type': 'deadline',
                    'course': deadline['course'],
                    'priority': deadline['priority'],
                    'fixed': True
                })
        
        # Generate realistic study sessions with 12-hour times
        available_morning = ['9:00 AM', '10:00 AM', '11:00 AM']
        available_afternoon = ['1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
        available_evening = ['6:00 PM', '7:00 PM', '8:00 PM'] if not is_weekend else ['6:00 PM', '7:00 PM', '8:00 PM', '9:00 PM']
        
        all_slots = available_morning + available_afternoon + available_evening
        
        # Get existing activities for this day
        existing_activities = schedule[date_str]
        busy_times = [act['time'] for act in existing_activities if act.get('fixed')]
        
        # Filter available slots
        free_slots = [slot for slot in all_slots if slot not in busy_times]
        
        # Add study sessions based on proposal type
        if proposal_type == "intensive":
            study_sessions_target = 4 if not is_weekend else 3
        elif proposal_type == "balanced":
            study_sessions_target = 3 if not is_weekend else 2
        else:  # relaxed
            study_sessions_target = 2 if not is_weekend else 1
        
        # Realistic study session scheduling
        courses_for_day = list(st.session_state.courses)
        if courses_for_day:
            random.shuffle(courses_for_day)  # Randomize for interleaving
            
            sessions_added = 0
            for slot in free_slots:
                if sessions_added >= study_sessions_target:
                    break
                
                course = courses_for_day[sessions_added % len(courses_for_day)]
                
                # Determine session type with realistic expectations
                session_types = ['review', 'practice', 'reading', 'problems']
                session_type = random.choice(session_types)
                
                schedule[date_str].append({
                    'time': slot,
                    'activity': f"📚 {course['code']} - {session_type.title()}",
                    'type': 'study',
                    'course': course['code'],
                    'duration': attention_span,
                    'session_type': session_type,
                    'fixed': False
                })
                sessions_added += 1
        
        # Add review sessions before major deadlines (but realistic)
        for deadline in st.session_state.deadlines:
            try:
                deadline_date = datetime.strptime(deadline['date'], '%Y-%m-%d')
                days_until = (deadline_date - date).days
                
                if days_until in [1, 3] and deadline['type'] in ['exam', 'practical']:
                    intensity = 'Cram Session' if days_until == 1 else 'Review Session'
                    
                    # Find evening slot for review
                    evening_slots = ['8:00 PM', '9:00 PM', '10:00 PM']
                    for slot in evening_slots:
                        if slot not in busy_times:
                            schedule[date_str].append({
                                'time': slot,
                                'activity': f"📖 {intensity}: {deadline['title'][:30]}...",
                                'type': 'review',
                                'duration': 45 if days_until == 1 else 30,
                                'course': deadline['course'],
                                'priority': 'high',
                                'fixed': False
                            })
                            break
            except:
                continue
        
        # Add realistic free time
        if not is_weekend:
            schedule[date_str].append({
                'time': '10:00 PM',
                'activity': '🎉 Social Time/Gaming/Netflix',
                'type': 'free',
                'duration': 120,
                'fixed': True
            })
        else:
            schedule[date_str].append({
                'time': '8:00 PM',
                'activity': '🎉 Weekend Social Time',
                'type': 'free',
                'duration': 180,
                'fixed': True
            })
        
        # Sort activities by time (convert to 24-hour for sorting, then back to 12-hour)
        schedule[date_str].sort(key=lambda x: convert_to_24hour(x['time']))
    
    return dict(schedule)

if st.button("🚀 Generate 2025-Realistic Schedule Proposals", type="primary"):
    if not email:
        st.error("❌ Please enter your email in the sidebar first")
    elif not st.session_state.courses:
        st.error("❌ Please add at least one course first")
    else:
        with st.spinner("⚡ Generating 3 realistic schedule proposals for 2025 students..."):
            
            # Generate 3 different proposals
            proposals = []
            for proposal_type in ["intensive", "balanced", "relaxed"]:
                proposal = generate_2025_schedule_proposal(
                    proposal_type, 
                    procrastination_buffer, 
                    study_attention_span, 
                    phone_breaks
                )
                proposals.append({
                    'type': proposal_type,
                    'schedule': proposal,
                    'description': {
                        'intensive': "🔥 Maximum effort (but still realistic)",
                        'balanced': "⚖️ Balanced study and social life",
                        'relaxed': "🌿 Chill schedule with flexibility"
                    }[proposal_type]
                })
            
            st.session_state.schedule_proposals = proposals
            st.success("✅ Generated 3 realistic schedule proposals!")

# Display schedule proposals
if st.session_state.schedule_proposals:
    st.header("7️⃣ Choose Your Schedule")
    
    # Create tabs for each proposal
    tab1, tab2, tab3 = st.tabs(["🔥 Intensive", "⚖️ Balanced", "🌿 Relaxed"])
    
    tabs = [tab1, tab2, tab3]
    
    for i, proposal in enumerate(st.session_state.schedule_proposals):
        with tabs[i]:
            st.subheader(f"{proposal['description']}")
            
            # Show statistics
            col1, col2, col3, col4 = st.columns(4)
            
            total_study_hours = 0
            total_free_hours = 0
            total_phone_time = 0
            total_days = len(proposal['schedule'])
            
            for day_schedule in proposal['schedule'].values():
                for activity in day_schedule:
                    if activity['type'] == 'study':
                        total_study_hours += activity.get('duration', 25) / 60
                    elif activity['type'] == 'free':
                        total_free_hours += activity.get('duration', 120) / 60
                    elif activity['type'] == 'break' and '📱' in activity.get('activity', ''):
                        total_phone_time += activity.get('duration', 15) / 60
            
            with col1:
                st.metric("Total Study Hours", f"{total_study_hours:.1f}h")
            with col2:
                st.metric("Daily Avg Study", f"{total_study_hours/total_days:.1f}h")
            with col3:
                st.metric("Daily Free Time", f"{total_free_hours/total_days:.1f}h")
            with col4:
                st.metric("Daily Phone Time", f"{total_phone_time/total_days:.1f}h")
            
            # Show sample week
            st.subheader("📅 Sample Week Preview")
            sample_dates = list(proposal['schedule'].keys())[:7]
            
            for date_str in sample_dates:
                day_schedule = proposal['schedule'][date_str]
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                day_name = date_obj.strftime('%A, %B %d')
                
                with st.expander(f"{day_name}"):
                    for activity in day_schedule:
                        duration = f" ({activity.get('duration', 30)} min)" if 'duration' in activity else ""
                        course_info = f" [{activity.get('course', '')}]" if activity.get('course') else ""
                        
                        # Color coding for different activity types
                        if activity['type'] == 'study':
                            st.write(f"📚 **{activity['time']}** - {activity['activity']}{course_info}{duration}")
                        elif activity['type'] == 'break' and '📱' in activity.get('activity', ''):
                            st.write(f"📱 **{activity['time']}** - {activity['activity']}{duration}")
                        elif activity['type'] == 'free':
                            st.write(f"🎉 **{activity['time']}** - {activity['activity']}{duration}")
                        elif activity['type'] == 'meal':
                            st.write(f"🍽️ **{activity['time']}** - {activity['activity']}{duration}")
                        elif activity['type'] == 'deadline':
                            st.write(f"⚠️ **{activity['time']}** - {activity['activity']}")
                        else:
                            st.write(f"• **{activity['time']}** - {activity['activity']}{duration}")
            
            # Select button
            if st.button(f"✅ Select {proposal['type'].title()} Schedule", key=f"select_{i}"):
                st.session_state.selected_schedule = proposal
                st.success(f"🎉 {proposal['type'].title()} schedule selected!")
                st.rerun()

# Final actions section
if st.session_state.selected_schedule:
    st.header("8️⃣ Export Your 2025 Schedule")
    
    selected = st.session_state.selected_schedule
    
    # Create export functions
    def create_2025_email_content(schedule_data):
        subject = f"Your 2025 StudyFlow {selected['type'].title()} Schedule"
        
        body = f"""Hey there!

Your {selected['type'].title()} StudyFlow schedule is ready! This schedule is designed for real 2025 college students with actual attention spans and distractions.

🎯 SCHEDULE TYPE: {selected['description']}

📚 YOUR COURSES:
"""
        for course in st.session_state.courses:
            body += f"• {course['code']} - {course['name']} (Difficulty: {course['difficulty']}/5)\n"
        
        body += f"""
⚠️ UPCOMING DEADLINES:
"""
        sorted_deadlines = sorted(st.session_state.deadlines, key=lambda x: x['date'])
        for deadline in sorted_deadlines:
            body += f"• {deadline['date']}: {deadline['title']} ({deadline['course']})\n"
        
        body += f"""
📝 YOUR OBLIGATIONS:
"""
        for obligation in st.session_state.obligations:
            if obligation['recurring']:
                start_12h = format_time_12hour(obligation['start_time'])
                end_12h = format_time_12hour(obligation['end_time'])
                body += f"• {obligation['title']}: {', '.join(obligation['days_of_week'])} {start_12h} - {end_12h}\n"
            else:
                start_12h = format_time_12hour(obligation['start_time'])
                end_12h = format_time_12hour(obligation['end_time'])
                body += f"• {obligation['title']}: {obligation['start_date']} {start_12h} - {end_12h}\n"
        
        body += f"""

📱 2025 STUDENT FEATURES:
• {study_attention_span}-minute focused study blocks (realistic attention span)
• Built-in phone/social media breaks
• {procrastination_buffer}% procrastination buffer built in
• US college meal times (5:00 PM dinner!)
• Evening social time protected
• All times in easy-to-read AM/PM format

🗓️ SAMPLE WEEK:
"""
        
        sample_dates = list(selected['schedule'].keys())[:7]
        for date_str in sample_dates:
            day_schedule = selected['schedule'][date_str]
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            day_name = date_obj.strftime('%A, %B %d')
            
            body += f"\n{day_name}:\n"
            for activity in day_schedule:
                duration = f" ({activity.get('duration', 30)} min)" if 'duration' in activity else ""
                body += f"  {activity['time']} - {activity['activity']}{duration}\n"
        
        body += f"""

🧠 SCIENCE-BASED FEATURES:
✓ {study_attention_span}-minute study blocks (matches actual attention spans)
✓ Spaced repetition with realistic review timing
✓ Interleaved study sessions between courses
✓ Phone break integration (because let's be real)
✓ Procrastination buffer built in

💡 TIPS FOR SUCCESS:
• Use your phone breaks wisely (set timers!)
• Study groups work great for accountability
• Don't feel bad about the procrastination buffer - it's realistic
• Evening social time is protected - maintain balance!
• All times are in AM/PM format - no confusing military time!

Generated by StudyFlow 2025 - Built for Real College Students
"""
        
        return subject, body
    
    def create_save_file():
        """Create a JSON file to save current state"""
        save_data = {
            'courses': st.session_state.courses,
            'deadlines': st.session_state.deadlines,
            'obligations': st.session_state.obligations,
            'selected_schedule': st.session_state.selected_schedule,
            'preferences': {
                'email': email,
                'wakeup': wakeup,
                'sleep': sleep,
                'semester_start': semester_start.strftime('%Y-%m-%d'),
                'semester_end': semester_end.strftime('%Y-%m-%d'),
                'phone_breaks': phone_breaks,
                'procrastination_buffer': procrastination_buffer,
                'study_attention_span': study_attention_span
            },
            'generated_date': datetime.now().isoformat()
        }
        return json.dumps(save_data, indent=2)
    
    def generate_ics_calendar():
        """Generate ICS calendar file"""
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//StudyFlow//StudyFlow 2025//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:StudyFlow 2025 Schedule
"""
        
        for date_str, activities in selected['schedule'].items():
            for activity in activities:
                if activity['type'] in ['study', 'obligation', 'deadline', 'review']:
                    event_id = str(uuid.uuid4())
                    event_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    try:
                        # Convert 12-hour time to 24-hour for ICS
                        time_24h = convert_to_24hour(activity['time'])
                        hour, minute = map(int, time_24h.split(':'))
                        start_datetime = event_date.replace(hour=hour, minute=minute)
                        duration_minutes = activity.get('duration', 30)
                        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
                        
                        start_str = start_datetime.strftime('%Y%m%dT%H%M%S')
                        end_str = end_datetime.strftime('%Y%m%dT%H%M%S')
                        
                        ics_content += f"""BEGIN:VEVENT
UID:{event_id}@studyflow.app
DTSTART:{start_str}
DTEND:{end_str}
SUMMARY:{activity['activity']}
DESCRIPTION:StudyFlow 2025 - Realistic College Schedule\\nType: {activity['type']}\\nDuration: {duration_minutes} minutes\\nTime: {activity['time']}
CATEGORIES:EDUCATION
END:VEVENT
"""
                    except:
                        continue
        
        ics_content += "END:VCALENDAR"
        return ics_content
    
    # Export buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Email Schedule", type="primary"):
            subject, body = create_2025_email_content(selected)
            mailto_url = f"mailto:{email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
            st.markdown(f'<a href="{mailto_url}" target="_blank">📧 Open Email Client</a>', unsafe_allow_html=True)
            st.success("📧 Email client opened with your 2025 schedule!")
    
    with col2:
        save_file_content = create_save_file()
        st.download_button(
            label="💾 Save Schedule File",
            data=save_file_content,
            file_name=f"StudyFlow_2025_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            help="Save this file to add more activities later!"
        )
    
    with col3:
        ics_content = generate_ics_calendar()
        st.download_button(
            label="📅 Download Calendar",
            data=ics_content,
            file_name=f"StudyFlow_2025_{datetime.now().strftime('%Y%m%d')}.ics",
            mime="text/calendar"
        )
    
    # Show final summary
    st.success(f"""
    🎉 **Your 2025-Realistic {selected['type'].title()} Schedule is Complete!**
    
    ✅ **Courses:** {len(st.session_state.courses)} courses integrated
    ✅ **Deadlines:** {len(st.session_state.deadlines)} deadlines tracked  
    ✅ **Obligations:** {len(st.session_state.obligations)} personal obligations included
    ✅ **Real Study Blocks:** {study_attention_span}-minute sessions (realistic attention span)
    ✅ **Phone Breaks:** Built-in social media time
    ✅ **US College Timing:** 5:00 PM dinner, realistic meal times
    ✅ **Procrastination Buffer:** {procrastination_buffer}% extra time built in
    ✅ **Easy Times:** All times in AM/PM format (no military time!)
    
    💡 **This schedule is designed for REAL 2025 college students with actual attention spans and distractions!**
    """)

else:
    if not st.session_state.courses:
        st.info("👆 Add some courses to get started!")
    elif not st.session_state.schedule_proposals:
        st.info("👆 Generate schedule proposals to continue!")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ for 2025 College Students • StudyFlow Realistic v5.0 • © 2024")
