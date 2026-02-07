# Module 2: Interview Manager & Conversation Flow

## 🎯 Module Overview

The **Interview Manager & Conversation Flow** module is the brain of our AI Interview Engine. It orchestrates the entire interview process, manages conversation state, integrates with Google's Gemini API, and ensures a smooth, professional interview experience. This module transforms raw resume context into intelligent, contextual questions while maintaining conversation flow and session management.

## 🏗️ Architecture Diagram

```
Session Start
    │
    ▼
┌─────────────────┐
│ Session Manager │ ── Creates & tracks interview sessions
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Context Builder │ ── Builds system prompts from resume
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Gemini API Comm │ ── Communicates with Gemini API
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Question Engine │ ── Generates contextual questions
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Flow Controller │ ── Manages interview progression
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Response Proc   │ ── Processes user responses
└─────────────────┘
```

## 🛠️ Core Components

### 1. Interview Session Manager
**Purpose**: Create, track, and manage interview sessions throughout their lifecycle.

**Key Features**:
- Unique session ID generation and tracking
- Session state persistence
- Conversation history management
- Session metadata and analytics
- Automatic cleanup and timeout handling

**Session Lifecycle**:
```python
class InterviewSession:
    def __init__(self, user_id: str, resume_context: List[str]):
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        self.resume_context = resume_context
        self.chat_history = []
        self.question_count = 0
        self.current_phase = "behavioral"  # behavioral -> technical -> wrap_up
        self.user_responses = []
        self.session_metadata = {}
        self.start_time = datetime.now()
        self.last_activity = datetime.now()
        self.is_active = True
```

### 2. System Prompt & Context Builder
**Purpose**: Create intelligent system prompts that guide Gemini API to conduct professional interviews.

**Context Building Strategy**:
- **Resume Integration**: Incorporates candidate background into prompts
- **Dynamic Adaptation**: Adjusts based on candidate responses
- **Professional Tone**: Maintains consistent interview quality
- **Context Window Management**: Optimizes for Gemini's 1M+ token limit

**Prompt Engineering Principles**:
```python
class SystemPromptBuilder:
    def build_interview_context(self, resume_chunks: List[str]) -> str:
        """
        Creates comprehensive system prompt for interview conduct
        
        Components:
        1. Interviewer persona definition
        2. Candidate background summary
        3. Interview structure guidelines
        4. Response format specifications
        5. Professional conduct rules
        """
```

### 3. Gemini API Communication Layer
**Purpose**: Handle all interactions with Google's Gemini API efficiently and reliably.

**Key Features**:
- **API Client Management**: Maintains connection and authentication
- **Request Optimization**: Batches and optimizes API calls
- **Error Handling**: Robust error recovery and fallback mechanisms
- **Response Parsing**: Cleans and validates API responses
- **Rate Limiting**: Respects API limits (5 RPM, 25/day for free tier)

**API Configuration**:
```python
class GeminiAPIClient:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.7,        # Balanced creativity
            max_output_tokens=300,  # Concise questions
            top_p=0.9,             # Focused responses
            candidate_count=1       # Single response
        )
```

### 4. Question Generation Engine
**Purpose**: Generate contextual, relevant interview questions based on resume and conversation flow.

**Question Types & Progression**:
```python
INTERVIEW_PHASES = {
    'behavioral': {
        'focus': 'Experience and soft skills',
        'question_count': 3,
        'examples': [
            'Tell me about a challenging project you led',
            'Describe a time you worked in a difficult team situation',
            'How do you handle tight deadlines and pressure?'
        ]
    },
    'technical': {
        'focus': 'Technical competency and problem-solving',
        'question_count': 4,
        'examples': [
            'Walk me through your approach to system design',
            'How would you debug a performance issue in production?',
            'Explain a complex technical concept to a non-technical person'
        ]
    },
    'wrap_up': {
        'focus': 'Clarification and closing',
        'question_count': 1,
        'examples': [
            'Do you have any questions about the role or company?',
            'Is there anything else you\'d like to highlight?'
        ]
    }
}
```

