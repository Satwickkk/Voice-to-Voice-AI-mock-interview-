# API Setup Guide for AI Interview System

## **🔑 Required API Keys**

### **1. OpenAI API Key (Recommended)**
- **Purpose**: Generate intelligent, context-aware interview questions
- **Get it from**: https://platform.openai.com/api-keys
- **Cost**: ~$0.002 per 1K tokens (very cheap for interviews)
- **Add to**: `.env` file as `OPENAI_API_KEY=your_key_here`

### **2. Google Gemini API Key (Alternative)**
- **Purpose**: Fallback question generation if OpenAI fails
- **Get it from**: https://makersuite.google.com/app/apikey
- **Cost**: Free tier available
- **Add to**: `.env` file as `GOOGLE_API_KEY=your_key_here`

## **📁 Environment File Setup**

Create a `.env` file in your project root:

```env
# AI API Keys
OPENAI_API_KEY=sk-your_openai_key_here
GOOGLE_API_KEY=your_google_key_here

# Interview Settings
INTERVIEW_QUESTIONS=10
AUDIO_SAMPLE_RATE=16000
AUDIO_CHUNK_SIZE=1024
```

## **🚨 Current Issues & Solutions**

### **Issue 1: Questions Are Identical**
- **Cause**: API keys not working, falling back to same questions
- **Solution**: Set up proper API keys
- **Fallback**: System now has 20+ unique questions per domain

### **Issue 2: Only 5 Questions Instead of 10**
- **Cause**: Limited question pool
- **Solution**: Expanded to 20+ questions per domain
- **Added**: Randomization based on session ID

### **Issue 3: No Results Displayed**
- **Cause**: Interview completion logic broken
- **Solution**: Fixed completion flow and state management

### **Issue 4: Interview Loop Not Completing**
- **Cause**: State management issues
- **Solution**: Improved interview lifecycle management

## **🔧 Manual API Key Setup**

If you can't set up API keys right now:

1. **Use Fallback Questions**: System will work with predefined questions
2. **Questions Will Vary**: Each session gets different question order
3. **Full 10 Questions**: All question types supported
4. **Results Will Show**: Interview completion fixed

## **📊 Expected Behavior After Fixes**

1. **10 Questions**: Full interview length
2. **Unique Questions**: Different questions per session
3. **Proper Completion**: Interview ends correctly
4. **Results Display**: Scores and feedback shown
5. **Reports Generated**: PDF and text reports created

## **🧪 Testing Without API Keys**

The system will work with fallback questions:
- **Technical Positions**: 20 technical questions
- **Business Positions**: 20 behavioral questions  
- **General**: 25 mixed questions
- **Randomization**: Questions vary per session
