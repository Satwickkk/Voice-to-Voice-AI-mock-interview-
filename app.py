"""
Main Streamlit application for AI Voice-to-Voice Mock Interview System
"""

import streamlit as st
import time
import threading
import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from interview_engine import InterviewEngine
from config import STREAMLIT_THEME, INTERVIEW_TYPES, DEFAULT_QUESTIONS

# Page configuration
st.set_page_config(
    page_title="AI Voice-to-Voice Mock Interview",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #FF6B6B;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .sub-header {
        font-size: 1.5rem;
        color: #4A90E2;
        margin-bottom: 1rem;
    }
    
    .status-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #FF6B6B;
        margin: 1rem 0;
    }
    
    .metric-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .progress-container {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .button-container {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin: 1rem 0;
    }
    
    .stButton > button {
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .start-button > button {
        background-color: #FF6B6B;
        color: white;
    }
    
    .stop-button > button {
        background-color: #E74C3C;
        color: white;
    }
    
    .pause-button > button {
        background-color: #F39C12;
        color: white;
    }
    
    .resume-button > button {
        background-color: #27AE60;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'interview_engine' not in st.session_state:
    st.session_state.interview_engine = InterviewEngine()
    st.session_state.interview_active = False
    st.session_state.current_status = "Ready to start"
    st.session_state.progress = 0
    st.session_state.session_data = None

# Initialize default values for interview settings
if 'num_questions' not in st.session_state:
    st.session_state.num_questions = DEFAULT_QUESTIONS
if 'selected_position' not in st.session_state:
    st.session_state.selected_position = "General"

def update_status(message: str):
    """Update status message"""
    st.session_state.current_status = message
    print(f"Status: {message}")

def update_progress(progress: float):
    """Update progress percentage"""
    st.session_state.progress = progress

def interview_completed_callback():
    """Callback when interview completes"""
    st.session_state.interview_active = False
    st.session_state.current_status = "Interview completed! Loading results..."
    # Load session data automatically
    load_session_results()
    st.session_state.current_status = "Interview completed! Results loaded."
    
    # Show completion message
    st.success("🎉 Interview completed! Check the detailed analysis below for your results.")

def start_interview():
    """Start interview function"""
    try:
        st.session_state.current_status = "Starting interview..."
        st.session_state.progress = 0
        st.session_state.session_data = None  # Reset session data
        
        # Get settings from session state
        position = st.session_state.get("selected_position", "General")
        num_questions = st.session_state.get("num_questions", DEFAULT_QUESTIONS)
        
        # Debug logging
        print(f"DEBUG: Starting interview with position={position}, num_questions={num_questions}")
        print(f"DEBUG: DEFAULT_QUESTIONS={DEFAULT_QUESTIONS}")
        print(f"DEBUG: Session state num_questions={st.session_state.get('num_questions')}")
        
        # Ensure we have a valid number of questions
        if not num_questions or num_questions < 1:
            num_questions = DEFAULT_QUESTIONS
            print(f"DEBUG: Using default questions: {num_questions}")
        
        # Start interview in a separate thread
        def run_interview():
            try:
                # Start the interview engine first
                st.session_state.interview_engine.start_interview(
                    position=position,
                    num_questions=num_questions,
                    status_callback=update_status,
                    progress_callback=update_progress
                )
                # Call completion callback when interview ends
                interview_completed_callback()
            except Exception as e:
                st.session_state.current_status = f"Interview error: {str(e)}"
                st.session_state.interview_active = False
        
        # Start interview thread
        interview_thread = threading.Thread(target=run_interview)
        interview_thread.start()
        
        # Wait a moment for the interview to initialize, then set active
        time.sleep(0.5)
        st.session_state.interview_active = True
        
    except Exception as e:
        st.session_state.current_status = f"Error starting interview: {str(e)}"
        st.session_state.interview_active = False

def stop_interview():
    """Stop interview function"""
    st.session_state.interview_engine.stop_interview()
    st.session_state.interview_active = False
    update_status("Interview stopped")

def pause_interview():
    """Pause interview function"""
    st.session_state.interview_engine.pause_interview()
    update_status("Interview paused")

def resume_interview():
    """Resume interview function"""
    st.session_state.interview_engine.resume_interview()
    update_status("Interview resumed")

def load_session_results():
    """Load and display session results"""
    try:
        if st.session_state.interview_engine:
            session_data = st.session_state.interview_engine.get_session_data()
            if session_data:
                st.session_state.session_data = session_data
                return True
    except Exception as e:
        st.error(f"Error loading session data: {e}")
    return False

def display_results():
    """Display interview results"""
    if not st.session_state.session_data:
        if not load_session_results():
            return
    
    data = st.session_state.session_data
    
    # Display overall score prominently
    overall_score = data.get("overall_score", 0)
    
    st.markdown("---")
    st.markdown('<h2 class="sub-header">🏆 Interview Results</h2>', unsafe_allow_html=True)
    
    # Overall score display
    col_score1, col_score2, col_score3 = st.columns([1, 2, 1])
    
    with col_score2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Overall Score</h3>
            <h1 style="color: #FF6B6B; font-size: 3rem;">{overall_score:.1f}/100</h1>
        </div>
        """, unsafe_allow_html=True)
    
    # Session info
    session_info = data.get("session_info", {})
    if session_info:
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.metric("Position", session_info.get("position", "N/A"))
        with col_info2:
            st.metric("Questions", session_info.get("total_questions", 0))
        with col_info3:
            duration = session_info.get("duration", 0)
            st.metric("Duration", f"{duration:.1f} min")
    
    # Download reports
    st.markdown("### 📄 Download Reports")
    col_download1, col_download2 = st.columns(2)
    
    with col_download1:
        if st.button("📊 Download PDF Report", use_container_width=True):
            try:
                # Generate PDF report
                pdf_path = st.session_state.interview_engine.report_generator.generate_interview_report(data)
                with open(pdf_path, "rb") as file:
                    st.download_button(
                        label="📥 Download PDF",
                        data=file.read(),
                        file_name=f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Error generating PDF: {e}")
    
    with col_download2:
        if st.button("📝 Download Text Report", use_container_width=True):
            try:
                # Generate text report
                text_path = st.session_state.interview_engine.report_generator.generate_simple_report(data)
                with open(text_path, "r") as file:
                    st.download_button(
                        label="📥 Download Text",
                        data=file.read(),
                        file_name=f"interview_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Error generating text report: {e}")

# Main application
def main():
    # Header
    st.markdown('<h1 class="main-header">🎤 AI Voice-to-Voice Mock Interview</h1>', unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("### ⚙️ Interview Settings")
        
        # Position selection
        positions = st.session_state.interview_engine.get_available_positions()
        selected_position = st.selectbox(
            "Select Position:",
            positions,
            key="selected_position"
        )
        
        # Number of questions
        num_questions = st.slider(
            "Number of Questions:",
            min_value=1,
            max_value=10,
            value=DEFAULT_QUESTIONS,
            key="num_questions"
        )
        
        # Question type info
        question_type = INTERVIEW_TYPES.get(selected_position, "mixed")
        st.info(f"**Question Type:** {question_type.title()}")
        
        st.markdown("---")
        
        # API Status
        st.markdown("### 🔑 API Status")
        openai_status = "✅ Configured" if os.getenv("OPENAI_API_KEY") else "❌ Not configured"
        google_status = "✅ Configured" if os.getenv("GOOGLE_API_KEY") else "❌ Not configured"
        
        st.write(f"OpenAI: {openai_status}")
        st.write(f"Google Gemini: {google_status}")
        
        if not os.getenv("OPENAI_API_KEY") or not os.getenv("GOOGLE_API_KEY"):
            st.warning("Please configure your API keys in the .env file")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Interview control section
        st.markdown('<h2 class="sub-header">🎯 Interview Control</h2>', unsafe_allow_html=True)
        
        # Status display
        st.markdown(f"""
        <div class="status-box">
            <strong>Status:</strong> {st.session_state.current_status}
        </div>
        """, unsafe_allow_html=True)
        
        # Debug info for question count
        if st.session_state.interview_active and st.session_state.interview_engine:
            try:
                status = st.session_state.interview_engine.get_interview_status()
                st.info(f"**Debug Info:** Question {status.get('current_question', 0)} of {status.get('total_questions', 0)} | Active: {st.session_state.interview_active}")
            except:
                pass
        
        # Progress bar
        if st.session_state.interview_active:
            st.markdown('<div class="progress-container">', unsafe_allow_html=True)
            st.progress(st.session_state.progress / 100)
            st.write(f"Progress: {st.session_state.progress:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Control buttons
        col1_1, col1_2, col1_3, col1_4 = st.columns(4)
        
        with col1_1:
            if not st.session_state.interview_active:
                if st.button("🚀 Start Interview", key="start", use_container_width=True):
                    start_interview()
        
        with col1_2:
            if st.session_state.interview_active:
                if st.button("⏹️ Stop", key="stop", use_container_width=True):
                    stop_interview()
        
        with col1_3:
            if st.session_state.interview_active:
                if st.button("⏸️ Pause", key="pause", use_container_width=True):
                    pause_interview()
        
        with col1_4:
            if st.session_state.interview_active:
                if st.button("▶️ Resume", key="resume", use_container_width=True):
                    resume_interview()
        
        # Add Next Question button for better control
        if st.session_state.interview_active:
            if st.button("⏭️ Next Question", key="next_question", use_container_width=True):
                # Manually trigger next question
                try:
                    # This will advance to the next question
                    st.session_state.interview_engine._ask_current_question()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error advancing to next question: {e}")
        
        # Add Voice Answer section
        if st.session_state.interview_active:
            st.markdown("### 🎤 Voice Answer")
            
            # Voice recording controls
            col_record1, col_record2, col_record3 = st.columns(3)
            
            with col_record1:
                if not st.session_state.get('is_recording', False):
                    if st.button("🎙️ Start Recording", key="start_recording", use_container_width=True):
                        st.session_state.is_recording = True
                        st.session_state.recording_start_time = time.time()
                        # Start recording
                        st.session_state.interview_engine.start_voice_recording()
                        st.rerun()
                else:
                    if st.button("⏹️ Stop Recording", key="stop_recording", use_container_width=True):
                        st.session_state.is_recording = False
                        # Stop recording and process
                        audio_file = st.session_state.interview_engine.stop_voice_recording()
                        if audio_file:
                            st.session_state.current_audio_file = audio_file
                            st.success("Voice recorded successfully! Click 'Submit Answer' to continue.")
                        st.rerun()
            
            with col_record2:
                if st.session_state.get('is_recording', False):
                    # Show recording status
                    recording_time = time.time() - st.session_state.get('recording_start_time', 0)
                    st.write(f"Recording: {recording_time:.1f}s")
                else:
                    st.write("Click to record")
            
            with col_record3:
                if st.session_state.get('current_audio_file'):
                    if st.button("📝 Submit Voice Answer", key="submit_voice", use_container_width=True):
                        # Process the voice answer
                        st.session_state.interview_engine.submit_voice_answer(st.session_state.current_audio_file)
                        st.session_state.current_audio_file = None
                        st.rerun()
            
            # Show recording instructions
            if not st.session_state.get('is_recording', False):
                st.info("🎤 **Instructions:** Click 'Start Recording' to begin speaking your answer. Click 'Stop Recording' when finished, then 'Submit Voice Answer' to continue.")
            
            # Alternative text input (fallback)
            st.markdown("### 💬 Text Answer (Alternative)")
            user_answer = st.text_area(
                "Or type your answer here:",
                key="user_answer_input",
                height=100,
                placeholder="Enter your answer if voice recording doesn't work..."
            )
            
            if st.button("📝 Submit Text Answer", key="submit_text", use_container_width=True):
                if user_answer and user_answer.strip():
                    st.session_state.interview_engine.submit_user_answer(user_answer.strip())
                    st.session_state.user_answer_input = ""
                    st.rerun()
                else:
                    st.error("Please enter your answer before submitting.")
        
        # Interview status
        if st.session_state.interview_active:
            # Check if interview is ready to display status
            if st.session_state.interview_engine.is_ready_for_status_display():
                status = st.session_state.interview_engine.get_interview_status()
                
                st.markdown('<h3>📊 Interview Status</h3>', unsafe_allow_html=True)
                
                col_status1, col_status2, col_status3 = st.columns(3)
                
                with col_status1:
                    st.metric("Current Question", f"{status['current_question']}/{status['total_questions']}")
                
                with col_status2:
                    st.metric("Position", status['position'])
                
                with col_status3:
                    session_id_display = status['session_id'][:8] + "..." if status['session_id'] else "Not started"
                    st.metric("Session ID", session_id_display)
                
                # Show current question
                current_question = st.session_state.interview_engine._generate_question()
                if current_question:
                    st.markdown("### 🎤 Current Question")
                    st.write(f"**{current_question}**")
                
                # Show latest Q&A if available
                if st.session_state.interview_engine.conversation_history:
                    latest_exchange = st.session_state.interview_engine.conversation_history[-1]
                    latest_question = latest_exchange.get('question', '')
                    latest_answer = latest_exchange.get('answer', '')
                    
                    if latest_answer:
                        st.markdown("### 💬 Your Answer")
                        st.write(latest_answer)
                        
                        # Show content evaluation if available
                        evaluation = latest_exchange.get('content_evaluation', {})
                        if evaluation:
                            st.markdown("### 📊 Content Evaluation")
                            col_eval1, col_eval2, col_eval3, col_eval4 = st.columns(4)
                            with col_eval1:
                                st.metric("Relevance", f"{evaluation.get('relevance_score', 0):.1f}")
                            with col_eval2:
                                st.metric("Specificity", f"{evaluation.get('specificity_score', 0):.1f}")
                            with col_eval3:
                                st.metric("Professionalism", f"{evaluation.get('professionalism_score', 0):.1f}")
                            with col_eval4:
                                st.metric("Overall", f"{evaluation.get('overall_score', 0):.1f}")
                            
                            # Show feedback
                            if evaluation.get('feedback'):
                                st.info(f"💡 **Content Feedback:** {evaluation['feedback']}")
                        
                        # Show speech analysis if available
                        speech_analysis = latest_exchange.get('speech_analysis', {})
                        if speech_analysis:
                            st.markdown("### 🎤 Speech Analysis")
                            col_speech1, col_speech2, col_speech3, col_speech4 = st.columns(4)
                            with col_speech1:
                                st.metric("Confidence", f"{speech_analysis.get('confidence_score', 0):.1f}")
                            with col_speech2:
                                st.metric("Pace", f"{speech_analysis.get('pace_score', 0):.1f}")
                            with col_speech3:
                                st.metric("Vocabulary", f"{speech_analysis.get('vocabulary_score', 0):.1f}")
                            with col_speech4:
                                st.metric("Overall Speech", f"{speech_analysis.get('overall_speech_score', 0):.1f}")
                            
                            # Show speech feedback
                            if speech_analysis.get('feedback'):
                                st.info(f"🎤 **Speech Feedback:** {speech_analysis['feedback']}")
            else:
                st.markdown('<h3>📊 Interview Status</h3>', unsafe_allow_html=True)
                st.info("Initializing interview... Please wait.")
    
    # Quick stats section
    with col2:
        st.markdown('<h2 class="sub-header">📈 Quick Stats</h2>', unsafe_allow_html=True)
        
        # Load session data if available
        if not st.session_state.session_data:
            if st.button("📊 Load Results", use_container_width=True):
                load_session_results()
        
        # Display results if available
        if st.session_state.session_data:
            display_results()
        
        # Show basic stats
        if st.session_state.interview_active:
            # Check if interview is ready to display stats
            if st.session_state.interview_engine.is_ready_for_status_display():
                status = st.session_state.interview_engine.get_interview_status()
                
                col_stats1, col_stats2 = st.columns(2)
                
                with col_stats1:
                    st.metric("Questions Completed", status['conversation_count'])
                
                with col_stats2:
                    st.metric("Progress", f"{st.session_state.progress:.1f}%")
            else:
                st.info("Interview is starting... Stats will appear shortly.")
        
        # Check if interview is completed and show results
        elif st.session_state.interview_engine.is_interview_completed():
            st.success("🎉 Interview completed! Loading results...")
            if not st.session_state.session_data:
                load_session_results()
            if st.session_state.session_data:
                display_results()
    
    # Display detailed analysis if session data is available
    if st.session_state.session_data:
        st.markdown("---")
        st.markdown('<h2 class="sub-header">📊 Detailed Analysis</h2>', unsafe_allow_html=True)
        
        data = st.session_state.session_data
        
        # Create tabs for different analysis views
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Performance Metrics", "🎤 Speech Analysis", "💬 Conversation", "📋 Summary"])
        
        with tab1:
            # Performance metrics
            col_metrics1, col_metrics2 = st.columns(2)
            
            with col_metrics1:
                # Overall score chart
                overall_score = data.get("overall_score", 0)
                fig_score = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=overall_score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Overall Score"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#FF6B6B"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "lightgreen"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                fig_score.update_layout(height=300)
                st.plotly_chart(fig_score, use_container_width=True)
            
            with col_metrics2:
                # Content analysis scores
                content_analysis = data.get("content_analysis", [])
                if content_analysis:
                    scores_data = []
                    for i, analysis in enumerate(content_analysis):
                        scores_data.append({
                            "Question": f"Q{i+1}",
                            "Relevance": analysis.get("relevance_score", 0),
                            "Specificity": analysis.get("specificity_score", 0),
                            "Professionalism": analysis.get("professionalism_score", 0),
                            "Overall": analysis.get("overall_score", 0)
                        })
                    
                    df_scores = pd.DataFrame(scores_data)
                    
                    fig_scores = px.bar(df_scores, x="Question", y=["Relevance", "Specificity", "Professionalism", "Overall"],
                                      title="Answer Quality Scores", barmode='group')
                    fig_scores.update_layout(height=300)
                    st.plotly_chart(fig_scores, use_container_width=True)
        
        with tab2:
            # Speech analysis
            speech_analysis = data.get("speech_analysis", [])
            if speech_analysis:
                col_speech1, col_speech2 = st.columns(2)
                
                with col_speech1:
                    # Confidence scores over time
                    confidence_scores = [analysis.get("confidence_score", 0) for analysis in speech_analysis]
                    questions = [f"Q{i+1}" for i in range(len(confidence_scores))]
                    
                    fig_confidence = px.line(x=questions, y=confidence_scores, 
                                           title="Confidence Score Progression",
                                           markers=True)
                    fig_confidence.update_layout(height=300)
                    st.plotly_chart(fig_confidence, use_container_width=True)
                
                with col_speech2:
                    # Speech metrics radar chart
                    if speech_analysis:
                        latest_analysis = speech_analysis[-1]
                        
                        categories = ['Pitch Stability', 'Speaking Rate', 'Energy Consistency', 'Pause Usage', 'Clarity']
                        values = [
                            latest_analysis.get("pitch", {}).get("pitch_stability", 0),
                            latest_analysis.get("tempo", {}).get("tempo_score", 0) * 100,
                            latest_analysis.get("energy", {}).get("energy_consistency", 0),
                            latest_analysis.get("pauses", {}).get("pause_score", 0) * 100,
                            latest_analysis.get("clarity", {}).get("clarity_score", 0) * 100
                        ]
                        
                        fig_radar = go.Figure()
                        fig_radar.add_trace(go.Scatterpolar(
                            r=values,
                            theta=categories,
                            fill='toself',
                            name='Speech Metrics'
                        ))
                        fig_radar.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 100]
                                )),
                            showlegend=False,
                            height=300
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)
        
        with tab3:
            # Conversation transcript
            conversation = data.get("conversation_history", [])
            if conversation:
                for i, exchange in enumerate(conversation):
                    with st.expander(f"Question {i+1}: {exchange.get('question', '')[:50]}..."):
                        st.write(f"**Question:** {exchange.get('question', '')}")
                        st.write(f"**Answer:** {exchange.get('answer', '')}")
                        
                        # Show scores
                        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
                        with col_q1:
                            st.metric("Relevance", f"{exchange.get('content_evaluation', {}).get('relevance_score', 0):.1f}")
                        with col_q2:
                            st.metric("Specificity", f"{exchange.get('content_evaluation', {}).get('specificity_score', 0):.1f}")
                        with col_q3:
                            st.metric("Professionalism", f"{exchange.get('content_evaluation', {}).get('professionalism_score', 0):.1f}")
                        with col_q4:
                            st.metric("Overall", f"{exchange.get('content_evaluation', {}).get('overall_score', 0):.1f}")
        
        with tab4:
            # Summary and recommendations
            summary = data.get("summary", {})
            
            col_summary1, col_summary2 = st.columns(2)
            
            with col_summary1:
                st.markdown("### 📋 Overall Assessment")
                st.write(f"**Overall Impression:** {summary.get('overall_impression', 'N/A')}")
                st.write(f"**Readiness Level:** {summary.get('readiness_level', 'N/A')}")
                
                st.markdown("### ✅ Key Strengths")
                strengths = summary.get("key_strengths", [])
                if strengths:
                    for strength in strengths:
                        st.write(f"• {strength}")
                else:
                    st.write("No specific strengths identified.")
            
            with col_summary2:
                st.markdown("### 🔧 Areas for Improvement")
                improvements = summary.get("improvement_areas", [])
                if improvements:
                    for improvement in improvements:
                        st.write(f"• {improvement}")
                else:
                    st.write("No specific improvements identified.")
                
                st.markdown("### 💡 Recommendations")
                recommendations = summary.get("recommendations", [])
                if recommendations:
                    for i, rec in enumerate(recommendations, 1):
                        st.write(f"{i}. {rec}")
                else:
                    st.write("No specific recommendations available.")
    
    # Auto-refresh for active interviews (disabled for now to prevent issues)
    # if st.session_state.interview_active:
    #     time.sleep(1)
    #     st.rerun()

if __name__ == "__main__":
    main()