**Adaptive Question Logic**:
```python
def generate_adaptive_question(self, session: InterviewSession, context: str):
    """
    Generates questions that adapt to:
    - Candidate's experience level (junior/mid/senior)
    - Previous responses quality
    - Technical domains mentioned in resume
    - Interview phase progression
    """
```

### 5. Conversation Flow Controller
**Purpose**: Manage interview progression, phase transitions, and conversation coherence.

**Flow Management**:
- **Phase Detection**: Automatically transitions between interview phases
- **Follow-up Logic**: Determines when to ask clarifying questions
- **Depth Control**: Adjusts question complexity based on responses
- **Time Management**: Ensures interview stays within reasonable duration

**Flow Decision Tree**:
```python
class ConversationFlowController:
    def determine_next_action(self, session: InterviewSession, user_response: str):
        """
        Decision logic:
        1. Assess response quality and completeness
        2. Check if follow-up needed
        3. Evaluate phase completion
        4. Determine next question type
        5. Check for interview termination conditions
        """
```

### 6. Response Processing System
**Purpose**: Analyze user responses and prepare context for next questions.

**Processing Pipeline**:
```python
class ResponseProcessor:
    def process_user_response(self, session_id: str, response: str):
        """
        1. Store response with metadata
        2. Extract key themes and topics
        3. Assess response quality
        4. Retrieve relevant resume context (RAG)
        5. Update session state
        6. Generate follow-up context
        """
```

## 🔧 Technical Implementation

### Dependencies & Setup
```bash
# Core dependencies
pip install google-generativeai==0.7.2
pip install python-dotenv==1.0.0
pip install asyncio==3.4.3
pip install uuid==1.30
pip install dataclasses==0.6
pip install typing-extensions==4.7.1

# Utility dependencies
pip install python-dateutil==2.8.2
pip install pytz==2023.3
pip install structlog==23.1.0
```

### Environment Configuration
```env
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_MAX_TOKENS=300
GEMINI_TEMPERATURE=0.7

# Interview Configuration
MAX_QUESTIONS_PER_INTERVIEW=8
SESSION_TIMEOUT_MINUTES=60
AUTO_CLEANUP_HOURS=24

# Rate Limiting
RPM_LIMIT=5
DAILY_LIMIT=25
BACKOFF_MULTIPLIER=2
MAX_RETRIES=3
```

### Core Classes Structure

