"""
Core interview engine that orchestrates the entire interview process
"""

import time
import threading
from typing import Dict, List, Optional, Callable
from datetime import datetime
from gtts import gTTS
import pyttsx3
import os

from audio_processor import AudioProcessor, AudioPlayer
from speech_analyzer import SpeechAnalyzer
from ai_interface import AIInterface
from report_generator import ReportGenerator
from utils import generate_session_id, save_interview_data, load_interview_data, cleanup_temp_files
from config import INTERVIEW_TYPES, DEFAULT_QUESTIONS

class InterviewEngine:
    """
    Main interview engine that coordinates all components
    """
    
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.audio_player = AudioPlayer()
        self.speech_analyzer = SpeechAnalyzer()
        self.ai_interface = AIInterface()
        self.report_generator = ReportGenerator()
        
        # Session state
        self.session_id = None
        self.is_interview_active = False
        self.current_question = 0
        self.total_questions = DEFAULT_QUESTIONS
        self.position = "General"
        self.question_type = "mixed"
        
        # Data storage
        self.conversation_history = []
        self.speech_analysis = []
        self.content_analysis = []
        self.session_start_time = None
        
        # Callbacks
        self.status_callback = None
        self.progress_callback = None
        
    def start_interview(self, position: str = "General", num_questions: int = None,
                       status_callback: Callable = None, progress_callback: Callable = None):
        """
        Start a new interview session
        
        Args:
            position: Job position
            num_questions: Number of questions to ask
            status_callback: Callback for status updates
            progress_callback: Callback for progress updates
        """
        # Initialize session
        self.session_id = generate_session_id()
        self.is_interview_active = True
        self.current_question = 0
        self.total_questions = num_questions or DEFAULT_QUESTIONS
        self.position = position
        self.question_type = INTERVIEW_TYPES.get(position, "mixed")
        
        # Reset data
        self.conversation_history = []
        self.speech_analysis = []
        self.content_analysis = []
        self.session_start_time = time.time()  # Ensure this is always set
        
        # Set callbacks
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        
        # Update status
        self._update_status("Interview started")
        print(f"DEBUG: Interview started - total_questions={self.total_questions}, current_question={self.current_question}")
        print(f"DEBUG: Session start time: {self.session_start_time}")
        
        # Give initial instructions
        self._give_instructions()
        
        # Ask first question
        self._ask_current_question()
    
    def _give_instructions(self):
        """Give initial interview instructions"""
        instructions = f"""
        Welcome to your mock interview for {self.position} position!
        
        Here's how this works:
        1. I will ask you {self.total_questions} questions
        2. For each question, type your answer in the text box
        3. Click 'Submit Answer' when you're done
        4. Click 'Next Question' to move to the next question
        5. After all questions, I'll analyze your answers and give you a detailed report
        
        Let's begin with the first question!
        """
        self._speak_message(instructions)
        self._update_status("Instructions given - ready for first question")
    
    def _ask_current_question(self):
        """Ask the current question"""
        print(f"DEBUG: current_question={self.current_question}, total_questions={self.total_questions}")
        if self.current_question < self.total_questions:
            question = self._generate_question()
            if question:
                # Display question number as 1-based for user
                question_number = self.current_question + 1
                self._speak_message(f"Question {question_number}: {question}")
                self._update_status(f"Question {question_number} asked - waiting for answer")
            else:
                # No more questions available, end interview
                self._update_status("No more questions available, ending interview")
                self._end_interview()
        else:
            # All questions completed
            self._end_interview()
                
    def start_voice_recording(self):
        """Start recording voice answer"""
        try:
            self._update_status("Starting voice recording...")
            self.audio_processor.start_recording()
            self._update_status("Voice recording started - speak your answer")
        except Exception as e:
            self._update_status(f"Error starting recording: {str(e)}")
    
    def stop_voice_recording(self) -> Optional[str]:
        """Stop recording and return audio file path"""
        try:
            self._update_status("Stopping voice recording...")
            audio_file = self.audio_processor.stop_recording()
            if audio_file:
                self._update_status("Voice recording completed")
                return audio_file
            else:
                self._update_status("No audio recorded")
                return None
        except Exception as e:
            self._update_status(f"Error stopping recording: {str(e)}")
            return None
    
    def submit_voice_answer(self, audio_file: str):
        """Submit voice answer and analyze it"""
        try:
            # Check if interview is already completed
            if self.current_question >= self.total_questions:
                self._update_status("Interview already completed")
                return
            
            # Get current question
            current_question = self._generate_question()
            if not current_question:
                self._update_status("Interview completed - no more questions")
                self._end_interview()
                return
            
            # Transcribe audio to text
            transcript = self._transcribe_audio(audio_file)
            if not transcript:
                self._update_status("Failed to transcribe audio")
                return
            
            # Analyze speech patterns
            speech_analysis = self._analyze_speech(audio_file, transcript)
            
            # Analyze content
            content_evaluation = self._analyze_answer(current_question, transcript)
            
            # Store the Q&A exchange with speech analysis
            exchange_data = {
                "question": current_question,
                "answer": transcript,
                "audio_file": audio_file,
                "speech_analysis": speech_analysis,
                "content_evaluation": content_evaluation,
                "timestamp": datetime.now().isoformat()
            }
            
            self.conversation_history.append(exchange_data)
            self.speech_analysis.append(speech_analysis)
            self.content_analysis.append(content_evaluation)
            
            # Update progress
            self._update_progress()
            
            # Move to next question
            self.current_question += 1
            print(f"DEBUG: Moved to next question - current_question={self.current_question}, total_questions={self.total_questions}")
            
            # Check if we've completed all questions
            if self.current_question >= self.total_questions:
                # All questions completed
                print(f"DEBUG: All questions completed, ending interview")
                self._end_interview()
            else:
                # Ask next question
                print(f"DEBUG: Asking next question - current_question={self.current_question}")
                self._ask_current_question()
                
            # Always check completion to ensure proper ending
            self._ensure_interview_completion()
                
        except Exception as e:
            self._update_status(f"Error submitting voice answer: {str(e)}")
    
    def submit_user_answer(self, answer_text: str):
        """Submit text answer (fallback method)"""
        try:
            # Check if interview is already completed
            if self.current_question >= self.total_questions:
                self._update_status("Interview already completed")
                return
            
            # Get current question
            current_question = self._generate_question()
            if not current_question:
                self._update_status("Interview completed - no more questions")
                self._end_interview()
                return
            
            # Analyze the user's answer
            content_evaluation = self._analyze_answer(current_question, answer_text)
            
            # Store the Q&A exchange
            exchange_data = {
                "question": current_question,
                "answer": answer_text,
                "content_evaluation": content_evaluation,
                "timestamp": datetime.now().isoformat()
            }
            
            self.conversation_history.append(exchange_data)
            self.content_analysis.append(content_evaluation)
            
            # Update progress
            self._update_progress()
            
            # Move to next question
            self.current_question += 1
            print(f"DEBUG: Moved to next question - current_question={self.current_question}, total_questions={self.total_questions}")
            
            # Check if we've completed all questions
            if self.current_question >= self.total_questions:
                # All questions completed
                print(f"DEBUG: All questions completed, ending interview")
                self._end_interview()
            else:
                # Ask next question
                print(f"DEBUG: Asking next question - current_question={self.current_question}")
                self._ask_current_question()
                
            # Always check completion to ensure proper ending
            self._ensure_interview_completion()
                
        except Exception as e:
            self._update_status(f"Error submitting answer: {str(e)}")
    
    def _transcribe_audio(self, audio_file: str) -> Optional[str]:
        """Transcribe audio file to text"""
        try:
            # For now, use a simple simulation since we need API keys
            # In production, this would use OpenAI Whisper or Google Speech-to-Text
            
            # Simulate transcription delay
            time.sleep(1)
            
            # Return a simulated transcript for demonstration
            # In production, this would be the actual transcribed text
            simulated_transcripts = [
                "I have a strong background in software development with over 5 years of experience.",
                "My greatest strength is my ability to solve complex problems and work well in teams.",
                "I'm interested in this position because it aligns with my career goals and technical skills.",
                "In 5 years, I see myself leading development teams and contributing to innovative projects.",
                "I once faced a challenging project deadline and solved it by prioritizing tasks and collaborating effectively."
            ]
            
            # Use the current question index to get a relevant transcript
            if self.current_question < len(simulated_transcripts):
                transcript = simulated_transcripts[self.current_question]
            else:
                transcript = "This is a simulated transcript for demonstration purposes."
            
            self._update_status(f"Audio transcribed: {transcript[:50]}...")
            return transcript
            
        except Exception as e:
            self._update_status(f"Transcription error: {str(e)}")
            return None
    
    def _analyze_speech(self, audio_file: str, transcript: str) -> Dict:
        """Analyze speech patterns from audio file"""
        try:
            # For now, use simulated speech analysis
            # In production, this would use librosa and other audio analysis libraries
            
            # Simulate speech analysis based on transcript length and content
            speech_score = 0
            speech_feedback = []
            
            # Analyze speaking pace (based on transcript length)
            if len(transcript) > 100:
                pace_score = 85  # Good pace
                speech_feedback.append("Good speaking pace")
            elif len(transcript) > 50:
                pace_score = 75  # Moderate pace
                speech_feedback.append("Moderate speaking pace")
            else:
                pace_score = 60  # Fast pace
                speech_feedback.append("Consider slowing down for clarity")
            
            # Analyze vocabulary complexity
            complex_words = ['experience', 'development', 'collaboration', 'innovation', 'leadership']
            vocab_score = 70
            if any(word in transcript.lower() for word in complex_words):
                vocab_score = 85
                speech_feedback.append("Good vocabulary usage")
            else:
                speech_feedback.append("Consider using more professional vocabulary")
            
            # Analyze confidence indicators
            confidence_words = ['confident', 'believe', 'know', 'can', 'will', 'achieve']
            confidence_score = 70
            if any(word in transcript.lower() for word in confidence_words):
                confidence_score = 85
                speech_feedback.append("Shows confidence in speech")
            else:
                speech_feedback.append("Work on expressing more confidence")
            
            # Calculate overall speech score
            overall_speech_score = (pace_score + vocab_score + confidence_score) / 3
            
            return {
                "confidence_score": confidence_score,
                "pace_score": pace_score,
                "vocabulary_score": vocab_score,
                "overall_speech_score": overall_speech_score,
                "feedback": " ".join(speech_feedback),
                "pitch": {"pitch_stability": 80.0},
                "tempo": {"tempo_score": 0.8},
                "energy": {"energy_consistency": 85.0},
                "pauses": {"pause_score": 0.7},
                "clarity": {"clarity_score": 0.9}
            }
            
        except Exception as e:
            self._update_status(f"Speech analysis error: {str(e)}")
            return {
                "confidence_score": 0,
                "pace_score": 0,
                "vocabulary_score": 0,
                "overall_speech_score": 0,
                "feedback": "Speech analysis failed",
                "pitch": {"pitch_stability": 0},
                "tempo": {"tempo_score": 0},
                "energy": {"energy_consistency": 0},
                "pauses": {"pause_score": 0},
                "clarity": {"clarity_score": 0}
            }
    
    def _analyze_answer(self, question: str, answer: str) -> Dict:
        """Analyze the user's answer and provide evaluation"""
        try:
            # For now, use a simple scoring algorithm
            # In production, this would use AI to analyze the answer
            
            score = 0
            strengths = []
            improvements = []
            
            # Basic scoring based on answer length and content
            if len(answer) > 50:
                score += 20
                strengths.append("Good answer length")
            elif len(answer) > 20:
                score += 10
                strengths.append("Adequate answer length")
            else:
                improvements.append("Consider providing more detailed answers")
            
            # Check for professional language
            professional_words = ['experience', 'skills', 'professional', 'team', 'leadership', 'project', 'results']
            if any(word in answer.lower() for word in professional_words):
                score += 15
                strengths.append("Professional language used")
            else:
                improvements.append("Use more professional language")
            
            # Check for specific examples
            if any(word in answer.lower() for word in ['example', 'instance', 'time when', 'situation']):
                score += 15
                strengths.append("Provided specific examples")
            else:
                improvements.append("Include specific examples in your answers")
            
            # Check for confidence indicators
            confidence_words = ['confident', 'believe', 'know', 'can', 'will', 'achieve']
            if any(word in answer.lower() for word in confidence_words):
                score += 10
                strengths.append("Shows confidence")
            else:
                improvements.append("Express more confidence in your abilities")
            
            # Ensure score is within 0-100 range
            score = max(0, min(100, score))
            
            # Calculate individual scores
            relevance_score = min(100, score + 10)  # Slightly higher for relevance
            specificity_score = min(100, score + 5)  # Based on examples
            professionalism_score = min(100, score + 15)  # Based on language
            
            return {
                "relevance_score": relevance_score,
                "specificity_score": specificity_score,
                "professionalism_score": professionalism_score,
                "overall_score": score,
                "strengths": strengths,
                "improvements": improvements,
                "feedback": f"Your answer scored {score}/100. {' '.join(strengths)}. {' '.join(improvements)}"
            }
            
        except Exception as e:
            self._update_status(f"Answer analysis error: {str(e)}")
            return {
                "relevance_score": 0,
                "specificity_score": 0,
                "professionalism_score": 0,
                "overall_score": 0,
                "strengths": ["Analysis failed"],
                "improvements": ["Please try again"],
                "feedback": "Unable to analyze answer"
            }
    
    # Removed _conduct_question_round method - no longer needed
    
    def _generate_question(self) -> str:
        """Generate interview question using AI APIs"""
        try:
            print(f"DEBUG: Generating question for current_question={self.current_question}, total_questions={self.total_questions}")
            
            # Check if we've reached the total questions limit
            if self.current_question >= self.total_questions:
                print(f"DEBUG: Reached question limit, returning None")
                return None  # Return None to indicate interview is complete
            
            # Add randomness to question selection
            self._add_randomness_to_questions()
            
            # Try to use AI to generate questions first
            ai_question = self._generate_ai_question()
            if ai_question:
                print(f"DEBUG: AI generated question: {ai_question[:50]}...")
                return ai_question
            
            # Fallback to predefined questions if AI fails
            fallback_question = self._get_fallback_question()
            if fallback_question:
                print(f"DEBUG: Using fallback question: {fallback_question[:50]}...")
                return fallback_question
            
            # Last resort generic question - ensure we always return something
            generic_questions = [
                "Please provide additional information about your experience and qualifications.",
                "Can you tell me more about your background?",
                "What else would you like me to know about you?",
                "Is there anything else you'd like to share?",
                "Do you have any additional experience to discuss?"
            ]
            generic_question = generic_questions[self.current_question % len(generic_questions)]
            print(f"DEBUG: Using generic question: {generic_question}")
            return generic_question
            
        except Exception as e:
            self._update_status(f"Question generation error: {str(e)}")
            print(f"DEBUG: Question generation failed, using emergency fallback")
            # Emergency fallback - always return a question
            emergency_questions = [
                "Tell me about yourself.",
                "What are your strengths?",
                "Why are you interested in this role?",
                "Where do you see yourself in the future?",
                "Describe a challenging situation."
            ]
            return emergency_questions[self.current_question % len(emergency_questions)]
    
    def _generate_ai_question(self) -> str:
        """Generate question using AI APIs"""
        try:
            # Try OpenAI first
            if hasattr(self, '_openai_client') or self._try_init_openai():
                return self._generate_openai_question()
            
            # Try Google Gemini if OpenAI fails
            if hasattr(self, '_gemini_client') or self._try_init_gemini():
                return self._generate_gemini_question()
            
            return None
            
        except Exception as e:
            print(f"DEBUG: AI question generation failed: {str(e)}")
            return None
    
    def _try_init_openai(self) -> bool:
        """Try to initialize OpenAI client"""
        try:
            from openai import OpenAI
            from config import OPENAI_API_KEY
            
            if OPENAI_API_KEY:
                self._openai_client = OpenAI(api_key=OPENAI_API_KEY)
                print("DEBUG: OpenAI client initialized successfully")
                return True
            else:
                print("DEBUG: OpenAI API key not found")
                return False
        except Exception as e:
            print(f"DEBUG: Failed to initialize OpenAI: {str(e)}")
            return False
    
    def _try_init_gemini(self) -> bool:
        """Try to initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            from config import GOOGLE_API_KEY
            
            if GOOGLE_API_KEY:
                genai.configure(api_key=GOOGLE_API_KEY)
                self._gemini_client = genai.GenerativeModel('gemini-pro')
                print("DEBUG: Gemini client initialized successfully")
                return True
            else:
                print("DEBUG: Google API key not found")
                return False
        except Exception as e:
            print(f"DEBUG: Failed to initialize Gemini: {str(e)}")
            return False
    
    def _generate_openai_question(self) -> str:
        """Generate question using OpenAI"""
        try:
            # Create a context-aware prompt based on position and question type
            prompt = self._create_question_prompt()
            
            response = self._openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert interviewer. Generate one relevant interview question."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.8  # Add randomness
            )
            
            question = response.choices[0].message.content.strip()
            # Clean up the question
            if question.endswith('?'):
                return question
            else:
                return question + "?"
                
        except Exception as e:
            print(f"DEBUG: OpenAI question generation failed: {str(e)}")
            return None
    
    def _generate_gemini_question(self) -> str:
        """Generate question using Google Gemini"""
        try:
            # Create a context-aware prompt based on position and question type
            prompt = self._create_question_prompt()
            
            response = self._gemini_client.generate_content(prompt)
            question = response.text.strip()
            
            # Clean up the question
            if question.endswith('?'):
                return question
            else:
                return question + "?"
                
        except Exception as e:
            print(f"DEBUG: Gemini question generation failed: {str(e)}")
            return None
    
    def _create_question_prompt(self) -> str:
        """Create a context-aware prompt for question generation"""
        position = getattr(self, 'position', 'General')
        question_type = getattr(self, 'question_type', 'mixed')
        current_q = getattr(self, 'current_question', 0)
        
        # Create different prompts based on question type and position
        if question_type == "technical":
            if position == "Software Engineer":
                technical_areas = ["programming", "system design", "algorithms", "databases", "testing", "architecture"]
                area = technical_areas[current_q % len(technical_areas)]
                return f"Generate a technical interview question for a Software Engineer position. Focus on {area}. Make it challenging but appropriate for the current question number ({current_q + 1})."
            elif position == "Data Scientist":
                data_areas = ["statistics", "machine learning", "data analysis", "Python", "SQL", "data visualization"]
                area = data_areas[current_q % len(data_areas)]
                return f"Generate a technical interview question for a Data Scientist position. Focus on {area}. Make it challenging but appropriate for the current question number ({current_q + 1})."
            else:
                return f"Generate a technical interview question for {position} position. Make it challenging but appropriate for the current question number ({current_q + 1})."
        
        elif question_type == "behavioral":
            behavioral_areas = ["leadership", "teamwork", "problem-solving", "communication", "adaptability", "conflict resolution"]
            area = behavioral_areas[current_q % len(behavioral_areas)]
            return f"Generate a behavioral interview question for {position} position. Focus on {area}. Make it appropriate for the current question number ({current_q + 1})."
        
        else:  # mixed
            if current_q < 2:
                # First questions are usually about background and motivation
                return f"Generate an interview question for {position} position. Focus on background, experience, or motivation. Make it appropriate for the current question number ({current_q + 1})."
            else:
                # Later questions are more specific
                return f"Generate an interview question for {position} position. Make it specific and challenging. Make it appropriate for the current question number ({current_q + 1})."
    
    def _get_fallback_question(self) -> str:
        """Get a fallback question from predefined list"""
        try:
            # Create position-specific question pools with 15+ questions each
            if hasattr(self, 'position') and self.position in ["Software Engineer", "Data Scientist"]:
                technical_questions = [
                    "Explain the difference between REST and GraphQL APIs.",
                    "How would you optimize a slow database query?",
                    "Describe your experience with version control systems.",
                    "How do you handle debugging complex issues?",
                    "What's your approach to code review?",
                    "Explain the concept of microservices architecture.",
                    "How do you ensure code quality and testing?",
                    "Describe a challenging technical problem you solved.",
                    "How do you stay updated with technology trends?",
                    "What's your experience with cloud platforms?",
                    "How do you handle technical debt in a project?",
                    "Describe your experience with CI/CD pipelines.",
                    "How do you approach system design problems?",
                    "What's your strategy for learning new technologies?",
                    "How do you handle production incidents?",
                    "Explain your experience with containerization.",
                    "How do you approach performance optimization?",
                    "What's your experience with distributed systems?",
                    "How do you handle security in your applications?",
                    "Describe a time you had to scale a system.",
                    "What programming languages are you most comfortable with?",
                    "How do you approach algorithm design?",
                    "Describe your experience with databases and data modeling.",
                    "How do you handle code optimization and refactoring?",
                    "What's your experience with testing frameworks?"
                ]
                # Use modulo to cycle through questions and add some randomness
                question_index = (self.current_question + hash(str(self.session_id)) % 5) % len(technical_questions)
                return technical_questions[question_index]
            
            elif hasattr(self, 'position') and self.position in ["Product Manager", "Sales Representative", "Marketing Manager"]:
                business_questions = [
                    "How do you prioritize competing demands?",
                    "Describe a successful project you led.",
                    "How do you handle stakeholder disagreements?",
                    "What metrics do you use to measure success?",
                    "How do you approach market research?",
                    "Describe a time you had to influence without authority.",
                    "How do you handle tight deadlines?",
                    "What's your strategy for building relationships?",
                    "How do you stay organized with multiple projects?",
                    "Describe a failure and what you learned from it.",
                    "How do you handle customer feedback and complaints?",
                    "What's your approach to competitive analysis?",
                    "How do you measure ROI on marketing campaigns?",
                    "Describe a time you had to pivot strategy.",
                    "How do you build consensus among team members?",
                    "What's your experience with budget management?",
                    "How do you handle team conflicts?",
                    "Describe a time you had to make a difficult decision.",
                    "How do you stay motivated in challenging times?",
                    "What's your approach to innovation?",
                    "How do you handle ambiguity in project requirements?",
                    "Describe your experience with cross-functional teams.",
                    "How do you approach problem-solving in business contexts?",
                    "What's your strategy for stakeholder communication?",
                    "How do you measure project success?"
                ]
                # Use modulo to cycle through questions and add some randomness
                question_index = (self.current_question + hash(str(self.session_id)) % 5) % len(business_questions)
                return business_questions[question_index]
            
            else:
                # General questions with 25+ options (removed inappropriate ones)
                general_questions = [
                    "Tell me about yourself and your background.",
                    "What are your greatest strengths and weaknesses?",
                    "Why are you interested in this position?",
                    "Where do you see yourself in 5 years?",
                    "Describe a challenging situation you faced at work and how you handled it.",
                    "What is your leadership style?",
                    "How do you handle stress and pressure?",
                    "What makes you the best candidate for this position?",
                    "How do you handle criticism and feedback?",
                    "Describe a time you had to work with a difficult colleague.",
                    "What motivates you in your work?",
                    "How do you stay productive and organized?",
                    "What's your approach to continuous learning?",
                    "How do you handle ambiguity and uncertainty?",
                    "Describe a time you had to adapt to change.",
                    "What's your experience with remote work?",
                    "How do you balance work and personal life?",
                    "What would your colleagues say about you?",
                    "How do you handle failure?",
                    "What's your biggest professional achievement?",
                    "How do you approach problem-solving?",
                    "Describe your ideal work environment.",
                    "What are your career goals?",
                    "How do you handle multiple priorities?",
                    "Describe a time you had to learn something quickly.",
                    "What's your approach to teamwork?",
                    "How do you handle constructive feedback?",
                    "Describe a time you exceeded expectations.",
                    "What's your learning style?",
                    "How do you stay motivated during challenging projects?"
                ]
                # Use modulo to cycle through questions and add some randomness
                question_index = (self.current_question + hash(str(self.session_id)) % 5) % len(general_questions)
                return general_questions[question_index]
                
        except Exception as e:
            print(f"DEBUG: Fallback question generation failed: {str(e)}")
            return None
    
    # Removed _record_answer method - no longer needed
    
    def _speak_message(self, message: str):
        """Convert text to speech and play it"""
        try:
            # For now, we'll use a simpler approach that works better in Streamlit
            # Print the message to console and update status
            print(f"AI: {message}")
            self._update_status(f"AI: {message}")
            
            # Try to use pyttsx3 if available
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)
                engine.setProperty('volume', 0.9)
                
                # Speak the message
                engine.say(message)
                engine.runAndWait()
                
            except ImportError:
                # pyttsx3 not available, just use text
                pass
            
        except Exception as e:
            self._update_status(f"Speech synthesis error: {str(e)}")
            # Fallback to text display
            print(f"AI: {message}")
    
    def _provide_feedback(self, evaluation: Dict):
        """Provide feedback on the answer"""
        try:
            overall_score = evaluation.get("overall_score", 0)
            strengths = evaluation.get("strengths", [])
            improvements = evaluation.get("improvements", [])
            
            # Create feedback message
            feedback_parts = [f"Your answer scored {overall_score:.1f} out of 100."]
            
            if strengths:
                feedback_parts.append("Strengths: " + ", ".join(strengths[:2]))
            
            if improvements:
                feedback_parts.append("Suggestions: " + ", ".join(improvements[:2]))
            
            feedback_message = " ".join(feedback_parts)
            
            # Speak feedback
            self._speak_message(feedback_message)
            self._update_status("Feedback provided")
            
        except Exception as e:
            self._update_status(f"Feedback error: {str(e)}")
    
    def _end_interview(self):
        """End the interview and generate summary"""
        try:
            # Prevent multiple calls to _end_interview
            if not self.is_interview_active:
                print("DEBUG: Interview already ended, skipping")
                return
                
            self._update_status("Interview completed. Generating summary...")
            print(f"DEBUG: Ending interview - current_question={self.current_question}, total_questions={self.total_questions}")
            print(f"DEBUG: Conversation history length: {len(self.conversation_history)}")
            
            # Calculate session duration
            if hasattr(self, 'session_start_time') and self.session_start_time is not None:
                session_duration = (time.time() - self.session_start_time) / 60  # minutes
                print(f"DEBUG: Session duration calculated: {session_duration:.2f} minutes")
            else:
                session_duration = 0
                print("DEBUG: Session start time not available, using 0 duration")
            
            # Generate overall summary based on content analysis
            summary = self._generate_interview_summary()
            
            # Calculate overall score
            if self.content_analysis:
                overall_score = sum(analysis.get("overall_score", 0) for analysis in self.content_analysis) / len(self.content_analysis)
            else:
                overall_score = 0
            
            # Prepare session data
            session_data = {
                "session_id": self.session_id,
                "session_info": {
                    "position": self.position,
                    "question_type": self.question_type,
                    "total_questions": self.total_questions,
                    "questions_answered": len(self.conversation_history),
                    "date": datetime.now().strftime("%B %d, %Y"),
                    "duration": session_duration
                },
                "conversation_history": self.conversation_history,
                "speech_analysis": self.speech_analysis,
                "content_analysis": self.content_analysis,
                "summary": summary,
                "overall_score": overall_score
            }
            
            # Save session data
            self._save_session_data(session_data)
            
            # Generate reports
            self._generate_reports(session_data)
            
            # Final message
            final_message = f"Interview completed! Your overall score is {overall_score:.1f} out of 100. Check your reports for detailed feedback."
            self._speak_message(final_message)
            
            self._update_status("Interview completed successfully")
            print(f"DEBUG: Interview ended successfully with {len(self.conversation_history)} questions answered")
            
        except Exception as e:
            self._update_status(f"Interview end error: {str(e)}")
            print(f"DEBUG: Error ending interview: {e}")
        finally:
            # Only mark as inactive after everything is complete
            self.is_interview_active = False
            print(f"DEBUG: Set is_interview_active = False")
            print(f"DEBUG: Final status - current_question={self.current_question}, total_questions={self.total_questions}, active={self.is_interview_active}")
    
    def _generate_interview_summary(self):
        """Generate a comprehensive interview summary"""
        try:
            # Analyze the conversation to generate meaningful summary
            if not self.conversation_history:
                return {
                    "overall_impression": "Interview completed but no answers recorded",
                    "readiness_level": "Unable to assess",
                    "key_strengths": ["Interview completed"],
                    "improvement_areas": ["No answers recorded"],
                    "recommendations": ["Please retake the interview"]
                }
            
            # Count different types of responses
            technical_answers = 0
            behavioral_answers = 0
            general_answers = 0
            
            for exchange in self.conversation_history:
                answer = exchange.get("answer", "").lower()
                if any(word in answer for word in ["code", "programming", "algorithm", "database", "system", "technical"]):
                    technical_answers += 1
                elif any(word in answer for word in ["team", "leadership", "communication", "problem", "challenge"]):
                    behavioral_answers += 1
                else:
                    general_answers += 1
            
            # Generate position-specific feedback
            if self.position in ["Software Engineer", "Data Scientist"]:
                if technical_answers > behavioral_answers:
                    readiness = "Strong Technical Foundation"
                    strengths = ["Technical knowledge", "Problem-solving approach"]
                    improvements = ["Could improve communication", "Work on behavioral examples"]
                else:
                    readiness = "Good Communication Skills"
                    strengths = ["Clear communication", "Professional demeanor"]
                    improvements = ["Focus on technical depth", "Provide more technical examples"]
            else:
                if behavioral_answers > general_answers:
                    readiness = "Strong Behavioral Skills"
                    strengths = ["Leadership potential", "Communication skills"]
                    improvements = ["Provide more specific examples", "Work on technical knowledge"]
                else:
                    readiness = "Good General Skills"
                    strengths = ["Professional attitude", "Basic communication"]
                    improvements = ["Develop leadership examples", "Work on specific achievements"]
            
            return {
                "overall_impression": f"Good candidate with {readiness.lower()}",
                "readiness_level": readiness,
                "key_strengths": strengths,
                "improvement_areas": improvements,
                "recommendations": [
                    "Practice with more mock interviews",
                    "Prepare specific examples for common questions",
                    "Work on speaking pace and clarity",
                    "Focus on position-specific skills"
                ]
            }
            
        except Exception as e:
            print(f"DEBUG: Error generating summary: {str(e)}")
            return {
                "overall_impression": "Good candidate with room for improvement",
                "readiness_level": "Intermediate",
                "key_strengths": ["Interview completed"],
                "improvement_areas": ["Could provide more specific examples"],
                "recommendations": [
                    "Practice with more mock interviews",
                    "Prepare specific examples for common questions"
                ]
            }
    
    def _generate_reports(self, session_data: Dict):
        """Generate PDF and text reports"""
        try:
            # Generate PDF report
            pdf_path = self.report_generator.generate_interview_report(session_data)
            self._update_status(f"PDF report generated: {pdf_path}")
            
            # Generate text report
            text_path = self.report_generator.generate_simple_report(session_data)
            self._update_status(f"Text report generated: {text_path}")
            
        except Exception as e:
            self._update_status(f"Report generation error: {str(e)}")
    
    def _save_session_data(self, session_data: Dict = None):
        """Save session data to file"""
        try:
            if session_data is None:
                # Save current session state
                session_data = {
                    "session_id": self.session_id,
                    "conversation_history": self.conversation_history,
                    "speech_analysis": self.speech_analysis,
                    "content_analysis": self.content_analysis
                }
            
            save_interview_data(self.session_id, session_data)
            
        except Exception as e:
            self._update_status(f"Data save error: {str(e)}")
    
    def stop_interview(self):
        """Stop the current interview"""
        self.is_interview_active = False
        self.audio_processor.stop_recording()
        self.audio_player.stop_playback()
        self._update_status("Interview stopped")
    
    def pause_interview(self):
        """Pause the current interview"""
        self.audio_processor.stop_recording()
        self.audio_player.stop_playback()
        self._update_status("Interview paused")
    
    def resume_interview(self):
        """Resume the current interview"""
        if self.is_interview_active:
            self._update_status("Interview resumed")
        else:
            self._update_status("No active interview to resume")
    
    def get_interview_status(self) -> Dict:
        """Get current interview status"""
        return {
            "is_active": self.is_interview_active,
            "current_question": self.current_question + 1,  # Display 1-based question number
            "total_questions": self.total_questions,
            "position": self.position,
            "session_id": self.session_id,
            "conversation_count": len(self.conversation_history),
            "progress_percentage": min(100, max(0, (len(self.conversation_history) / self.total_questions) * 100))
        }
    
    def is_ready_for_status_display(self) -> bool:
        """Check if interview is ready to display status"""
        return self.is_interview_active and self.session_id is not None
    
    def is_interview_completed(self) -> bool:
        """Check if interview has completed all questions"""
        # Interview is completed when:
        # 1. We've asked all questions (current_question >= total_questions)
        # 2. We have conversation history (at least one answer)
        # 3. Interview is no longer active
        return (self.current_question >= self.total_questions and 
                len(self.conversation_history) > 0 and
                not self.is_interview_active)
    
    def get_session_data(self) -> Dict:
        """Get complete session data"""
        if not self.session_id:
            return {}
        
        return load_interview_data(self.session_id)
    
    def _update_status(self, message: str):
        """Update status via callback"""
        if self.status_callback:
            self.status_callback(message)
        print(f"Status: {message}")
    
    def _update_progress(self):
        """Update progress via callback"""
        if self.progress_callback:
            # Calculate progress as percentage of completed questions
            # Progress should be based on answered questions, not just current question number
            answered_questions = len(self.conversation_history)
            # Ensure progress doesn't exceed 100% and is accurate
            progress = min(100, max(0, (answered_questions / self.total_questions) * 100))
            print(f"DEBUG: Progress update - answered: {answered_questions}, total: {self.total_questions}, progress: {progress:.1f}%")
            self.progress_callback(progress)
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_interview()
        cleanup_temp_files()
    
    def get_available_positions(self) -> List[str]:
        """Get list of available interview positions"""
        return list(INTERVIEW_TYPES.keys())
    
    def get_question_types(self) -> List[str]:
        """Get list of available question types"""
        return list(set(INTERVIEW_TYPES.values()))

    def _ensure_interview_completion(self):
        """Ensure the interview completes properly"""
        try:
            print(f"DEBUG: Ensuring interview completion - current_question={self.current_question}, total_questions={self.total_questions}")
            print(f"DEBUG: Conversation history length: {len(self.conversation_history)}")
            
            # Check if interview is already inactive
            if not self.is_interview_active:
                print("DEBUG: Interview already inactive, skipping completion check")
                return True
            
            # Check if we've completed all questions
            if self.current_question >= self.total_questions:
                print("DEBUG: Interview completed, calling _end_interview")
                # Force the interview to complete properly
                self._end_interview()
                return True
            
            # Interview should continue
            print(f"DEBUG: Interview should continue - {self.current_question}/{self.total_questions} questions asked")
            return False
            
        except Exception as e:
            print(f"DEBUG: Error ensuring interview completion: {str(e)}")
            return False
    
    def _add_randomness_to_questions(self):
        """Add randomness to question selection to avoid repetition"""
        try:
            # Use current timestamp and question number to create some randomness
            import random
            import time
            
            # Seed random with current time and question number
            random.seed(int(time.time()) + self.current_question)
            
            # Randomly select from available question types
            if hasattr(self, 'question_type'):
                if self.question_type == "technical":
                    # Randomly vary technical focus areas
                    technical_focuses = ["programming", "system design", "algorithms", "databases", "testing", "architecture", "performance", "security"]
                    random_focus = random.choice(technical_focuses)
                    print(f"DEBUG: Randomly selected technical focus: {random_focus}")
                
                elif self.question_type == "behavioral":
                    # Randomly vary behavioral focus areas
                    behavioral_focuses = ["leadership", "teamwork", "problem-solving", "communication", "adaptability", "conflict resolution", "time management", "innovation"]
                    random_focus = random.choice(behavioral_focuses)
                    print(f"DEBUG: Randomly selected behavioral focus: {random_focus}")
            
        except Exception as e:
            print(f"DEBUG: Error adding randomness: {str(e)}")

    def should_continue_interview(self) -> bool:
        """Check if the interview should continue"""
        try:
            # Interview should continue if:
            # 1. Interview is active
            # 2. We haven't reached the total questions limit
            # 3. We haven't completed all questions
            should_continue = (
                self.is_interview_active and 
                self.current_question < self.total_questions and
                len(self.conversation_history) < self.total_questions
            )
            
            print(f"DEBUG: Should continue interview: {should_continue}")
            print(f"DEBUG: - is_interview_active: {self.is_interview_active}")
            print(f"DEBUG: - current_question: {self.current_question}")
            print(f"DEBUG: - total_questions: {self.total_questions}")
            print(f"DEBUG: - conversation_history: {len(self.conversation_history)}")
            
            return should_continue
            
        except Exception as e:
            print(f"DEBUG: Error checking interview status: {str(e)}")
            return False
    
    def force_complete_interview(self):
        """Force complete the interview if it's stuck"""
        try:
            print("DEBUG: Force completing interview")
            if self.is_interview_active:
                self._end_interview()
            else:
                print("DEBUG: Interview already inactive")
        except Exception as e:
            print(f"DEBUG: Error force completing interview: {str(e)}")
            self.is_interview_active = False
