import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import pickle
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="EduLens AI",
    page_icon="🎓",
    layout="wide"
)

DB_PATH = 'edulens.db'
MODEL_PATH = 'dropout_model.pkl'
ENCODER_PATH = 'label_encoder.pkl'
@st.cache_resource
def load_model():
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    with open(ENCODER_PATH, 'rb') as f:
        le = pickle.load(f)
    return model, le

@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    students = pd.read_sql('SELECT * FROM students', conn)
    enrollments = pd.read_sql('SELECT * FROM enrollments', conn)
    assessments = pd.read_sql('SELECT * FROM assessments', conn)
    sessions = pd.read_sql('SELECT * FROM learning_sessions', conn)
    risk = pd.read_sql('SELECT * FROM risk_scores', conn)
    courses = pd.read_sql('SELECT * FROM courses', conn)
    conn.close()
    return students, enrollments, assessments, sessions, risk, courses

model, le = load_model()
students, enrollments, assessments, sessions, risk, courses = load_data()

# ================================================
# SIDEBAR
# ================================================
st.sidebar.image("https://via.placeholder.com/280x80/1a73e8/ffffff?text=EduLens+AI", 
                 use_column_width=True)
st.sidebar.markdown("---")
page = st.sidebar.selectbox(
    "Navigate",
    ["Dashboard", "Student Analysis", "Live Prediction", "Learning Paths"]
)
st.sidebar.markdown("---")
st.sidebar.markdown("**EduLens AI** v1.0")
st.sidebar.markdown("Built by Vaishnavi Singasani")
st.sidebar.markdown("Google Pitch Project 2025")