```python
class InterviewManager:
    """Main orchestrator for interview sessions"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.prompt_builder = SystemPromptBuilder()
        self.gemini_client = GeminiAPIClient()
        self.question_engine = QuestionEngine()
        self.flow_controller = ConversationFlowController()
        self.response_processor = ResponseProcessor()
        
    async def start_interview(self, user_id: str, resume_context: List[str]):
        """Initialize new interview session"""
        
    async def process_response(self, session_id: str, user_response: str):
        """Process user response and generate next question"""
        
    async def end_interview(self, session_id: str):
        """Clean up and finalize interview session"""

class SessionManager:
    """Manages interview session lifecycle"""
    
    def __init__(self):
        self.active_sessions: Dict[str, InterviewSession] = {}
        self.session_cleanup_task = None
        
    def create_session(self, user_id: str, resume_context: List[str]) -> InterviewSession:
        """Create new interview session"""
        
    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        """Retrieve active session"""
        
    def update_session(self, session_id: str, **kwargs):
        """Update session metadata"""
        
    def cleanup_expired_sessions(self):
        """Remove expired/inactive sessions"""

class SystemPromptBuilder:
    """Constructs intelligent system prompts"""
    
    def build_initial_prompt(self, resume_context: List[str]) -> str:
        """Create system prompt for interview start"""
        
    def build_follow_up_prompt(self, session: InterviewSession, context: str) -> str:
        """Create prompt for follow-up questions"""
        
    def build_phase_transition_prompt(self, session: InterviewSession) -> str:
        """Create prompt for phase transitions"""

class GeminiAPIClient:
    """Handles all Gemini API communication"""
    
    def __init__(self):
        self.setup_client()
        self.rate_limiter = RateLimiter()
        
    async def generate_question(self, prompt: str) -> str:
        """Generate interview question via Gemini API"""
        
    async def validate_response(self, response: str) -> bool:
        """Validate API response quality"""
        
    def handle_api_error(self, error: Exception) -> str:
        """Handle API errors with fallbacks"""

class QuestionEngine:
    """Generates contextual interview questions"""
    
    def __init__(self):
        self.question_templates = self.load_templates()
        self.fallback_questions = self.load_fallbacks()
        
    async def generate_contextual_question(self, session: InterviewSession, context: str) -> str:
        """Generate question based on context and session state"""
        
    def get_fallback_question(self, session: InterviewSession) -> str:
        """Return appropriate fallback question"""
        
    def adapt_difficulty(self, question: str, experience_level: str) -> str:
        """Adjust question difficulty based on candidate level"""

class ConversationFlowController:
    """Manages interview flow and transitions"""
    
    def __init__(self):
        self.phase_rules = self.load_phase_rules()
        self.transition_logic = self.setup_transitions()
        
    def should_ask_follow_up(self, session: InterviewSession, response: str) -> bool:
        """Determine if follow-up question needed"""
        
    def should_transition_phase(self, session: InterviewSession) -> bool:
        """Check if phase transition is required"""
        
    def should_end_interview(self, session: InterviewSession) -> bool:
        """Determine if interview should conclude"""

class ResponseProcessor:
    """Processes and analyzes user responses"""
    
    def __init__(self):
        self.rag_system = None  # Injected from Module 1
        
    async def process_response(self, session: InterviewSession, response: str):
        """Complete response processing pipeline"""
        
    def extract_topics(self, response: str) -> List[str]:
        """Extract key topics and themes from response"""
        
    def assess_response_quality(self, response: str, question: str) -> float:
        """Score response quality (0.0 to 1.0)"""
```

## 🎯 Key Algorithms

### 1. Dynamic Question Generation Algorithm
```python
async def generate_dynamic_question(self, session: InterviewSession, user_response: str = None):
    """
    Multi-step question generation:
    
    1. Analyze current interview phase
    2. Extract relevant resume context via RAG
    3. Consider previous response quality
    4. Build contextual prompt
    5. Generate via Gemini API
    6. Validate and post-process
    """
    
    # Phase analysis
    current_phase = self.determine_current_phase(session)
    
    # Context retrieval (integration with Module 1)
    if user_response:
        relevant_context = await self.rag_system.retrieve_context(
            session.user_id, 
            user_response
        )
    else:
        relevant_context = session.resume_context[:3]  # Initial context
    
    # Prompt construction
    prompt = self.prompt_builder.build_contextual_prompt(
        phase=current_phase,
        resume_context=relevant_context,
        conversation_history=session.chat_history[-4:],  # Last 2 Q&A pairs
        user_response=user_response
    )
    
    # API call with error handling
    try:
        question = await self.gemini_client.generate_question(prompt)
        validated_question = self.validate_and_clean_question(question)
        return validated_question
    except Exception as e:
        # Fallback to template-based question
        return self.question_engine.get_fallback_question(session)
```

