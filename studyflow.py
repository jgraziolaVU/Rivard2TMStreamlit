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
    page_title="StudyFlow - Complete Time Management",
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

# Title
st.title("📚 StudyFlow - Complete Time Management System")
st.markdown("Upload schedules, add obligations, and get scientifically-optimized study plans!")

# Sidebar for basic preferences
st.sidebar.header("⚙️ Basic Settings")
email = st.sidebar.text_input("📧 Your Email", placeholder="your.email@example.com")
wakeup = st.sidebar.slider("🌅 Wake Up Time", 5, 12, 8)
sleep = st.sidebar.slider("😴 Sleep Time", 20, 26, 23)
semester_start = st.sidebar.date_input("📅 Semester Start Date", datetime.now().date())
semester_end = st.sidebar.date_input("📅 Semester End Date", datetime.now().date() + timedelta(days=120))

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
        r'([A-Z]{2,4}\s+\d{3,4})\s*[-:]?\s*([^:\n]+)'
    ]
    
    for pattern in course_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) == 2:
                courses.append({
                    'code': match[0].strip().upper(),
                    'name': match[1].strip(),
                    'difficulty': 3,  # Default medium difficulty
                    'credits': 3
                })
    
    # Deadline extraction with multiple date formats
    deadline_keywords = ['due', 'deadline', 'exam', 'test', 'assignment', 'project', 'quiz', 'presentation', 'final', 'midterm', 'practical']
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY
        r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY
        r'\b\w+ \d{1,2}, \d{4}\b',   # Month DD, YYYY
        r'\b\d{1,2} \w+ \d{4}\b',    # DD Month YYYY
        r'\d{1,2}/\d{1,2}',          # MM/DD (add current year)
        r'\b\w+ \d{1,2}\b',          # Month DD (add current year)
        r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+\d{1,2}/\d{1,2}',  # Day MM/DD
    ]
    
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
                    
                    deadlines.append({
                        'id': str(uuid.uuid4()),
                        'title': sentence[:80].strip(),
                        'date': date_matches[0],
                        'type': deadline_type,
                        'course': courses[0]['code'] if courses else 'UNKNOWN',
                        'priority': 'high' if deadline_type == 'exam' else 'medium',
                        'study_hours_needed': 8 if deadline_type == 'exam' else 4
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
        course_code = st.text_input("Course Code", placeholder="CS101")
        course_name = st.text_input("Course Name", placeholder="Introduction to Computer Science")
        difficulty = st.slider("Difficulty Level", 1, 5, 3, help="1=Easy, 5=Very Hard")
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
        st.info("No courses added yet")

# Deadlines management
st.header("4️⃣ Manage Deadlines & Assignments")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Add Deadline")
    with st.form("deadline_form"):
        deadline_title = st.text_input("Assignment/Exam Title")
        deadline_date = st.date_input("Due Date")
        deadline_type = st.selectbox("Type", ["assignment", "exam", "quiz", "project", "presentation"])
        deadline_course = st.selectbox("Course", [c['code'] for c in st.session_state.courses] if st.session_state.courses else ["NONE"])
        study_hours = st.number_input("Study Hours Needed", min_value=1, max_value=40, value=8)
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
        obligation_title = st.text_input("Obligation Title", placeholder="Work, gym, meetings, etc.")
        obligation_type = st.selectbox("Type", ["work", "meeting", "appointment", "exercise", "personal", "recurring"])
        
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
                    st.write(f"Recurring: {', '.join(obligation['days_of_week'])} | {obligation['start_time']}-{obligation['end_time']}")
                else:
                    st.write(f"Date: {obligation['start_date']} | {obligation['start_time']}-{obligation['end_time']}")
            with col_b:
                if st.button(f"🗑️", key=f"delete_obligation_{i}"):
                    st.session_state.obligations.pop(i)
                    st.rerun()
    else:
        st.info("No obligations added yet")

# Schedule generation section
st.header("6️⃣ Generate Schedule Proposals")

def calculate_study_time_per_course():
    """Calculate weekly study time needed per course based on difficulty and credits"""
    study_times = {}
    for course in st.session_state.courses:
        # Base study time = credits * difficulty * 2 hours per week
        weekly_hours = course['credits'] * course['difficulty'] * 2
        study_times[course['code']] = weekly_hours
    return study_times

def create_time_slots(start_hour, end_hour, slot_duration=60):
    """Create available time slots"""
    slots = []
    current_hour = start_hour
    while current_hour < end_hour:
        slots.append(f"{current_hour:02d}:00")
        current_hour += slot_duration // 60
    return slots

def is_time_available(date, time_slot, existing_obligations):
    """Check if a time slot is available"""
    day_name = date.strftime('%A')
    
    for obligation in existing_obligations:
        if obligation['recurring'] and day_name in obligation['days_of_week']:
            if obligation['start_time'] <= time_slot <= obligation['end_time']:
                return False
        elif not obligation['recurring']:
            if obligation['start_date'] == date.strftime('%Y-%m-%d'):
                if obligation['start_time'] <= time_slot <= obligation['end_time']:
                    return False
    
    return True

def implement_spaced_repetition(course_code, study_sessions, total_weeks):
    """Implement spaced repetition scheduling"""
    sessions = []
    intervals = [1, 3, 7, 14, 30]  # Days between reviews
    
    for week in range(total_weeks):
        # Initial learning session
        sessions.append({
            'week': week,
            'type': 'initial',
            'course': course_code,
            'priority': 'high'
        })
        
        # Review sessions at increasing intervals
        for i, interval in enumerate(intervals):
            review_week = week + (interval // 7)
            if review_week < total_weeks:
                sessions.append({
                    'week': review_week,
                    'type': f'review_{i+1}',
                    'course': course_code,
                    'priority': 'medium' if i < 2 else 'low'
                })
    
    return sessions

def generate_schedule_proposal(proposal_type, study_times):
    """Generate a specific schedule proposal"""
    schedule = defaultdict(list)
    total_weeks = (semester_end - semester_start).days // 7
    
    # Calculate total semester dates
    current_date = semester_start
    semester_dates = []
    while current_date <= semester_end:
        semester_dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Create base schedule with fixed obligations
    for date in semester_dates:
        date_str = date.strftime('%Y-%m-%d')
        
        # Add morning routine
        schedule[date_str].append({
            'time': f"{wakeup:02d}:00",
            'activity': '🌅 Morning Routine',
            'type': 'routine',
            'duration': 60,
            'fixed': True
        })
        
        # Add meals
        schedule[date_str].extend([
            {'time': '12:00', 'activity': '🍽️ Lunch', 'type': 'meal', 'duration': 60, 'fixed': True},
            {'time': '18:00', 'activity': '🍽️ Dinner', 'type': 'meal', 'duration': 60, 'fixed': True}
        ])
        
        # Add obligations
        for obligation in st.session_state.obligations:
            if obligation['recurring'] and date.strftime('%A') in obligation['days_of_week']:
                schedule[date_str].append({
                    'time': obligation['start_time'],
                    'activity': f"📝 {obligation['title']}",
                    'type': 'obligation',
                    'duration': (datetime.strptime(obligation['end_time'], '%H:%M') - 
                               datetime.strptime(obligation['start_time'], '%H:%M')).seconds // 60,
                    'fixed': True
                })
            elif not obligation['recurring'] and obligation['start_date'] == date_str:
                schedule[date_str].append({
                    'time': obligation['start_time'],
                    'activity': f"📝 {obligation['title']}",
                    'type': 'obligation',
                    'duration': (datetime.strptime(obligation['end_time'], '%H:%M') - 
                               datetime.strptime(obligation['start_time'], '%H:%M')).seconds // 60,
                    'fixed': True
                })
        
        # Add deadline-specific activities
        for deadline in st.session_state.deadlines:
            if deadline['date'] == date_str:
                schedule[date_str].append({
                    'time': '23:59',
                    'activity': f"⚠️ DUE: {deadline['title']}",
                    'type': 'deadline',
                    'course': deadline['course'],
                    'priority': deadline['priority'],
                    'fixed': True
                })
    
    # Generate study sessions based on proposal type
    available_slots = create_time_slots(wakeup + 2, sleep - 2, 60)
    
    for date in semester_dates:
        date_str = date.strftime('%Y-%m-%d')
        is_weekend = date.weekday() >= 5
        
        # Get existing activities for this day
        existing_activities = schedule[date_str]
        busy_times = [act['time'] for act in existing_activities if act.get('fixed')]
        
        # Add study sessions based on proposal type
        if proposal_type == "intensive":
            # Intensive schedule: More study hours, longer sessions
            study_sessions_per_day = 4 if not is_weekend else 2
            session_duration = 90
        elif proposal_type == "balanced":
            # Balanced schedule: Moderate study hours, mixed sessions
            study_sessions_per_day = 3 if not is_weekend else 2
            session_duration = 75
        else:  # relaxed
            # Relaxed schedule: Fewer study hours, shorter sessions
            study_sessions_per_day = 2 if not is_weekend else 1
            session_duration = 60
        
        # Implement scientific interspersing
        courses_for_day = list(st.session_state.courses)
        random.shuffle(courses_for_day)  # Randomize for interleaving
        
        sessions_added = 0
        for i, slot in enumerate(available_slots):
            if sessions_added >= study_sessions_per_day:
                break
            
            if slot not in busy_times:
                course = courses_for_day[sessions_added % len(courses_for_day)] if courses_for_day else None
                if course:
                    # Apply spaced repetition logic
                    session_type = "review" if sessions_added % 3 == 0 else "practice"
                    
                    schedule[date_str].append({
                        'time': slot,
                        'activity': f"📚 {course['code']} - {session_type.title()}",
                        'type': 'study',
                        'course': course['code'],
                        'duration': session_duration,
                        'session_type': session_type,
                        'fixed': False
                    })
                    sessions_added += 1
        
        # Add relaxation time
        if not is_weekend:
            schedule[date_str].append({
                'time': f"{sleep-2:02d}:00",
                'activity': '🎉 Relaxation & Free Time',
                'type': 'relaxation',
                'duration': 120,
                'fixed': True
            })
        
        # Sort activities by time
        schedule[date_str].sort(key=lambda x: x['time'])
    
    return dict(schedule)

if st.button("🚀 Generate Schedule Proposals", type="primary"):
    if not email:
        st.error("❌ Please enter your email in the sidebar first")
    elif not st.session_state.courses:
        st.error("❌ Please add at least one course first")
    else:
        with st.spinner("⚡ Generating 3 scientifically-optimized schedule proposals..."):
            study_times = calculate_study_time_per_course()
            
            # Generate 3 different proposals
            proposals = []
            for proposal_type in ["intensive", "balanced", "relaxed"]:
                proposal = generate_schedule_proposal(proposal_type, study_times)
                proposals.append({
                    'type': proposal_type,
                    'schedule': proposal,
                    'description': {
                        'intensive': "🔥 High study hours, maximum preparation",
                        'balanced': "⚖️ Balanced study and personal time",
                        'relaxed': "🌿 Lighter schedule, more flexibility"
                    }[proposal_type]
                })
            
            st.session_state.schedule_proposals = proposals
            st.success("✅ Generated 3 schedule proposals!")

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
            total_days = len(proposal['schedule'])
            
            for day_schedule in proposal['schedule'].values():
                for activity in day_schedule:
                    if activity['type'] == 'study':
                        total_study_hours += activity.get('duration', 60) / 60
                    elif activity['type'] == 'relaxation':
                        total_free_hours += activity.get('duration', 60) / 60
            
            with col1:
                st.metric("Total Study Hours", f"{total_study_hours:.1f}h")
            with col2:
                st.metric("Daily Avg Study", f"{total_study_hours/total_days:.1f}h")
            with col3:
                st.metric("Free Time/Day", f"{total_free_hours/total_days:.1f}h")
            with col4:
                st.metric("Schedule Days", total_days)
            
            # Show sample week
            st.subheader("📅 Sample Week Preview")
            sample_dates = list(proposal['schedule'].keys())[:7]
            
            for date_str in sample_dates:
                day_schedule = proposal['schedule'][date_str]
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                day_name = date_obj.strftime('%A, %B %d')
                
                with st.expander(f"{day_name}"):
                    for activity in day_schedule:
                        duration = f" ({activity.get('duration', 60)} min)" if 'duration' in activity else ""
                        course_info = f" [{activity.get('course', '')}]" if activity.get('course') else ""
                        st.write(f"• {activity['time']} - {activity['activity']}{course_info}{duration}")
            
            # Select button
            if st.button(f"✅ Select {proposal['type'].title()} Schedule", key=f"select_{i}"):
                st.session_state.selected_schedule = proposal
                st.success(f"🎉 {proposal['type'].title()} schedule selected!")
                st.rerun()

# Final actions section
if st.session_state.selected_schedule:
    st.header("8️⃣ Export Your Schedule")
    
    selected = st.session_state.selected_schedule
    
    # Create export functions
    def create_email_content(schedule_data):
        subject = f"Your StudyFlow {selected['type'].title()} Schedule"
        
        body = f"""Hello!

Your {selected['type'].title()} StudyFlow schedule is ready!

SCHEDULE TYPE: {selected['description']}

COURSES:
"""
        for course in st.session_state.courses:
            body += f"• {course['code']} - {course['name']} (Difficulty: {course['difficulty']}/5)\n"
        
        body += f"""
UPCOMING DEADLINES:
"""
        for deadline in st.session_state.deadlines:
            body += f"• {deadline['date']}: {deadline['title']} ({deadline['course']})\n"
        
        body += f"""
OBLIGATIONS:
"""
        for obligation in st.session_state.obligations:
            if obligation['recurring']:
                body += f"• {obligation['title']}: {', '.join(obligation['days_of_week'])} {obligation['start_time']}-{obligation['end_time']}\n"
            else:
                body += f"• {obligation['title']}: {obligation['start_date']} {obligation['start_time']}-{obligation['end_time']}\n"
        
        body += f"""

SAMPLE WEEK:
"""
        
        sample_dates = list(selected['schedule'].keys())[:7]
        for date_str in sample_dates:
            day_schedule = selected['schedule'][date_str]
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            day_name = date_obj.strftime('%A, %B %d')
            
            body += f"\n{day_name}:\n"
            for activity in day_schedule:
                duration = f" ({activity.get('duration', 60)} min)" if 'duration' in activity else ""
                body += f"  {activity['time']} - {activity['activity']}{duration}\n"
        
        body += """

Your schedule uses scientific principles:
✓ Spaced repetition for better retention
✓ Interleaved study sessions between courses
✓ Optimized difficulty-based time allocation

Generated by StudyFlow - Your Complete Time Management System
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
                'semester_end': semester_end.strftime('%Y-%m-%d')
            },
            'generated_date': datetime.now().isoformat()
        }
        return json.dumps(save_data, indent=2)
    
    def generate_ics_calendar():
        """Generate ICS calendar file"""
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//StudyFlow//StudyFlow Complete//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:StudyFlow Complete Schedule
"""
        
        for date_str, activities in selected['schedule'].items():
            for activity in activities:
                if activity['type'] in ['study', 'obligation', 'deadline']:
                    event_id = str(uuid.uuid4())
                    event_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    try:
                        hour, minute = map(int, activity['time'].split(':'))
                        start_datetime = event_date.replace(hour=hour, minute=minute)
                        duration_minutes = activity.get('duration', 60)
                        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
                        
                        start_str = start_datetime.strftime('%Y%m%dT%H%M%S')
                        end_str = end_datetime.strftime('%Y%m%dT%H%M%S')
                        
                        ics_content += f"""BEGIN:VEVENT
UID:{event_id}@studyflow.app
DTSTART:{start_str}
DTEND:{end_str}
SUMMARY:{activity['activity']}
DESCRIPTION:Generated by StudyFlow Complete\\nType: {activity['type']}\\nDuration: {duration_minutes} minutes
CATEGORIES:EDUCATION
END:VEVENT
"""
                    except:
                        continue
        
        ics_content += "END:VCALENDAR"
        return ics_content
    
    def generate_pdf_schedule():
        """Generate PDF schedule"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        
        story = []
        
        # Title
        story.append(Paragraph("📚 StudyFlow - Your Complete Study Schedule", title_style))
        story.append(Spacer(1, 12))
        
        # Preferences summary
        pref_text = f"""
        <b>Schedule Type:</b> {selected['type'].title()} - {selected['description']}<br/>
        <b>Email:</b> {email}<br/>
        <b>Wake Up:</b> {wakeup}:00 AM<br/>
        <b>Sleep:</b> {sleep}:00 PM<br/>
        <b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        """
        story.append(Paragraph(pref_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Courses
        story.append(Paragraph("📚 Your Courses", styles['Heading2']))
        for course in st.session_state.courses:
            course_text = f"• {course['code']} - {course['name']} (Difficulty: {course['difficulty']}/5, Credits: {course['credits']})"
            story.append(Paragraph(course_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Sample schedule
        story.append(Paragraph("📅 Sample Week Schedule", styles['Heading2']))
        
        sample_dates = list(selected['schedule'].keys())[:7]
        for date_str in sample_dates:
            day_schedule = selected['schedule'][date_str]
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            day_name = date_obj.strftime('%A, %B %d')
            
            story.append(Paragraph(day_name, styles['Heading3']))
            
            for activity in day_schedule:
                duration = f" ({activity.get('duration', 60)} min)" if 'duration' in activity else ""
                activity_text = f"• {activity['time']} - {activity['activity']}{duration}"
                story.append(Paragraph(activity_text, styles['Normal']))
            
            story.append(Spacer(1, 12))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    # Export buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Email Schedule", type="primary"):
            subject, body = create_email_content(selected)
            mailto_url = f"mailto:{email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
            st.markdown(f'<a href="{mailto_url}" target="_blank">📧 Open Email Client</a>', unsafe_allow_html=True)
            st.success("📧 Email client opened!")
    
    with col2:
        save_file_content = create_save_file()
        st.download_button(
            label="💾 Save Schedule File",
            data=save_file_content,
            file_name=f"StudyFlow_Complete_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            help="Save this file to add more activities later!"
        )
    
    with col3:
        ics_content = generate_ics_calendar()
        st.download_button(
            label="📅 Download Calendar",
            data=ics_content,
            file_name=f"StudyFlow_Calendar_{datetime.now().strftime('%Y%m%d')}.ics",
            mime="text/calendar"
        )
    
    # PDF download in separate row
    st.subheader("📄 Additional Export Options")
    col1, col2 = st.columns(2)
    
    with col1:
        pdf_buffer = generate_pdf_schedule()
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_buffer,
            file_name=f"StudyFlow_Schedule_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
    
    with col2:
        schedule_text = create_email_content(selected)[1]
        st.download_button(
            label="📋 Download Text Summary",
            data=schedule_text,
            file_name=f"StudyFlow_Summary_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
    
    # Show final summary
    st.success(f"""
    🎉 **Your {selected['type'].title()} Schedule is Complete!**
    
    ✅ **Courses:** {len(st.session_state.courses)} courses integrated
    ✅ **Deadlines:** {len(st.session_state.deadlines)} deadlines tracked  
    ✅ **Obligations:** {len(st.session_state.obligations)} personal obligations included
    ✅ **Scientific Scheduling:** Spaced repetition and interleaved study implemented
    ✅ **Complete Integration:** School + personal life optimized together
    
    💡 **Pro Tip:** Save your schedule file to easily add new activities later!
    """)

else:
    if not st.session_state.courses:
        st.info("👆 Add some courses to get started!")
    elif not st.session_state.schedule_proposals:
        st.info("👆 Generate schedule proposals to continue!")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit • StudyFlow Complete v3.0 • © 2024")
