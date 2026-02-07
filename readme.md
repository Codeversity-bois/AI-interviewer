# Gemini AI Interview Engine

## 🎯 Project Overview

The **Gemini AI Interview Engine** is the core intelligence module of our AI Interviewer system. It conducts professional, contextual interviews using Google's Gemini API with RAG (Retrieval-Augmented Generation) capabilities for resume-aware questioning and comprehensive feedback generation.

### 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Gemini AI Interview Engine                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   Module 1       │  │   Module 2       │  │   Module 3       │  │
│  │ Resume Processor │  │Interview Manager │  │Feedback Generator│  │
│  │   & RAG System   │  │  & Conversation  │  │   & Analytics    │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│           │                       │                       │        │
│           └───────────────────────┼───────────────────────┘        │
│                                   │                                │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Module 4 - API Service Layer                   │ │
│  │         (Flask REST API & Rate Limit Management)            │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                   │
                          ┌────────▼────────┐
                          │   Astra DB      │
                          │ Vector Storage  │
                          └─────────────────┘
```

## 🗃️ Module Breakdown

### Module 1: Resume Processor & RAG System
**👤 Developer: Person A**

**Responsibility**: PDF parsing, text chunking, embedding generation, and vector storage in Astra DB.

**Core Components**:
- PDF resume parsing with PyPDF2
- Intelligent text chunking by resume sections
- Sentence embedding generation using SentenceTransformer
- Astra DB integration for vector storage and retrieval
- Context retrieval based on user responses

### Module 2: Interview Manager & Conversation Flow
**👤 Developer: Person B**

**Responsibility**: Session management, conversation flow control, and Gemini API integration.

**Core Components**:
- Interview session lifecycle management
- Conversation history tracking
- Gemini API communication and prompt engineering
- Dynamic question generation based on context
- Interview flow logic (behavioral → technical → wrap-up)

### Module 3: Feedback Generator & Analytics
**👤 Developer: Person A or B (whoever finishes first)**

**Responsibility**: Post-interview analysis, comprehensive feedback generation, and scoring.

**Core Components**:
- Interview transcript analysis
- Performance scoring algorithms
- Structured feedback generation using Gemini
- JSON response parsing and validation
- Session analytics and metrics

### Module 4: API Service Layer
**👤 Developer: Both (Integration Phase)**

**Responsibility**: REST API endpoints, rate limiting, error handling, and service coordination.

**Core Components**:
- Flask REST API with CORS support
- Rate limit management for Gemini free tier
- Request validation and error handling
- Module integration and orchestration
- Health checks and monitoring endpoints

## 🛠️ Technology Stack

### Core Dependencies
```bash
pip install google-generativeai==0.7.2
pip install python-dotenv==1.0.0
pip install flask==3.0.0
pip install flask-cors==4.0.0
pip install sentence-transformers==2.2.2
pip install PyPDF2==3.0.1
pip install cassio==0.1.7  # For Astra DB integration
pip install astrapy==1.0.0
```

### Environment Configuration
```env
GEMINI_API_KEY=your_gemini_api_key_here
ASTRA_DB_ID=your_astra_db_id
ASTRA_DB_REGION=your_astra_db_region
ASTRA_DB_KEYSPACE=interview_system
ASTRA_DB_TOKEN=your_astra_db_token
```

## 📊 Data Flow Architecture

### 1. Interview Initiation Flow
```
PDF Upload → Resume Parser → Text Chunking → Embedding Generation → 
Astra DB Storage → Context Building → First Question Generation
```

### 2. Conversation Flow
```
User Response → Context Retrieval (RAG) → Gemini Prompt Building → 
Question Generation → Session Update → Response Delivery
```

### 3. Feedback Generation Flow
```
Interview Completion → Transcript Analysis → Performance Scoring → 
Feedback Generation → JSON Validation → Response Delivery
```

## 🗄️ Astra DB Schema

### Collections Structure

**Collection: `resume_embeddings`**
```json
{
    "user_id": "string",
    "chunk_id": "integer", 
    "content": "string",
    "embedding": "vector",
    "section_type": "string",
    "created_at": "timestamp"
}
```

**Collection: `interview_sessions`**
```json
{
    "session_id": "string",
    "user_id": "string", 
    "chat_history": "array",
    "session_metadata": "object",
    "created_at": "timestamp",
    "updated_at": "timestamp"
}
```

## 🔄 API Endpoints

### Core Interview Endpoints
```
POST /start_interview
- Accepts: multipart/form-data (resume PDF)
- Returns: session_id, first_question