### 2. Interview Phase Transition Algorithm
```python
def determine_phase_transition(self, session: InterviewSession) -> str:
    """
    Phase transition logic based on:
    - Question count per phase
    - Response quality indicators  
    - Time elapsed
    - Conversation depth
    """
    
    current_phase = session.current_phase
    questions_in_phase = self.count_questions_in_phase(session, current_phase)
    avg_response_quality = self.calculate_avg_response_quality(session)
    
    transition_rules = {
        'behavioral': {
            'min_questions': 2,
            'max_questions': 4,
            'quality_threshold': 0.6,
            'next_phase': 'technical'
        },
        'technical': {
            'min_questions': 3,
            'max_questions': 5,
            'quality_threshold': 0.5,
            'next_phase': 'wrap_up'
        },
        'wrap_up': {
            'min_questions': 1,
            'max_questions': 2,
            'quality_threshold': 0.3,
            'next_phase': 'complete'
        }
    }
    
    rules = transition_rules.get(current_phase, {})
    
    # Check transition conditions
    if (questions_in_phase >= rules.get('min_questions', 0) and 
        (questions_in_phase >= rules.get('max_questions', 999) or 
         avg_response_quality >= rules.get('quality_threshold', 0.5))):
        return rules.get('next_phase', 'complete')
    
    return current_phase
```

### 3. Context-Aware Follow-up Logic
```python
def should_generate_follow_up(self, session: InterviewSession, response: str) -> bool:
    """
    Determines if a follow-up question is needed based on:
    - Response completeness
    - Technical depth achieved
    - Time constraints
    - Question quality
    """
    
    # Analyze response characteristics
    response_length = len(response.split())
    contains_examples = bool(re.search(r'\b(example|instance|time when|situation)\b', response, re.I))
    contains_technical_details = self.detect_technical_content(response)
    
    # Get last question context
    last_question = session.chat_history[-2]['content'] if len(session.chat_history) >= 2 else ""
    is_behavioral_question = self.is_behavioral_question(last_question)
    
    # Follow-up conditions
    conditions = {
        'too_short': response_length < 30,
        'lacks_examples': is_behavioral_question and not contains_examples,
        'lacks_technical_depth': not is_behavioral_question and not contains_technical_details,
        'within_time_limit': session.question_count < 8,
        'phase_appropriate': self.is_follow_up_appropriate(session.current_phase)
    }
    
    # Decision logic
    should_follow_up = (
        conditions['within_time_limit'] and 
        conditions['phase_appropriate'] and
        (conditions['too_short'] or 
         conditions['lacks_examples'] or 
         conditions['lacks_technical_depth'])
    )
    
    return should_follow_up
```

## 📊 Data Flow

### Interview Initiation Flow
```
1. Session Creation
   ├── Generate unique session ID
   ├── Initialize session state
   ├── Store resume context
   └── Set initial phase to 'behavioral'

2. Context Building
   ├── Analyze resume sections
   ├── Extract key experiences/skills
   ├── Build system prompt
   └── Set interview tone/style

3. First Question Generation
   ├── Create behavioral opening prompt
   ├── Call Gemini API
   ├── Validate response quality
   └── Return formatted question

4. Session Activation
   ├── Mark session as active
   ├── Start timeout timer
   ├── Log session creation
   └── Return session details
```

### Response Processing Flow
```
1. Response Reception
   ├── Validate session exists
   ├── Check session timeout
   ├── Store user response
   └── Update last activity

2. Response Analysis
   ├── Extract key themes/topics
   ├── Assess response quality
   ├── Determine completeness
   └── Check for follow-up needs

3. Context Retrieval (RAG)
   ├── Send response to Module 1
   ├── Get relevant resume context
   ├── Rank context by relevance
   └── Prepare for prompt building

4. Next Question Planning
   ├── Check phase transition needs
   ├── Determine question type
   ├── Build contextual prompt
   └── Prepare API call

5. Question Generation
   ├── Call Gemini API with prompt
   ├── Handle rate limiting
   ├── Validate response
   └── Format final question

6. Session Update
   ├── Update conversation history
   ├── Increment question count
   ├── Update phase if needed
   └── Check completion criteria
```

