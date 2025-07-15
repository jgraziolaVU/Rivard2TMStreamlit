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

# Page config
st.set_page_config(
    page_title="StudyFlow - Smart Study Planner",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'schedule_data' not in st.session_state:
    st.session_state.schedule_data = None
if 'share_id' not in st.session_state:
    st.session_state.share_id = None

# Title
st.title("📚 StudyFlow - Smart Study Planner")
st.markdown("Upload your course schedule and get a personalized study plan!")

# Sidebar for user preferences
st.sidebar.header("⚙️ Your Preferences")
email = st.sidebar.text_input("📧 Your Email", placeholder="your.email@example.com")
wakeup = st.sidebar.slider("🌅 Wake Up Time", 5, 12, 8)
sleep = st.sidebar.slider("😴 Sleep Time", 20, 26, 23)
study_style = st.sidebar.selectbox(
    "📖 Study Style",
    ["pomodoro", "focused", "flexible"],
    help="Pomodoro: 25min blocks, Focused: Long sessions, Flexible: Varied timing"
)

# Advanced preferences
with st.sidebar.expander("🔧 Advanced Options"):
    schedule_length = st.slider("📅 Schedule Length (days)", 7, 90, 30)
    include_weekends = st.checkbox("📅 Include Weekend Study", value=True)
    break_duration = st.slider("⏰ Break Duration (minutes)", 5, 30, 15)

# File upload
uploaded_file = st.file_uploader(
    "📄 Upload Your Course Schedule",
    type=['pdf', 'docx', 'txt'],
    help="Upload your syllabus, schedule, or any course document"
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
        # Extract from tables too
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
                text += "\n"
        return text
    else:  # txt file
        return str(file.read(), "utf-8")

def parse_deadlines(text):
    """Extract deadlines from text with better parsing"""
    deadlines = []
    
    # Enhanced deadline extraction
    deadline_keywords = ['due', 'deadline', 'exam', 'test', 'assignment', 'project', 'quiz', 'presentation', 'final', 'midterm']
    
    # Multiple date patterns
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY or MM/DD/YY
        r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY
        r'\b\w+ \d{1,2}, \d{4}\b',   # Month DD, YYYY
        r'\b\d{1,2} \w+ \d{4}\b',    # DD Month YYYY
        r'\d{1,2}/\d{1,2}',          # MM/DD (current year)
    ]
    
    sentences = re.split(r'[.!?\n]', text)
    for sentence in sentences:
        sentence = sentence.strip()
        if any(keyword in sentence.lower() for keyword in deadline_keywords):
            # Find dates in this sentence
            for pattern in date_patterns:
                date_matches = re.findall(pattern, sentence)
                if date_matches:
                    # Determine deadline type
                    deadline_type = 'assignment'
                    if any(word in sentence.lower() for word in ['exam', 'test', 'final', 'midterm']):
                        deadline_type = 'exam'
                    elif 'quiz' in sentence.lower():
                        deadline_type = 'quiz'
                    elif 'project' in sentence.lower():
                        deadline_type = 'project'
                    elif 'presentation' in sentence.lower():
                        deadline_type = 'presentation'
                    
                    deadlines.append({
                        'date': date_matches[0],
                        'description': sentence[:150],  # Limit description length
                        'type': deadline_type,
                        'priority': 'high' if deadline_type == 'exam' else 'medium'
                    })
                    break
    
    return deadlines

def generate_study_schedule(deadlines, wakeup, sleep, study_style, schedule_length=30, include_weekends=True):
    """Generate enhanced personalized study schedule"""
    schedule = {}
    start_date = datetime.now()
    
    for i in range(schedule_length):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        day_name = current_date.strftime('%A')
        is_weekend = current_date.weekday() >= 5
        
        # Skip weekends if not included
        if is_weekend and not include_weekends:
            continue
        
        daily_plan = []
        
        # Morning routine
        daily_plan.append({
            'time': f"{wakeup:02d}:00",
            'activity': '🌅 Morning Routine & Breakfast',
            'type': 'routine',
            'duration': 60,
            'color': '#e8f5e8'
        })
        
        # Study sessions based on style and day type
        if is_weekend:
            # Lighter weekend schedule
            study_sessions = [
                {'time': f"{wakeup+2:02d}:00", 'activity': '📚 Weekend Review Session', 'duration': 90, 'color': '#fff3e0'},
                {'time': '15:00', 'activity': '📚 Light Study Session', 'duration': 60, 'color': '#fff3e0'}
            ]
        else:
            # Weekday schedule based on study style
            if study_style == 'pomodoro':
                study_sessions = [
                    {'time': f"{wakeup+2:02d}:00", 'activity': '📚 Pomodoro Block 1 (4×25min)', 'duration': 120, 'color': '#e3f2fd'},
                    {'time': '14:00', 'activity': '📚 Pomodoro Block 2 (4×25min)', 'duration': 120, 'color': '#e3f2fd'},
                    {'time': '19:00', 'activity': '📚 Evening Review (2×25min)', 'duration': 60, 'color': '#e3f2fd'}
                ]
            elif study_style == 'focused':
                study_sessions = [
                    {'time': f"{wakeup+2:02d}:00", 'activity': '📚 Deep Focus Session 1', 'duration': 180, 'color': '#f3e5f5'},
                    {'time': '14:00', 'activity': '📚 Deep Focus Session 2', 'duration': 150, 'color': '#f3e5f5'}
                ]
            else:  # flexible
                study_sessions = [
                    {'time': f"{wakeup+2:02d}:00", 'activity': '📚 Morning Study', 'duration': 90, 'color': '#e8f5e8'},
                    {'time': '13:00', 'activity': '📚 Afternoon Study', 'duration': 60, 'color': '#e8f5e8'},
                    {'time': '16:00', 'activity': '📚 Late Afternoon Study', 'duration': 90, 'color': '#e8f5e8'},
                    {'time': '19:30', 'activity': '📚 Evening Review', 'duration': 45, 'color': '#e8f5e8'}
                ]
        
        daily_plan.extend(study_sessions)
        
        # Meals
        daily_plan.extend([
            {'time': '12:00', 'activity': '🍽️ Lunch Break', 'type': 'meal', 'duration': 60, 'color': '#fff8e1'},
            {'time': '18:00', 'activity': '🍽️ Dinner', 'type': 'meal', 'duration': 60, 'color': '#fff8e1'}
        ])
        
        # Exercise/wellness (weekdays only)
        if not is_weekend:
            daily_plan.append({
                'time': f"{wakeup+8:02d}:00",
                'activity': '💪 Exercise/Wellness',
                'type': 'wellness',
                'duration': 45,
                'color': '#e8f5e8'
            })
        
        # Check for deadlines
        for deadline in deadlines:
            if deadline['date'] in date_str or deadline['date'].replace('/', '-') in date_str:
                emoji = {'exam': '📝', 'assignment': '📄', 'project': '🚀', 'quiz': '❓', 'presentation': '🎤'}.get(deadline['type'], '⚠️')
                daily_plan.append({
                    'time': '23:59',
                    'activity': f"{emoji} {deadline['type'].upper()}: {deadline['description'][:50]}...",
                    'type': 'deadline',
                    'priority': deadline['priority'],
                    'color': '#ffebee'
                })
        
        # Add review sessions before deadlines
        for deadline in deadlines:
            try:
                deadline_date = datetime.strptime(deadline['date'], '%m/%d/%Y')
                days_until = (deadline_date - current_date).days
                if days_until in [1, 3, 7] and deadline['type'] in ['exam', 'project']:
                    intensity = {1: 'Intensive', 3: 'Focused', 7: 'Initial'}[days_until]
                    daily_plan.append({
                        'time': '20:00',
                        'activity': f"📖 {intensity} Review: {deadline['description'][:40]}...",
                        'type': 'review',
                        'duration': 60 if days_until == 1 else 45,
                        'color': '#fff3e0'
                    })
            except:
                continue
        
        # Free time
        daily_plan.append({
            'time': f"{sleep-2:02d}:00",
            'activity': '🎉 Free Time & Relaxation',
            'type': 'free',
            'duration': 120,
            'color': '#f1f8e9'
        })
        
        # Sort by time
        daily_plan.sort(key=lambda x: x['time'])
        
        schedule[date_str] = {
            'day': day_name,
            'activities': daily_plan,
            'is_weekend': is_weekend
        }
    
    return schedule

def generate_ics_calendar(schedule, email, study_style):
    """Generate ICS calendar file"""
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//StudyFlow//StudyFlow App//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:StudyFlow Schedule
X-WR-CALDESC:Your personalized study schedule
"""
    
    for date_str, day_info in schedule.items():
        for activity in day_info['activities']:
            if activity.get('type') not in ['routine', 'meal', 'free']:
                # Create unique event ID
                event_id = str(uuid.uuid4())
                
                # Parse date and time
                event_date = datetime.strptime(date_str, '%Y-%m-%d')
                try:
                    hour, minute = map(int, activity['time'].split(':'))
                    start_datetime = event_date.replace(hour=hour, minute=minute)
                    
                    # Calculate end time
                    duration_minutes = activity.get('duration', 60)
                    end_datetime = start_datetime + timedelta(minutes=duration_minutes)
                    
                    # Format for ICS
                    start_str = start_datetime.strftime('%Y%m%dT%H%M%S')
                    end_str = end_datetime.strftime('%Y%m%dT%H%M%S')
                    
                    ics_content += f"""BEGIN:VEVENT
UID:{event_id}@studyflow.app
DTSTART:{start_str}
DTEND:{end_str}
SUMMARY:{activity['activity']}
DESCRIPTION:Generated by StudyFlow\\nStudy Style: {study_style}\\nDuration: {duration_minutes} minutes
CATEGORIES:EDUCATION
END:VEVENT
"""
                except:
                    continue
    
    ics_content += "END:VCALENDAR"
    return ics_content

def generate_pdf_schedule(schedule, email, preferences):
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
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkgreen
    )
    
    story = []
    
    # Title
    story.append(Paragraph("📚 StudyFlow - Your Personal Study Schedule", title_style))
    story.append(Spacer(1, 12))
    
    # Preferences summary
    story.append(Paragraph("⚙️ Your Preferences", heading_style))
    pref_text = f"""
    <b>Email:</b> {email}<br/>
    <b>Wake Up:</b> {preferences['wakeup']}:00 AM<br/>
    <b>Sleep:</b> {preferences['sleep']}:00 PM<br/>
    <b>Study Style:</b> {preferences['study_style'].title()}<br/>
    <b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
    """
    story.append(Paragraph(pref_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Schedule by day
    story.append(Paragraph("📅 Your Daily Schedule", heading_style))
    
    for date_str, day_info in list(schedule.items())[:14]:  # First 2 weeks
        day_title = f"{day_info['day']} - {datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')}"
        story.append(Paragraph(day_title, styles['Heading3']))
        
        # Create table for activities
        table_data = [['Time', 'Activity', 'Duration']]
        for activity in day_info['activities']:
            duration = f"{activity.get('duration', 60)} min" if 'duration' in activity else ""
            table_data.append([
                activity['time'],
                activity['activity'],
                duration
            ])
        
        table = Table(table_data, colWidths=[1*inch, 4*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
    
    # Study tips
    story.append(Paragraph("💡 Study Tips for Success", heading_style))
    tips_text = """
    • Take regular breaks during study sessions<br/>
    • Stay hydrated and maintain good nutrition<br/>
    • Get adequate sleep (7-9 hours per night)<br/>
    • Use active learning techniques<br/>
    • Create a dedicated study space<br/>
    • Don't hesitate to ask for help when needed
    """
    story.append(Paragraph(tips_text, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def create_email_content(schedule, email, preferences):
    """Create email content for the schedule"""
    subject = "Your StudyFlow Schedule"
    
    body = f"""Hi there!

Here's your personalized study schedule from StudyFlow:

PREFERENCES:
- Wake up: {preferences['wakeup']}:00 AM
- Sleep: {preferences['sleep']}:00 PM  
- Study style: {preferences['study_style'].title()}
- Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

SCHEDULE PREVIEW (Next 7 Days):
"""
    
    # Add first week to email
    for i, (date, day_info) in enumerate(list(schedule.items())[:7]):
        body += f"\n{day_info['day']} ({date}):\n"
        for activity in day_info['activities'][:6]:  # First 6 activities
            duration = f" ({activity.get('duration', 60)} min)" if 'duration' in activity else ""
            body += f"  {activity['time']} - {activity['activity']}{duration}\n"
        body += "\n"
    
    body += """
STUDY TIPS:
- Take regular breaks during study sessions
- Stay hydrated and eat well
- Get enough sleep for better focus
- Review material before deadlines
- Use active learning techniques

Generated by StudyFlow - Your Smart Study Planner
Visit again anytime to create updated schedules!
"""
    
    return subject, body

def generate_share_link(schedule_data):
    """Generate a shareable link for the schedule"""
    # Create a unique ID for this schedule
    share_id = str(uuid.uuid4())[:8]
    
    # In a real app, you'd save this to a database
    # For demo purposes, we'll just store in session state
    st.session_state.share_id = share_id
    st.session_state.shared_schedule = schedule_data
    
    # Create the share URL (in real app, this would be your domain)
    share_url = f"https://studyflow.streamlit.app/shared/{share_id}"
    
    return share_url

def copy_to_clipboard_js(text):
    """Generate JavaScript to copy text to clipboard"""
    return f"""
    <script>
    function copyToClipboard() {{
        navigator.clipboard.writeText(`{text}`).then(function() {{
            alert('Schedule copied to clipboard!');
        }}).catch(function(err) {{
            console.error('Could not copy text: ', err);
        }});
    }}
    </script>
    """

# Main app logic
if uploaded_file and email:
    # Extract text
    with st.spinner("🔍 Analyzing your schedule..."):
        text = extract_text_from_file(uploaded_file)
    
    # Parse deadlines
    deadlines = parse_deadlines(text)
    
    # Generate schedule
    preferences = {
        'wakeup': wakeup,
        'sleep': sleep,
        'study_style': study_style,
        'schedule_length': schedule_length,
        'include_weekends': include_weekends
    }
    
    schedule = generate_study_schedule(
        deadlines, wakeup, sleep, study_style, schedule_length, include_weekends
    )
    
    # Store in session state
    st.session_state.schedule_data = {
        'schedule': schedule,
        'deadlines': deadlines,
        'preferences': preferences,
        'email': email
    }
    
    # Display results
    st.success("✅ Your personalized schedule is ready!")
    
    # Action buttons row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("📧 Email Schedule", type="primary"):
            subject, body = create_email_content(schedule, email, preferences)
            mailto_url = f"mailto:{email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
            st.markdown(f'<a href="{mailto_url}" target="_blank">Open Email Client</a>', unsafe_allow_html=True)
            st.success("📧 Email client opened!")
    
    with col2:
        # Calendar download
        ics_content = generate_ics_calendar(schedule, email, study_style)
        st.download_button(
            label="📅 Download Calendar",
            data=ics_content,
            file_name=f"StudyFlow_Calendar_{datetime.now().strftime('%Y%m%d')}.ics",
            mime="text/calendar"
        )
    
    with col3:
        # PDF download
        pdf_buffer = generate_pdf_schedule(schedule, email, preferences)
        st.download_button(
            label="📄 Download PDF",
            data=pdf_buffer,
            file_name=f"StudyFlow_Schedule_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
    
    with col4:
        # Copy to clipboard
        schedule_text = create_email_content(schedule, email, preferences)[1]
        if st.button("📋 Copy Schedule"):
            st.code(schedule_text, language="text")
            st.info("📋 Schedule displayed above - you can select and copy it!")
    
    with col5:
        # Share link
        if st.button("🔗 Generate Share Link"):
            share_url = generate_share_link(st.session_state.schedule_data)
            st.code(share_url)
            st.info("🔗 Share link generated! (Demo - not functional)")
    
    # Show deadlines found
    if deadlines:
        st.subheader("📅 Deadlines Found")
        deadline_df = pd.DataFrame(deadlines)
        st.dataframe(deadline_df, use_container_width=True)
    
    # Show schedule preview
    st.subheader("📋 Your Schedule Preview")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        show_weekends = st.checkbox("Show Weekends", value=include_weekends)
    with col2:
        view_type = st.selectbox("View Type", ["Daily Tabs", "Weekly Table", "Calendar View"])
    
    if view_type == "Daily Tabs":
        # Create tabs for each day
        filtered_schedule = {k: v for k, v in schedule.items() if show_weekends or not v['is_weekend']}
        tab_names = [f"{schedule[date]['day'][:3]} {datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')}" 
                    for date in list(filtered_schedule.keys())[:7]]
        
        tabs = st.tabs(tab_names)
        
        for i, (date, day_info) in enumerate(list(filtered_schedule.items())[:7]):
            with tabs[i]:
                st.write(f"**{day_info['day']} - {datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y')}**")
                
                for activity in day_info['activities']:
                    # Color coding based on activity type
                    if activity.get('type') == 'deadline':
                        st.error(f"🔴 {activity['time']} - {activity['activity']}")
                    elif activity.get('type') == 'review':
                        st.warning(f"🟡 {activity['time']} - {activity['activity']}")
                    elif 'study' in activity.get('activity', '').lower():
                        st.info(f"🔵 {activity['time']} - {activity['activity']}")
                    else:
                        duration = f" ({activity.get('duration', 60)} min)" if 'duration' in activity else ""
                        st.write(f"⚪ {activity['time']} - {activity['activity']}{duration}")
    
    elif view_type == "Weekly Table":
        # Create a weekly table view
        st.subheader("📊 Weekly Overview")
        
        # Prepare data for table
        weekly_data = []
        for date, day_info in list(schedule.items())[:7]:
            if not show_weekends and day_info['is_weekend']:
                continue
            
            study_hours = sum(activity.get('duration', 60) for activity in day_info['activities'] 
                            if 'study' in activity.get('activity', '').lower()) / 60
            
            deadlines_count = sum(1 for activity in day_info['activities'] 
                                if activity.get('type') == 'deadline')
            
            weekly_data.append({
                'Day': day_info['day'],
                'Date': datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d'),
                'Study Hours': f"{study_hours:.1f}h",
                'Deadlines': deadlines_count,
                'Activities': len(day_info['activities'])
            })
        
        df = pd.DataFrame(weekly_data)
        st.dataframe(df, use_container_width=True)
    
    else:  # Calendar View
        st.subheader("📅 Calendar View")
        st.info("📅 Calendar view would show a monthly calendar with activities. This is a simplified version.")
        
        # Simple calendar representation
        for date, day_info in list(schedule.items())[:7]:
            if not show_weekends and day_info['is_weekend']:
                continue
            
            with st.expander(f"{day_info['day']} - {datetime.strptime(date, '%Y-%m-%d').strftime('%B %d')}"):
                for activity in day_info['activities']:
                    st.write(f"• {activity['time']} - {activity['activity']}")
    
    # Statistics
    st.subheader("📊 Schedule Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    total_study_hours = sum(
        sum(activity.get('duration', 60) for activity in day_info['activities'] 
            if 'study' in activity.get('activity', '').lower()) / 60
        for day_info in schedule.values()
    )
    
    total_deadlines = sum(
        sum(1 for activity in day_info['activities'] if activity.get('type') == 'deadline')
        for day_info in schedule.values()
    )
    
    with col1:
        st.metric("Total Study Hours", f"{total_study_hours:.1f}h")
    
    with col2:
        st.metric("Total Deadlines", total_deadlines)
    
    with col3:
        st.metric("Schedule Days", len(schedule))
    
    with col4:
        avg_daily_study = total_study_hours / len(schedule)
        st.metric("Avg Daily Study", f"{avg_daily_study:.1f}h")

else:
    st.info("👆 Please upload your course schedule and enter your email to get started!")
    
    # Show example and instructions
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📖 How It Works")
        st.markdown("""
        1. **Upload** your course schedule, syllabus, or any academic document
        2. **Set** your preferences (wake time, sleep time, study style)  
        3. **Generate** your personalized study schedule
        4. **Export** your schedule in multiple formats:
           - 📧 **Email** to yourself
           - 📅 **Calendar** file (.ics)
           - 📄 **PDF** document
           - 📋 **Copy** to clipboard
           - 🔗 **Share** link
        
        **No accounts needed, no data stored!** Everything happens in your browser.
        """)
    
    with col2:
        st.subheader("✨ Features")
        st.markdown("""
        **📚 Smart Parsing**
        - Extracts deadlines from any document
        - Recognizes exams, assignments, projects
        - Supports PDF, DOCX, and TXT files
        
        **🎯 Personalized Planning**
        - Adapts to your schedule preferences
        - Multiple study styles (Pomodoro, Focused, Flexible)
        - Weekend study options
        
        **📤 Easy Export**
        - Email integration with default mail client
        - Calendar files for Google/Outlook
        - Professional PDF reports
        - Shareable links for collaboration
        """)
    
    # Demo section
    st.subheader("🎬 Try a Demo")
    if st.button("🚀 Generate Sample Schedule"):
        # Create demo data
        demo_deadlines = [
            {'date': '12/15/2024', 'description': 'Computer Science Final Exam', 'type': 'exam', 'priority': 'high'},
            {'date': '12/10/2024', 'description': 'Math Assignment Due', 'type': 'assignment', 'priority': 'medium'},
            {'date': '12/20/2024', 'description': 'History Research Project', 'type': 'project', 'priority': 'high'}
        ]
        
        demo_schedule = generate_study_schedule(demo_deadlines, 8, 23, 'pomodoro', 14, True)
        
        st.success("✅ Demo schedule generated!")
        st.subheader("📋 Sample Schedule Preview")
        
        # Show first 3 days
        for i, (date, day_info) in enumerate(list(demo_schedule.items())[:3]):
            with st.expander(f"Day {i+1}: {day_info['day']} - {datetime.strptime(date, '%Y-%m-%d').strftime('%B %d')}"):
                for activity in day_info['activities']:
                    st.write(f"• {activity['time']} - {activity['activity']}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit • StudyFlow v2.0 • © 2024")