POST /process_response  
- Accepts: {"session_id": string, "response": string}
- Returns: next_question or interview_complete status

POST /generate_feedback/{session_id}
- Returns: comprehensive feedback JSON
```

### Health & Monitoring
```
GET /health
- Returns: system status, active sessions, rate limit status
```

## ⚡ Rate Limiting Strategy

### Gemini API Free Tier Constraints
- **RPM Limit**: 5 requests per minute
- **Daily Limit**: 25 requests per day  
- **Context Window**: 1M+ tokens available

### Implementation Strategy
- Intelligent rate limiting with backoff
- Fallback question templates for limit hits
- Session-based token optimization
- Graceful degradation with pre-written questions

## 🔧 Module Integration Points

### Inter-Module Communication
```python
# Module 1 → Module 2
resume_context = rag_system.get_relevant_context(user_id, query)

# Module 2 → Module 3  
interview_data = session_manager.get_session_summary(session_id)

# All Modules → Module 4
api_response = service_layer.coordinate_response(request_data)
```

### Shared Interfaces
```python
class InterviewSession:
    # Shared data structure across modules
    
class GeminiAPIClient:
    # Centralized API communication
    
class AstraDBConnector:
    # Database abstraction layer
```

## 🎯 Development Workflow

### Phase 1: Individual Module Development (Week 1-2)
- **Module 1**: Implement resume parsing and Astra DB integration
- **Module 2**: Develop session management and Gemini integration  
- **Module 3**: Create feedback generation system
- **Module 4**: Set up basic Flask API structure

### Phase 2: Integration & Testing (Week 3)
- Integrate all modules through Module 4 API layer
- End-to-end testing with sample resumes
- Rate limit testing and optimization
- Error handling and edge case management

### Phase 3: Optimization & Deployment (Week 4)
- Performance optimization
- Security hardening
- Documentation completion
- Deployment preparation

## 🧪 Testing Strategy

### Unit Testing (Per Module)
```python
# Module 1 Tests
test_pdf_parsing()
test_chunking_logic() 
test_astra_db_operations()

# Module 2 Tests  
test_session_management()
test_gemini_integration()
test_conversation_flow()

# Module 3 Tests
test_feedback_generation()
test_scoring_algorithms()

# Module 4 Tests
test_api_endpoints()
test_rate_limiting()
test_error_handling()
```

### Integration Testing
```python
test_full_interview_flow()
test_concurrent_sessions()
test_api_rate_limits()
test_astra_db_performance()
```

## 🚀 Deployment Considerations

### Environment Setup
- Python 3.9+ runtime environment
- Astra DB cluster provisioning
- Gemini API key management
- CORS configuration for frontend integration

### Performance Optimization
- Connection pooling for Astra DB
- Caching strategies for frequent queries
- Async processing for non-critical operations
- Memory management for embeddings

### Security Measures
- API key encryption and rotation
- Input validation and sanitization
- Rate limiting per IP/session
- Secure session management

## 📈 Monitoring & Analytics

### Key Metrics to Track
- API response times
- Gemini API usage and limits
- Interview completion rates
- Feedback quality scores
- System error rates
- Astra DB query performance

### Logging Strategy
- Structured logging with JSON format
- Error tracking with stack traces
- Performance monitoring
- User interaction analytics

## 🔮 Future Enhancements

### Planned Features
- Multi-language interview support
- Industry-specific question templates
- Real-time interview difficulty adjustment
- Integration with external assessment tools
- Bulk interview scheduling and management

### Scalability Considerations
- Microservice architecture migration
- Load balancing for multiple instances
- Database sharding strategies
- CDN integration for static assets

---

## 🤝 Team Collaboration

### Git Workflow
```bash
# Main branch: main
# Feature branches: feature/module-{1,2,3,4}-{feature-name}
# Integration branch: develop

# Example branch naming
feature/module-1-resume-parser
feature/module-2-gemini-integration
feature/module-3-feedback-system
feature/module-4-api-endpoints
```

### Code Standards
- Python PEP 8 compliance
- Type hints for all function parameters
- Comprehensive docstrings
- Unit test coverage > 80%
- Integration test for critical paths

### Communication Protocol
- Daily standups for progress sync
- Code review for all pull requests
- Documentation updates with each feature
- Integration testing before merging

---

*This README serves as the technical specification and development guide for the Gemini AI Interview Engine. Update this document as modules evolve and new requirements emerge.*