### Error Recovery Flow
```
1. Error Detection
   ├── API timeout/error
   ├── Rate limit exceeded
   ├── Invalid response format
   └── Session state corruption

2. Error Classification
   ├── Recoverable vs Non-recoverable
   ├── User-facing vs System error
   ├── Retry-able vs Fallback needed
   └── Priority level assignment

3. Recovery Strategy
   ├── API Retry with backoff
   ├── Fallback question selection
   ├── Session state reconstruction
   └── User notification if needed

4. Fallback Execution
   ├── Select appropriate fallback
   ├── Maintain conversation flow
   ├── Log error for analysis
   └── Continue interview process
```

## 🧪 Testing Strategy

### Unit Tests
```python
class TestInterviewManager:
    def test_session_creation(self):
        """Test interview session initialization"""
        
    def test_session_lifecycle(self):
        """Test session state management"""
        
    def test_cleanup_expired_sessions(self):
        """Test automatic session cleanup"""

class TestSystemPromptBuilder:
    def test_initial_prompt_generation(self):
        """Test system prompt creation"""
        
    def test_context_integration(self):
        """Test resume context integration"""
        
    def test_prompt_optimization(self):
        """Test prompt length and quality"""

class TestGeminiAPIClient:
    def test_api_communication(self):
        """Test successful API calls"""
        
    def test_rate_limiting(self):
        """Test rate limit handling"""
        
    def test_error_recovery(self):
        """Test API error scenarios"""

class TestQuestionEngine:
    def test_question_generation(self):
        """Test contextual question creation"""
        
    def test_difficulty_adaptation(self):
        """Test question difficulty scaling"""
        
    def test_fallback_mechanisms(self):
        """Test fallback question selection"""

class TestConversationFlowController:
    def test_phase_transitions(self):
        """Test interview phase management"""
        
    def test_follow_up_logic(self):
        """Test follow-up question decisions"""
        
    def test_interview_completion(self):
        """Test interview ending criteria"""

class TestResponseProcessor:
    def test_response_analysis(self):
        """Test response quality assessment"""
        
    def test_topic_extraction(self):
        """Test key topic identification"""
        
    def test_context_retrieval_integration(self):
        """Test RAG system integration"""
```

### Integration Tests
```python
class TestFullInterviewFlow:
    async def test_complete_interview_simulation(self):
        """Test full interview from start to finish"""
        
    async def test_multi_session_handling(self):
        """Test concurrent interview sessions"""
        
    async def test_rag_integration(self):
        """Test integration with Module 1 RAG system"""
        
    async def test_api_limit_scenarios(self):
        """Test behavior under API constraints"""
```

### Performance Tests
```python
class TestPerformance:
    def test_response_time_benchmarks(self):
        """Test API response times"""
        
    def test_memory_usage(self):
        """Test memory consumption"""
        
    def test_concurrent_session_limits(self):
        """Test system under load"""
```

## 🚀 Performance Optimization

### API Optimization
```python
# Connection pooling for Gemini API
class OptimizedGeminiClient:
    def __init__(self):
        self.session_pool = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=10,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
        )
        
    async def batch_generate(self, prompts: List[str]):
        """Batch multiple API calls for efficiency"""
```

### Memory Management
```python
# Efficient session storage
class OptimizedSessionManager:
    def __init__(self):
        self.session_cache = LRUCache(maxsize=100)
        self.cleanup_interval = 3600  # 1 hour
        
    def compress_session_history(self, session: InterviewSession):
        """Compress old conversation history to save memory"""
        if len(session.chat_history) > 10:
            # Keep only recent exchanges and summaries
            recent_history = session.chat_history[-6:]
            summary = self.summarize_early_conversation(session.chat_history[:-6])
            session.chat_history = [summary] + recent_history
```

### Caching Strategy
```python
# Cache frequent operations
@lru_cache(maxsize=50)
def get_fallback_question(phase: str, experience_level: str) -> str:
    """Cache fallback questions for quick retrieval"""
    
@lru_cache(maxsize=100)  
def build_system_prompt_template(resume_type: str) -> str:
    """Cache system prompt templates"""
```

## 🔧 Configuration Options