# ================================================
# PAGE 1: DASHBOARD
# ================================================
if page == "Dashboard":
    st.title("EduLens AI — Educator Dashboard")
    st.markdown("*Real-time student engagement and dropout risk analytics*")
    st.markdown("---")

    # Metric cards
    total_students = len(students)
    dropout_count = len(enrollments[enrollments['status'] == 'dropped'])
    dropout_rate = dropout_count / len(enrollments) * 100
    at_risk = len(risk[risk['risk_level'].isin(['high', 'critical'])])
    avg_score = assessments['score'].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", f"{total_students}")
    col2.metric("Dropout Rate", f"{dropout_rate:.1f}%", "-2.3%")
    col3.metric("At-Risk Students", f"{at_risk}", f"+{at_risk}")
    col4.metric("Avg Assessment Score", f"{avg_score:.1f}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Enrollment Status")
        status_counts = enrollments['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig = px.pie(status_counts, values='Count', names='Status',
                     color_discrete_sequence=['#1D9E75', '#378ADD', '#E24B4A'],
                     hole=0.4)
        fig.update_layout(height=300, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Risk Level Distribution")
        risk_counts = risk['risk_level'].value_counts().reset_index()
        risk_counts.columns = ['Risk Level', 'Count']
        color_map = {
            'low': '#1D9E75', 'medium': '#BA7517',
            'high': '#E24B4A', 'critical': '#7F77DD'
        }
        fig = px.bar(risk_counts, x='Risk Level', y='Count',
                     color='Risk Level', color_discrete_map=color_map)
        fig.update_layout(height=300, margin=dict(t=20, b=20),
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Score Distribution Across All Students")
    fig = px.histogram(assessments, x='score', nbins=20,
                       color_discrete_sequence=['#378ADD'])
    fig.add_vline(x=40, line_dash="dash", line_color="red",
                  annotation_text="Pass threshold")
    fig.update_layout(height=300, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# ================================================
# PAGE 2: STUDENT ANALYSIS
# ================================================
elif page == "Student Analysis":
    st.title("Student Analysis")
    st.markdown("*Deep dive into individual student performance*")
    st.markdown("---")

    student_list = students['name'].tolist()
    selected_name = st.selectbox("Select a student", student_list)

    selected = students[students['name'] == selected_name].iloc[0]
    student_id = selected['student_id']

    col1, col2, col3 = st.columns(3)
    col1.metric("Age", selected['age'])
    col2.metric("Learning Style", selected['learning_style'].title())
    col3.metric("Baseline Score", f"{selected['baseline_score']:.1f}")

    st.markdown("---")

    student_assess = assessments[assessments['student_id'] == student_id]
    student_sessions = sessions[sessions['student_id'] == student_id]
    student_risk = risk[risk['student_id'] == student_id]
    student_enroll = enrollments[enrollments['student_id'] == student_id]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Assessment Scores")
        if len(student_assess) > 0:
            fig = px.bar(student_assess, x=student_assess.index,
                         y='score', color_discrete_sequence=['#378ADD'])
            fig.add_hline(y=40, line_dash="dash", line_color="red")
            fig.update_layout(height=250, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No assessments found")

    with col2:
        st.subheader("Risk Profile")
        if len(student_risk) > 0:
            risk_row = student_risk.iloc[0]
            prob = risk_row['dropout_probability']
            level = risk_row['risk_level']

            color = {'low':'green','medium':'orange',
                     'high':'red','critical':'purple'}.get(level, 'gray')

            st.markdown(f"**Risk Level:** :{color}[{level.upper()}]")
            st.progress(float(prob))
            st.markdown(f"**Dropout Probability:** {prob*100:.1f}%")
        else:
            st.info("No risk data found")

    st.subheader("Enrollment Status")
    if len(student_enroll) > 0:
        enroll_display = student_enroll.merge(
            courses[['course_id', 'course_name']], on='course_id', how='left'
        )[['course_name', 'progress_pct', 'status']]
        st.dataframe(enroll_display, use_container_width=True)

# ================================================
# PAGE 3: LIVE PREDICTION
# ================================================
elif page == "Live Prediction":
    st.title("Live Dropout Prediction")
    st.markdown("*Enter student details to predict dropout risk in real time*")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Student Profile")
        age = st.slider("Age", 17, 50, 22)
        baseline_score = st.slider("Baseline Score", 0.0, 100.0, 60.0)
        progress_pct = st.slider("Course Progress (%)", 0.0, 100.0, 40.0)
        learning_style = st.selectbox(
            "Learning Style",
            ['visual', 'auditory', 'reading', 'kinesthetic']
        )

    with col2:
        st.subheader("Performance Signals")
        avg_duration = st.slider("Avg Session Duration (mins)", 0, 120, 45)
        total_sessions = st.slider("Total Sessions Attended", 0, 30, 8)
        avg_score = st.slider("Average Assessment Score", 0.0, 100.0, 55.0)
        failed_count = st.slider("Number of Failed Assessments", 0, 10, 1)

    st.markdown("---")

    if st.button("Predict Dropout Risk", type="primary"):
        risk_map = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
        ls_encoded = le.transform([learning_style])[0] if learning_style in le.classes_ else 0

        dropout_prob_estimate = max(0, min(1,
            (1 - avg_score/100) * 0.4 +
            (1 - progress_pct/100) * 0.3 +
            (failed_count / 10) * 0.3
        ))

        sample = pd.DataFrame([{
            'age': age,
            'baseline_score': baseline_score,
            'progress_pct': progress_pct,
            'avg_duration': avg_duration,
            'total_sessions': total_sessions,
            'avg_score': avg_score,
            'failed_count': failed_count,
            'dropout_probability': dropout_prob_estimate,
            'learning_style_encoded': ls_encoded,
            'risk_level_encoded': 1
        }])

        prediction = model.predict(sample)[0]
        probability = model.predict_proba(sample)[0][1]

        col1, col2, col3 = st.columns(3)

        if prediction == 1:
            col1.error(f"DROPOUT RISK DETECTED")
        else:
            col1.success(f"STUDENT ON TRACK")

        col2.metric("Dropout Probability", f"{probability*100:.1f}%")

        if probability >= 0.5:
            col3.error("Risk Level: HIGH")
            path_type = "CRITICAL INTERVENTION"
        elif probability >= 0.3:
            col3.warning("Risk Level: MEDIUM")
            path_type = "REMEDIAL"
        else:
            col3.success("Risk Level: LOW")
            path_type = "STANDARD"

        st.markdown("---")
        st.subheader("Recommended Learning Path")

        style_tips = {
            'visual': ['Watch video summaries', 'Use mind maps', 'Review diagrams'],
            'auditory': ['Listen to recorded lectures', 'Join study groups', 'Use text-to-speech'],
            'reading': ['Read module summaries', 'Take structured notes', 'Use flashcards'],
            'kinesthetic': ['Hands-on practice problems', 'Build mini-projects', 'Interactive simulations']
        }

        st.info(f"Path Type: **{path_type}**")
        st.markdown("**Personalized tips based on your learning style:**")
        for tip in style_tips.get(learning_style, []):
            st.markdown(f"- {tip}")

# ================================================
# PAGE 4: LEARNING PATHS
# ================================================
elif page == "Learning Paths":
    st.title("Generated Learning Paths")
    st.markdown("*All AI-generated intervention plans*")
    st.markdown("---")

    try:
        with open('learning_paths.json') as f:
            paths = json.load(f)

        st.metric("Total Paths Generated", len(paths))
        st.markdown("---")

        for path in paths:
            with st.expander(
                f"Student {path['student_name']} — {path['path_type']} "
                f"(Risk: {path['dropout_probability']})"
            ):
                col1, col2 = st.columns(2)
                col1.markdown(f"**Course:** {path['course']}")
                col1.markdown(f"**Status:** {path['urgency']}")
                col1.markdown(f"**Weekly Goal:** {path['weekly_goal']}")
                col2.markdown(f"**Recommended Modules:** {path['recommended_modules']}")
                col2.markdown("**Learning Tips:**")
                for tip in path['learning_tips']:
                    col2.markdown(f"- {tip}")
    except:
        st.warning("Run path_engine.py first to generate learning paths.")