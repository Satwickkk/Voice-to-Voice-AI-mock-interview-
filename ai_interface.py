"""
AI interface module for speech recognition and AI interview logic
"""

import os
import openai
import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
from config import OPENAI_API_KEY, GOOGLE_API_KEY, WHISPER_MODEL, GEMINI_MODEL

class AIInterface:
    """
    Handles AI interactions for speech recognition and interview logic
    """
    
    def __init__(self):
        """Initialize AI interface"""
        # Load API keys
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        
        # Initialize OpenAI client
        self.openai_client = None
        if self.openai_api_key:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            except Exception as e:
                print(f"OpenAI initialization error: {e}")
        
        # Initialize Google Gemini
        self.gemini_model = None
        if self.google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_api_key)
                # Use the correct model name
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                print(f"Gemini initialization error: {e}")
        
        if not self.openai_client and not self.gemini_model:
            print("Warning: No AI APIs configured. Using fallback responses.")
    
    def transcribe_audio(self, audio_file: str) -> Tuple[str, Dict]:
        """
        Transcribe audio file using OpenAI Whisper
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Tuple of (transcript, metadata)
        """
        try:
            if not self.openai_client:
                return "", {"error": "OpenAI client not initialized"}
            
            with open(audio_file, "rb") as audio:
                response = self.openai_client.audio.transcriptions.create(
                    model=WHISPER_MODEL,
                    file=audio,
                    response_format="verbose_json"
                )
            
            transcript = response.text
            metadata = {
                "language": response.language,
                "duration": response.duration,
                "segments": response.segments
            }
            
            return transcript, metadata
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return "", {"error": str(e)}
    
    def generate_interview_question(self, position: str, question_type: str = "behavioral", 
                                  conversation_history: List[Dict] = None) -> str:
        """
        Generate interview question using Google Gemini
        
        Args:
            position: Job position
            question_type: Type of question (behavioral, technical, etc.)
            conversation_history: Previous conversation context
            
        Returns:
            Generated question
        """
        try:
            if not self.gemini_model:
                return self._get_fallback_question(position, question_type)
            
            # Build context from conversation history
            context = self._build_conversation_context(conversation_history)
            
            # Create prompt for question generation
            prompt = f"""
            You are an expert interviewer conducting a {question_type} interview for a {position} position.
            
            {context}
            
            Generate a relevant, professional interview question that:
            1. Is appropriate for a {position} role
            2. Follows up on the candidate's previous responses naturally
            3. Encourages detailed, thoughtful answers
            4. Is specific and actionable
            
            Return only the question, no additional text.
            """
            
            response = self.gemini_model.generate_content(prompt)
            question = response.text.strip()
            
            # Fallback if response is empty
            if not question:
                return self._get_fallback_question(position, question_type)
            
            return question
            
        except Exception as e:
            print(f"Question generation error: {e}")
            return self._get_fallback_question(position, question_type)
    
    def evaluate_answer(self, question: str, answer: str, position: str) -> Dict:
        """
        Evaluate candidate's answer using AI
        
        Args:
            question: Interview question
            answer: Candidate's answer
            position: Job position
            
        Returns:
            Evaluation results
        """
        try:
            if not self.gemini_model:
                return self._get_default_evaluation()
            
            prompt = f"""
            You are an expert interviewer evaluating a candidate's response for a {position} position.
            
            Question: {question}
            Answer: {answer}
            
            Please provide a comprehensive evaluation. Respond ONLY with a valid JSON object in this exact format:
            {{
                "relevance_score": <number between 0-100>,
                "specificity_score": <number between 0-100>,
                "professionalism_score": <number between 0-100>,
                "overall_score": <number between 0-100>,
                "strengths": ["strength1", "strength2"],
                "improvements": ["improvement1", "improvement2"],
                "follow_up_question": "question"
            }}
            
            Evaluation criteria:
            - Relevance: How well does the answer address the question?
            - Specificity: How specific and detailed is the answer?
            - Professionalism: How professional and appropriate is the response?
            - Overall: Overall assessment considering all factors
            """
            
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Try to parse JSON response
            try:
                import json
                # Clean the response text to extract JSON
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                evaluation = json.loads(response_text.strip())
                
                # Validate the evaluation
                required_keys = ["relevance_score", "specificity_score", "professionalism_score", 
                               "overall_score", "strengths", "improvements", "follow_up_question"]
                
                for key in required_keys:
                    if key not in evaluation:
                        evaluation[key] = self._get_default_evaluation()[key]
                
                # Ensure scores are within valid range
                for key in ["relevance_score", "specificity_score", "professionalism_score", "overall_score"]:
                    if key in evaluation:
                        evaluation[key] = max(0, min(100, float(evaluation[key])))
                
                return evaluation
                
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"JSON parsing error: {e}")
                print(f"Response text: {response_text}")
                return self._get_default_evaluation()
                
        except Exception as e:
            print(f"Answer evaluation error: {e}")
            return self._get_default_evaluation()
    
    def generate_follow_up_question(self, question: str, answer: str, 
                                  conversation_history: List[Dict]) -> str:
        """
        Generate contextual follow-up question
        
        Args:
            question: Original question
            answer: Candidate's answer
            conversation_history: Full conversation context
            
        Returns:
            Follow-up question
        """
        try:
            if not self.gemini_model:
                return self._get_generic_follow_up()
            
            context = self._build_conversation_context(conversation_history)
            
            prompt = f"""
            Based on the conversation history and the candidate's most recent answer, generate a natural follow-up question.
            
            {context}
            
            The follow-up question should:
            1. Build upon the candidate's response
            2. Explore deeper aspects of their answer
            3. Maintain professional interview flow
            4. Be specific and relevant
            
            Return only the follow-up question, no additional text.
            """
            
            response = self.gemini_model.generate_content(prompt)
            follow_up = response.text.strip()
            
            if not follow_up:
                return self._get_generic_follow_up()
            
            return follow_up
            
        except Exception as e:
            print(f"Follow-up generation error: {e}")
            return self._get_generic_follow_up()
    
    def generate_interview_summary(self, conversation_history: List[Dict], 
                                 speech_analysis: List[Dict]) -> Dict:
        """
        Generate comprehensive interview summary
        
        Args:
            conversation_history: Full conversation
            speech_analysis: Speech analysis results
            
        Returns:
            Interview summary
        """
        try:
            if not self.gemini_model:
                return self._get_default_summary()
            
            # Prepare conversation summary
            conversation_text = self._format_conversation_for_summary(conversation_history)
            
            # Prepare speech analysis summary
            speech_summary = self._format_speech_analysis_for_summary(speech_analysis)
            
            prompt = f"""
            You are an expert interview coach providing a comprehensive evaluation of a mock interview.
            
            Conversation:
            {conversation_text}
            
            Speech Analysis:
            {speech_summary}
            
            Please provide a detailed evaluation including:
            1. Overall interview score (0-100)
            2. Content quality assessment
            3. Communication effectiveness
            4. Key strengths demonstrated
            5. Areas needing improvement
            6. Specific recommendations for future interviews
            7. Overall impression and readiness level
            
            Format as JSON:
            {{
                "overall_score": number,
                "content_assessment": "detailed assessment",
                "communication_effectiveness": "detailed assessment",
                "key_strengths": ["strength1", "strength2", "strength3"],
                "improvement_areas": ["area1", "area2", "area3"],
                "recommendations": ["rec1", "rec2", "rec3"],
                "overall_impression": "detailed impression",
                "readiness_level": "Ready/Needs Improvement/Not Ready"
            }}
            """
            
            response = self.gemini_model.generate_content(prompt)
            
            try:
                import json
                summary = json.loads(response.text)
                return summary
            except json.JSONDecodeError:
                return self._parse_summary_text(response.text)
                
        except Exception as e:
            print(f"Summary generation error: {e}")
            return self._get_default_summary()
    
    def _build_conversation_context(self, conversation_history: List[Dict]) -> str:
        """Build conversation context for AI prompts"""
        if not conversation_history:
            return "This is the beginning of the interview."
        
        context_parts = []
        for i, exchange in enumerate(conversation_history[-5:], 1):  # Last 5 exchanges
            question = exchange.get("question", "")
            answer = exchange.get("answer", "")
            context_parts.append(f"Q{i}: {question}\nA{i}: {answer}")
        
        return "\n\n".join(context_parts)
    
    def _get_fallback_question(self, position: str, question_type: str) -> str:
        """Get fallback question when AI is unavailable"""
        questions = {
            "behavioral": [
                "Tell me about a time when you had to work with a difficult team member.",
                "Describe a situation where you had to meet a tight deadline.",
                "Give me an example of when you had to learn something new quickly.",
                "Tell me about a time when you had to handle a conflict at work.",
                "Describe a project where you had to take initiative."
            ],
            "technical": [
                "What programming languages are you most comfortable with?",
                "Describe your experience with version control systems.",
                "How do you approach debugging a complex problem?",
                "Tell me about a technical challenge you recently solved.",
                "What's your experience with cloud platforms?"
            ],
            "mixed": [
                "What interests you about this position?",
                "Where do you see yourself in 5 years?",
                "What are your greatest strengths and weaknesses?",
                "Why should we hire you for this role?",
                "What motivates you in your work?"
            ]
        }
        
        import random
        return random.choice(questions.get(question_type, questions["mixed"]))
    
    def _get_generic_follow_up(self) -> str:
        """Get generic follow-up question"""
        follow_ups = [
            "Can you elaborate on that?",
            "What was the outcome of that situation?",
            "How did you handle the challenges you mentioned?",
            "What did you learn from that experience?",
            "Can you give me a specific example?"
        ]
        import random
        return random.choice(follow_ups)
    
    def _get_default_evaluation(self) -> Dict:
        """Get default evaluation when AI is unavailable"""
        return {
            "relevance_score": 75,
            "specificity_score": 70,
            "professionalism_score": 80,
            "overall_score": 75,
            "strengths": ["Good response structure", "Professional tone", "Clear communication"],
            "improvements": ["Provide more specific examples", "Add more detail to responses", "Practice speaking pace"],
            "follow_up_question": "Can you elaborate on that with a specific example?"
        }
    
    def _get_default_summary(self) -> Dict:
        """Get default summary when AI is unavailable"""
        return {
            "overall_score": 75,
            "content_assessment": "Good overall responses with room for improvement",
            "communication_effectiveness": "Clear communication with some areas to enhance",
            "key_strengths": ["Professional demeanor", "Good response structure"],
            "improvement_areas": ["Add more specific examples", "Improve speaking pace"],
            "recommendations": ["Practice with more mock interviews", "Work on specific examples"],
            "overall_impression": "Promising candidate with good potential",
            "readiness_level": "Needs Improvement"
        }
    
    def _parse_evaluation_text(self, text: str) -> Dict:
        """Parse evaluation from text response"""
        # Simple text parsing as fallback
        return self._get_default_evaluation()
    
    def _parse_summary_text(self, text: str) -> Dict:
        """Parse summary from text response"""
        # Simple text parsing as fallback
        return self._get_default_summary()
    
    def _format_conversation_for_summary(self, conversation_history: List[Dict]) -> str:
        """Format conversation for summary generation"""
        if not conversation_history:
            return "No conversation recorded."
        
        formatted = []
        for i, exchange in enumerate(conversation_history, 1):
            question = exchange.get("question", "")
            answer = exchange.get("answer", "")
            formatted.append(f"Q{i}: {question}\nA{i}: {answer}")
        
        return "\n\n".join(formatted)
    
    def _format_speech_analysis_for_summary(self, speech_analysis: List[Dict]) -> str:
        """Format speech analysis for summary generation"""
        if not speech_analysis:
            return "No speech analysis available."
        
        summary_parts = []
        for i, analysis in enumerate(speech_analysis, 1):
            confidence = analysis.get("confidence_score", 0)
            summary_parts.append(f"Answer {i}: Confidence Score {confidence:.1f}/100")
        
        return "\n".join(summary_parts)