### Module Settings
```python
MODULE_CONFIG = {
    # Session Management
    'max_concurrent_sessions': 50,
    'session_timeout_minutes': 60,
    'cleanup_interval_hours': 1,
    
    # Interview Structure
    'max_questions_per_interview': 8,
    'behavioral_phase_questions': (2, 4),
    'technical_phase_questions': (3, 5),
    'wrap_up_phase_questions': (1, 2),
    
    # API Configuration
    'gemini_model': 'gemini-2.0-flash-exp',
    'max_tokens': 300,
    'temperature': 0.7,
    'top_p': 0.9,
    
    # Rate Limiting
    'requests_per_minute': 5,
    'requests_per_day': 25,
    'backoff_multiplier': 2,
    'max_retries': 3,
    
    # Quality Control
    'min_response_length': 20,
    'quality_threshold': 0.6,
    'follow_up_probability': 0.3
}
```

## 🔍 Error Handling

### Error Classification & Response
```python
class InterviewError(Exception):
    """Base exception for interview-related errors"""
    
class SessionError(InterviewError):
    """Session management errors"""
    
class APIError(InterviewError):
    """Gemini API related errors"""
    
class FlowError(InterviewError):
    """Conversation flow errors"""

# Error handling strategies
ERROR_STRATEGIES = {
    'SessionNotFound': {
        'action': 'return_error',
        'message': 'Interview session has expired or is invalid',
        'recovery': None
    },
    'RateLimitExceeded': {
        'action': 'fallback',
        'message': 'System temporarily busy, using prepared question',
        'recovery': 'use_fallback_question'
    },
    'APITimeout': {
        'action': 'retry_with_backoff',
        'message': 'Generating question, please wait...',
        'recovery': 'exponential_backoff'
    },
    'InvalidResponse': {
        'action': 'regenerate',
        'message': 'Reformulating question...',
        'recovery': 'retry_with_different_prompt'
    }
}
```

## 📈 Monitoring & Metrics

### Key Performance Indicators
```python
METRICS_TO_TRACK = {
    # Session Metrics
    'active_sessions': 'Number of concurrent interview sessions',
    'session_duration_avg': 'Average interview duration',
    'completion_rate': 'Percentage of interviews completed',
    
    # API Metrics
    'api_response_time': 'Gemini API response latency',
    'api_success_rate': 'Percentage of successful API calls',
    'rate_limit_hits': 'Frequency of rate limit encounters',
    
    # Quality Metrics
    'question_relevance_score': 'Quality of generated questions',
    'conversation_flow_score': 'Smoothness of conversation transitions',
    'user_engagement_score': 'Quality of user responses',
    
    # Error Metrics
    'error_rate_by_type': 'Breakdown of error types',
    'recovery_success_rate': 'Success rate of error recovery',
    'fallback_usage_rate': 'Frequency of fallback mechanisms'
}
```

### Structured Logging
```python
import structlog

logger = structlog.get_logger(__name__)

# Example logging throughout the module
logger.info(
    "interview_started",
    session_id=session.session_id,
    user_id=session.user_id,
    resume_sections_count=len(session.resume_context),
    estimated_duration_minutes=15
)

logger.info(
    "question_generated",
    session_id=session_id,
    question_number=session.question_count,
    phase=session.current_phase,
    generation_time_ms=generation_time,
    api_tokens_used=tokens_used
)

logger.warning(
    "api_rate_limit_encountered",
    session_id=session_id,
    retry_after_seconds=retry_after,
    fallback_used=True
)
```

## 🔗 Integration Points

### Input Interfaces
```python
# From Module 1 (Resume Processor)
async def receive_resume_context(user_id: str) -> List[str]:
    """Receives processed resume context for interview setup"""
    
async def request_relevant_context(user_id: str, query: str) -> List[str]:
    """Requests RAG-based context during interview"""

# From Module 4 (API Service Layer)
async def start_interview_request(user_id: str, resume_context: List[str]):
    """Handles interview start requests from API layer"""
    
async def process_response_request(session_id: str, response: str):
    """Handles user response processing requests"""
```

