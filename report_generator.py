"""
Report generator module for creating comprehensive interview reports
"""

import os
from datetime import datetime
from typing import Dict, List, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from config import REPORTS_DIR

class ReportGenerator:
    """
    Generates comprehensive PDF reports for interview sessions
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Section header style
        self.section_style = ParagraphStyle(
            'CustomSection',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        )
        
        # Subsection style
        self.subsection_style = ParagraphStyle(
            'CustomSubsection',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkgreen
        )
        
        # Normal text style
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        # Score style
        self.score_style = ParagraphStyle(
            'ScoreStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            alignment=TA_LEFT,
            textColor=colors.darkred
        )
    
    def generate_interview_report(self, session_data: Dict[str, Any], 
                                output_filename: str = None) -> str:
        """
        Generate comprehensive interview report
        
        Args:
            session_data: Complete session data
            output_filename: Optional output filename
            
        Returns:
            Path to generated PDF file
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"interview_report_{timestamp}.pdf"
        
        filepath = os.path.join(REPORTS_DIR, output_filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        # Build story (content)
        story = []
        
        # Add title page
        story.extend(self._create_title_page(session_data))
        story.append(PageBreak())
        
        # Add executive summary
        story.extend(self._create_executive_summary(session_data))
        story.append(PageBreak())
        
        # Add detailed analysis
        story.extend(self._create_detailed_analysis(session_data))
        story.append(PageBreak())
        
        # Add conversation transcript
        story.extend(self._create_conversation_transcript(session_data))
        story.append(PageBreak())
        
        # Add recommendations
        story.extend(self._create_recommendations(session_data))
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    def _create_title_page(self, session_data: Dict[str, Any]) -> List:
        """Create title page"""
        story = []
        
        # Title
        title = Paragraph("AI Mock Interview Report", self.title_style)
        story.append(title)
        story.append(Spacer(1, 30))
        
        # Session information
        session_info = session_data.get("session_info", {})
        position = session_info.get("position", "Unknown Position")
        date = session_info.get("date", datetime.now().strftime("%B %d, %Y"))
        
        # Position and date
        position_text = Paragraph(f"<b>Position:</b> {position}", self.normal_style)
        date_text = Paragraph(f"<b>Date:</b> {date}", self.normal_style)
        
        story.append(position_text)
        story.append(date_text)
        story.append(Spacer(1, 20))
        
        # Overall score
        overall_score = session_data.get("overall_score", 0)
        score_text = Paragraph(f"<b>Overall Score:</b> {overall_score:.1f}/100", self.score_style)
        story.append(score_text)
        
        return story
    
    def _create_executive_summary(self, session_data: Dict[str, Any]) -> List:
        """Create executive summary section"""
        story = []
        
        # Section header
        header = Paragraph("Executive Summary", self.section_style)
        story.append(header)
        story.append(Spacer(1, 12))
        
        # Overall assessment
        summary = session_data.get("summary", {})
        overall_impression = summary.get("overall_impression", "No overall impression available.")
        readiness_level = summary.get("readiness_level", "Unknown")
        
        impression_text = Paragraph(f"<b>Overall Impression:</b> {overall_impression}", self.normal_style)
        readiness_text = Paragraph(f"<b>Readiness Level:</b> {readiness_level}", self.normal_style)
        
        story.append(impression_text)
        story.append(readiness_text)
        story.append(Spacer(1, 12))
        
        # Key metrics table
        metrics_data = self._create_metrics_table_data(session_data)
        if metrics_data:
            metrics_table = Table(metrics_data, colWidths=[2*inch, 1*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(metrics_table)
            story.append(Spacer(1, 20))
        
        # Key strengths and weaknesses
        strengths = summary.get("key_strengths", [])
        weaknesses = summary.get("improvement_areas", [])
        
        if strengths:
            story.append(Paragraph("<b>Key Strengths:</b>", self.subsection_style))
            for strength in strengths:
                story.append(Paragraph(f"• {strength}", self.normal_style))
            story.append(Spacer(1, 12))
        
        if weaknesses:
            story.append(Paragraph("<b>Areas for Improvement:</b>", self.subsection_style))
            for weakness in weaknesses:
                story.append(Paragraph(f"• {weakness}", self.normal_style))
        
        return story
    
    def _create_detailed_analysis(self, session_data: Dict[str, Any]) -> List:
        """Create detailed analysis section"""
        story = []
        
        # Section header
        header = Paragraph("Detailed Analysis", self.section_style)
        story.append(header)
        story.append(Spacer(1, 12))
        
        # Speech analysis
        speech_analysis = session_data.get("speech_analysis", [])
        if speech_analysis:
            story.append(Paragraph("Speech Analysis", self.subsection_style))
            
            for i, analysis in enumerate(speech_analysis, 1):
                story.append(Paragraph(f"<b>Answer {i}:</b>", self.normal_style))
                
                # Confidence score
                confidence = analysis.get("confidence_score", 0)
                story.append(Paragraph(f"Confidence Score: {confidence:.1f}/100", self.score_style))
                
                # Detailed metrics
                pitch = analysis.get("pitch", {})
                tempo = analysis.get("tempo", {})
                energy = analysis.get("energy", {})
                pauses = analysis.get("pauses", {})
                clarity = analysis.get("clarity", {})
                
                metrics_text = f"""
                Pitch Stability: {pitch.get('pitch_stability', 0):.1f}% | 
                Speaking Rate: {tempo.get('speaking_rate_wpm', 0):.1f} WPM | 
                Energy Consistency: {energy.get('energy_consistency', 0):.1f}% | 
                Pause Usage: {pauses.get('pause_score', 0)*100:.1f}% | 
                Clarity: {clarity.get('clarity_score', 0)*100:.1f}%
                """
                story.append(Paragraph(metrics_text, self.normal_style))
                story.append(Spacer(1, 8))
        
        # Content analysis
        content_analysis = session_data.get("content_analysis", [])
        if content_analysis:
            story.append(Paragraph("Content Analysis", self.subsection_style))
            
            for i, content in enumerate(content_analysis, 1):
                story.append(Paragraph(f"<b>Answer {i} Evaluation:</b>", self.normal_style))
                
                relevance = content.get("relevance_score", 0)
                specificity = content.get("specificity_score", 0)
                professionalism = content.get("professionalism_score", 0)
                overall = content.get("overall_score", 0)
                
                scores_text = f"""
                Relevance: {relevance}/100 | 
                Specificity: {specificity}/100 | 
                Professionalism: {professionalism}/100 | 
                Overall: {overall}/100
                """
                story.append(Paragraph(scores_text, self.score_style))
                
                # Strengths and improvements
                strengths = content.get("strengths", [])
                improvements = content.get("improvements", [])
                
                if strengths:
                    story.append(Paragraph("<b>Strengths:</b>", self.normal_style))
                    for strength in strengths:
                        story.append(Paragraph(f"• {strength}", self.normal_style))
                
                if improvements:
                    story.append(Paragraph("<b>Improvements:</b>", self.normal_style))
                    for improvement in improvements:
                        story.append(Paragraph(f"• {improvement}", self.normal_style))
                
                story.append(Spacer(1, 12))
        
        return story
    
    def _create_conversation_transcript(self, session_data: Dict[str, Any]) -> List:
        """Create conversation transcript section"""
        story = []
        
        # Section header
        header = Paragraph("Conversation Transcript", self.section_style)
        story.append(header)
        story.append(Spacer(1, 12))
        
        # Conversation history
        conversation = session_data.get("conversation_history", [])
        
        if not conversation:
            story.append(Paragraph("No conversation recorded.", self.normal_style))
            return story
        
        for i, exchange in enumerate(conversation, 1):
            question = exchange.get("question", "")
            answer = exchange.get("answer", "")
            
            # Question
            story.append(Paragraph(f"<b>Question {i}:</b>", self.subsection_style))
            story.append(Paragraph(question, self.normal_style))
            story.append(Spacer(1, 6))
            
            # Answer
            story.append(Paragraph("<b>Answer:</b>", self.normal_style))
            story.append(Paragraph(answer, self.normal_style))
            story.append(Spacer(1, 12))
        
        return story
    
    def _create_recommendations(self, session_data: Dict[str, Any]) -> List:
        """Create recommendations section"""
        story = []
        
        # Section header
        header = Paragraph("Recommendations", self.section_style)
        story.append(header)
        story.append(Spacer(1, 12))
        
        # Get recommendations from summary
        summary = session_data.get("summary", {})
        recommendations = summary.get("recommendations", [])
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                story.append(Paragraph(f"{i}. {rec}", self.normal_style))
        else:
            story.append(Paragraph("No specific recommendations available.", self.normal_style))
        
        story.append(Spacer(1, 20))
        
        # General tips
        story.append(Paragraph("General Interview Tips:", self.subsection_style))
        general_tips = [
            "Practice speaking clearly and at a moderate pace",
            "Use specific examples to illustrate your points",
            "Maintain good posture and eye contact",
            "Prepare thoughtful questions to ask the interviewer",
            "Follow up with a thank-you note after the interview"
        ]
        
        for tip in general_tips:
            story.append(Paragraph(f"• {tip}", self.normal_style))
        
        return story
    
    def _create_metrics_table_data(self, session_data: Dict[str, Any]) -> List:
        """Create metrics table data"""
        data = [["Metric", "Score"]]
        
        # Overall score
        overall_score = session_data.get("overall_score", 0)
        data.append(["Overall Score", f"{overall_score:.1f}/100"])
        
        # Average confidence score
        speech_analysis = session_data.get("speech_analysis", [])
        if speech_analysis:
            avg_confidence = sum(analysis.get("confidence_score", 0) for analysis in speech_analysis) / len(speech_analysis)
            data.append(["Average Confidence", f"{avg_confidence:.1f}/100"])
        
        # Number of questions
        conversation = session_data.get("conversation_history", [])
        data.append(["Questions Answered", str(len(conversation))])
        
        # Session duration
        session_info = session_data.get("session_info", {})
        duration = session_info.get("duration", 0)
        if duration:
            data.append(["Session Duration", f"{duration:.1f} minutes"])
        
        return data
    
    def generate_simple_report(self, session_data: Dict[str, Any], 
                             output_filename: str = None) -> str:
        """
        Generate a simplified text report
        
        Args:
            session_data: Session data
            output_filename: Optional output filename
            
        Returns:
            Path to generated text file
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"interview_summary_{timestamp}.txt"
        
        filepath = os.path.join(REPORTS_DIR, output_filename)
        
        with open(filepath, 'w') as f:
            # Header
            f.write("AI Mock Interview Report\n")
            f.write("=" * 50 + "\n\n")
            
            # Session info
            session_info = session_data.get("session_info", {})
            f.write(f"Position: {session_info.get('position', 'Unknown')}\n")
            f.write(f"Date: {session_info.get('date', 'Unknown')}\n")
            f.write(f"Overall Score: {session_data.get('overall_score', 0):.1f}/100\n\n")
            
            # Summary
            summary = session_data.get("summary", {})
            f.write("Summary:\n")
            f.write(f"Overall Impression: {summary.get('overall_impression', 'N/A')}\n")
            f.write(f"Readiness Level: {summary.get('readiness_level', 'N/A')}\n\n")
            
            # Strengths and weaknesses
            strengths = summary.get("key_strengths", [])
            if strengths:
                f.write("Key Strengths:\n")
                for strength in strengths:
                    f.write(f"- {strength}\n")
                f.write("\n")
            
            weaknesses = summary.get("improvement_areas", [])
            if weaknesses:
                f.write("Areas for Improvement:\n")
                for weakness in weaknesses:
                    f.write(f"- {weakness}\n")
                f.write("\n")
            
            # Recommendations
            recommendations = summary.get("recommendations", [])
            if recommendations:
                f.write("Recommendations:\n")
                for i, rec in enumerate(recommendations, 1):
                    f.write(f"{i}. {rec}\n")
        
        return filepath