### Output Interfaces
```python
# To Module 3 (Feedback Generator)
def provide_interview_data(session_id: str) -> Dict:
    """Provides complete interview data for feedback generation"""
    
def provide_session_analytics(session_id: str) -> Dict:
    """Provides session metrics and analytics"""

# To Module 4 (API Service Layer)  
def return_interview_response(session_id: str, question: str, status: str):
    """Returns formatted response to API layer"""
    
def return_error_response(error_type: str, message: str):
    """Returns error information to API layer"""
```

## 🔄 Development Workflow

### Setup Instructions
```bash
# 1. Environment Setup
cd gemini-interview-engine/module2
python -m venv venv
source venv/bin/activate

# 2. Dependencies
pip install -r requirements-module2.txt

# 3. Environment Configuration  
cp .env.example .env
# Add your Gemini API key and configuration

# 4. Test Gemini API Connection
python scripts/test_gemini_connection.py

# 5. Initialize Module
python -m module2.main --test-mode

# 6. Run Tests
pytest tests/module2/ -v --cov=module2

# 7. Start Development Server
python -m module2.main --dev
```

### Development Tasks
```python
# Priority 1: Core Session Management
- [ ] Implement SessionManager class
- [ ] Create session lifecycle methods
- [ ] Add session timeout and cleanup
- [ ] Build session state persistence

# Priority 2: Gemini API Integration
- [ ] Set up GeminiAPIClient class
- [ ] Implement rate limiting logic
- [ ] Add error handling and retries
- [ ] Create response validation

# Priority 3: Question Generation System  
- [ ] Build SystemPromptBuilder
- [ ] Implement QuestionEngine class
- [ ] Create fallback question system
- [ ] Add difficulty adaptation logic

# Priority 4: Conversation Flow Control
- [ ] Implement ConversationFlowController
- [ ] Add phase transition logic
- [ ] Create follow-up decision system
- [ ] Build interview completion detection

# Priority 5: Response Processing
- [ ] Build ResponseProcessor class
- [ ] Integrate with Module 1 RAG system
- [ ] Add response quality assessment
- [ ] Create topic extraction logic

# Priority 6: Testing & Optimization
- [ ] Write comprehensive unit tests
- [ ] Add integration tests with Module 1
- [ ] Performance testing and optimization
- [ ] Error scenario testing
```

### Integration Milestones
```python
# Week 1: Foundation
- [ ] Basic session management working
- [ ] Gemini API connection established
- [ ] Simple question generation implemented

# Week 2: Intelligence  
- [ ] RAG integration with Module 1 complete
- [ ] Contextual question generation working
- [ ] Flow control logic implemented

# Week 3: Polish & Integration
- [ ] Error handling comprehensive
- [ ] Performance optimized
- [ ] Integration with Module 4 API layer
- [ ] Testing complete

# Week 4: Deployment Ready
- [ ] Production configuration ready
- [ ] Monitoring and logging implemented  
- [ ] Documentation complete
- [ ] Ready for Module 3 integration
```

---

## 📞 Support & Communication

### Getting Help
- **Technical Issues**: Create GitHub issue with `module-2` label
- **Gemini API Issues**: Check Google AI documentation first
- **Integration Questions**: Coordinate with Module 1 and 4 developers
- **Architecture Decisions**: Tag team lead for review

### Code Review Checklist
- [ ] All async functions properly awaited
- [ ] Error handling for all external calls (Gemini API, Module 1)
- [ ] Rate limiting properly implemented
- [ ] Session management memory-efficient
- [ ] Integration points clearly documented
- [ ] Unit tests cover >80% of code paths
- [ ] Performance considerations addressed

---

*This module is the heart of the interview experience. Focus on creating natural, contextual conversations while maintaining professional quality and robust error handling.*