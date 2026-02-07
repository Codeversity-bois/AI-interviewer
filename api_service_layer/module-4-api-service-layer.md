# Module 4: API Service Layer

## 🎯 Module Overview

The **API Service Layer** is the orchestration hub of our Gemini AI Interview Engine. It provides RESTful endpoints, coordinates all modules, manages rate limiting, handles authentication, and ensures reliable service delivery. This module serves as the single point of contact for frontend applications and integrates seamlessly with existing STT/TTS microservices.

## 🏗️ Architecture Diagram

```
External Clients (Frontend/STT/TTS)
    │
    ▼
┌─────────────────┐
│ Load Balancer   │ ── Distributes incoming requests
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ API Gateway     │ ── Authentication, rate limiting
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Request Router  │ ── Routes to appropriate endpoints
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Service Layer   │ ── Orchestrates module operations
└─────────────────┘
    │
    ├─── Module 1 (Resume Processor)
    ├─── Module 2 (Interview Manager)
    └─── Module 3 (Feedback Generator)
```

## 🛠️ Core Components

### 1. Flask Application & Route Management
**Purpose**: Provide RESTful API endpoints with proper HTTP semantics and error handling.

**Key Features**:
- **RESTful Design**: Follows REST principles for intuitive API usage
- **CORS Support**: Enables cross-origin requests for web frontends
- **Request Validation**: Validates input data and file uploads
- **Response Formatting**: Consistent JSON response structure
- **Health Monitoring**: System health and status endpoints

**API Structure**:
```python
class APIServiceLayer:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_cors()
        self.setup_routes()
        self.setup_error_handlers()
        
        # Module integrations
        self.resume_processor = ResumeProcessorRAG()
        self.interview_manager = InterviewManager()
        self.feedback_generator = FeedbackAnalyticsEngine()
```

### 2. Request Validation & Processing
**Purpose**: Ensure data integrity and security for all incoming requests.

**Validation Components**:
- **File Upload Validation**: PDF format, size limits, security scanning
- **JSON Schema Validation**: Request body structure validation
- **Session Management**: Session ID validation and lifecycle
- **Rate Limiting**: Per-client request limiting
- **Input Sanitization**: XSS and injection prevention

**Validation Pipeline**:
```python
class RequestValidator:
    def __init__(self):
        self.file_validator = FileUploadValidator()
        self.json_validator = JSONSchemaValidator()
        self.session_validator = SessionValidator()
        
    def validate_interview_start(self, request):
        """Comprehensive validation for interview start requests"""
        
    def validate_response_processing(self, request):
        """Validation for user response processing"""
```

### 3. Rate Limiting & Traffic Management
**Purpose**: Manage API usage to stay within Gemini API constraints and ensure fair usage.

**Rate Limiting Strategy**:
- **Global Rate Limiting**: Overall system request limits
- **Per-Client Limiting**: Individual client usage tracking  
- **Adaptive Throttling**: Dynamic adjustment based on API availability
- **Queue Management**: Request queuing during peak usage
- **Graceful Degradation**: Fallback responses when limits exceeded

**Rate Limiter Implementation**:
```python
class IntelligentRateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis()  # For distributed rate limiting
        self.gemini_limits = {
            'rpm': 5,    # Requests per minute
            'rpd': 25    # Requests per day
        }
        self.client_limits = {
            'rpm_per_client': 2,
            'concurrent_sessions': 3
        }
        
    def check_rate_limit(self, client_id: str, endpoint: str) -> RateLimitResult:
        """Check if request is within rate limits"""
        
    def apply_backoff_strategy(self, limit_type: str) -> int:
        """Calculate backoff time for rate limit recovery"""
```

### 4. Service Orchestration Layer
**Purpose**: Coordinate operations across all modules while maintaining consistency and reliability.

**Orchestration Responsibilities**:
- **Module Communication**: Manages inter-module data flow
- **Transaction Management**: Ensures data consistency across operations
- **Error Propagation**: Handles and transforms errors from modules
- **State Synchronization**: Maintains consistent state across modules
- **Performance Monitoring**: Tracks module performance and health

**Service Coordinator**:
```python
class ServiceOrchestrator:
    def __init__(self):
        self.module1 = ResumeProcessorRAG()
        self.module2 = InterviewManager()
        self.module3 = FeedbackGenerator()
        
        self.state_manager = StateManager()
        self.transaction_manager = TransactionManager()
        
    async def orchestrate_interview_start(self, file, metadata):
        """Coordinate interview initiation across modules"""
        
    async def orchestrate_response_processing(self, session_id, response):
        """Coordinate response processing workflow"""
        
    async def orchestrate_feedback_generation(self, session_id):
        """Coordinate comprehensive feedback generation"""
```

### 5. Error Handling & Recovery
**Purpose**: Provide robust error handling with graceful degradation and recovery mechanisms.

**Error Management Strategy**:
- **Error Classification**: Categorize errors by severity and type
- **Graceful Degradation**: Fallback mechanisms for service failures
- **Circuit Breaker**: Prevent cascade failures across modules
- **Retry Logic**: Intelligent retry strategies with exponential backoff
- **User-Friendly Messages**: Transform technical errors to user-friendly responses

**Error Handler Architecture**:
```python
class ErrorHandler:
    def __init__(self):
        self.circuit_breakers = {}
        self.retry_strategies = {}
        self.fallback_responses = {}
        
    def handle_module_error(self, error: Exception, module: str, operation: str):
        """Handle errors from specific modules with appropriate strategy"""
        
    def create_user_friendly_response(self, error: Exception) -> Dict:
        """Transform technical errors into user-friendly responses"""
```

### 6. Integration Management
**Purpose**: Seamlessly integrate with existing STT/TTS microservices and future extensions.

**Integration Features**:
- **Microservice Communication**: HTTP/gRPC communication protocols
- **Service Discovery**: Automatic discovery of available services  
- **Health Checks**: Monitor dependency service health
- **Fallback Services**: Backup options for critical dependencies
- **API Versioning**: Support multiple API versions for backward compatibility

**Integration Layer**:
```python
class IntegrationManager:
    def __init__(self):
        self.stt_service = STTServiceClient()
        self.tts_service = TTSServiceClient()
        self.health_checker = ServiceHealthChecker()
        
    async def process_audio_interview(self, audio_file, session_id):
        """Integrate with STT/TTS for audio-based interviews"""
        
    def check_service_health(self) -> Dict:
        """Check health of all integrated services"""
```

## 🔧 Technical Implementation

### Dependencies & Setup
```bash
# Core Flask dependencies
pip install flask==3.0.0
pip install flask-cors==4.0.0
pip install flask-limiter==3.5.0
pip install gunicorn==21.2.0

# Validation and security
pip install marshmallow==3.20.0
pip install flask-wtf==1.1.1
pip install python-multipart==0.0.6

# Async support
pip install flask[async]==3.0.0
pip install aiohttp==3.8.5

# Monitoring and logging
pip install prometheus-client==0.17.1
pip install structlog==23.1.0
pip install sentry-sdk==1.32.0

# Caching and session management
pip install redis==4.6.0
pip install flask-session==0.5.0

# Integration support
pip install requests==2.31.0
pip install httpx==0.24.1
```

### Environment Configuration
```env
# Flask Application Settings
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your-secret-key-here
API_VERSION=v1

# Rate Limiting Configuration
RATE_LIMIT_STORAGE=redis://localhost:6379/0
GLOBAL_RATE_LIMIT=100/hour
PER_CLIENT_RATE_LIMIT=20/hour

# Service Integration
STT_SERVICE_URL=http://localhost:8001
TTS_SERVICE_URL=http://localhost:8002
HEALTH_CHECK_INTERVAL=30

# Security Settings
CORS_ORIGINS=http://localhost:3000,https://your-frontend.com
UPLOAD_MAX_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=pdf

# Monitoring
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO
```

### Core Classes Structure

```python
class GeminiInterviewAPI:
    """Main Flask application class"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_configuration()
        self.setup_dependencies()
        self.setup_middleware()
        self.setup_routes()
        self.setup_error_handlers()
        
    def create_app(self) -> Flask:
        """Application factory pattern"""
        return self.app

class APIEndpoints:
    """Defines all API endpoints and their handlers"""
    
    def __init__(self, orchestrator: ServiceOrchestrator):
        self.orchestrator = orchestrator
        self.validator = RequestValidator()
        
    def setup_interview_endpoints(self):
        """Setup interview-related endpoints"""
        
    def setup_feedback_endpoints(self):
        """Setup feedback-related endpoints"""
        
    def setup_integration_endpoints(self):
        """Setup STT/TTS integration endpoints"""

class RequestValidator:
    """Handles request validation and sanitization"""
    
    def __init__(self):
        self.file_validator = FileValidator()
        self.schema_validator = SchemaValidator()
        
    def validate_file_upload(self, file) -> ValidationResult:
        """Validate uploaded resume files"""
        
    def validate_json_request(self, data, schema) -> ValidationResult:
        """Validate JSON request bodies"""

class ResponseFormatter:
    """Standardizes API response formats"""
    
    @staticmethod
    def success_response(data: Any, message: str = "Success") -> Dict:
        """Format successful responses"""
        
    @staticmethod
    def error_response(error_code: str, message: str, details: Dict = None) -> Dict:
        """Format error responses"""

class ServiceOrchestrator:
    """Coordinates operations across all modules"""
    
    def __init__(self):
        self.resume_processor = None  # Injected
        self.interview_manager = None  # Injected  
        self.feedback_generator = None  # Injected
        
    async def execute_workflow(self, workflow_type: str, **kwargs) -> Dict:
        """Execute complete workflows across modules"""
```

## 🎯 API Endpoints

### Core Interview Endpoints

#### Start Interview
```python
@app.route('/api/v1/interview/start', methods=['POST'])
async def start_interview():
    """
    Start a new interview session
    
    Request:
    - File: resume.pdf (multipart/form-data)
    - Optional: metadata (JSON)
    
    Response:
    {
        "status": "success",
        "session_id": "uuid-string",
        "first_question": "Tell me about yourself...",
        "question_number": 1,
        "estimated_duration": 15
    }
    """
```

#### Process Response
```python
@app.route('/api/v1/interview/<session_id>/response', methods=['POST'])
async def process_response(session_id):
    """
    Process user response and get next question
    
    Request:
    {
        "response": "I have 5 years of experience in...",
        "response_time_ms": 15000
    }
    
    Response:
    {
        "status": "continue|complete",
        "next_question": "Can you elaborate on...",
        "question_number": 2,
        "phase": "behavioral|technical|wrap_up"
    }
    """
```

#### Generate Feedback
```python
@app.route('/api/v1/interview/<session_id>/feedback', methods=['POST'])
async def generate_feedback(session_id):
    """
    Generate comprehensive interview feedback
    
    Response:
    {
        "status": "success",
        "feedback": {
            "overall_score": 7.5,
            "strengths": ["Clear communication", "Strong examples"],
            "improvements": ["More technical depth needed"],
            "detailed_analysis": {...}
        },
        "report_url": "/api/v1/reports/session_id.pdf"
    }
    """
```

### Integration Endpoints

#### Audio Interview Processing
```python
@app.route('/api/v1/interview/<session_id>/audio', methods=['POST'])
async def process_audio_response(session_id):
    """
    Process audio response through STT integration
    
    Request:
    - File: audio.wav (multipart/form-data)
    - session_id: string
    
    Response:
    {
        "transcribed_text": "I worked on a project where...",
        "next_question": "Can you tell me more about...",
        "audio_question_url": "https://tts-service/audio/question.wav"
    }
    """
```

### System Endpoints

#### Health Check
```python
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """
    System health status
    
    Response:
    {
        "status": "healthy|degraded|down",
        "timestamp": "2025-09-23T00:00:00Z",
        "services": {
            "gemini_api": "operational",
            "astra_db": "operational",
            "stt_service": "operational",
            "tts_service": "operational"
        },
        "metrics": {
            "active_sessions": 5,
            "api_calls_today": 180,
            "average_response_time": 250
        }
    }
    """
```

#### System Metrics
```python
@app.route('/api/v1/metrics', methods=['GET'])
def get_metrics():
    """
    Detailed system metrics for monitoring
    
    Response:
    {
        "request_metrics": {...},
        "performance_metrics": {...},
        "error_metrics": {...},
        "resource_usage": {...}
    }
    """
```

## 📊 Data Flow Architecture

### Interview Initiation Flow
```
1. Request Reception
   ├── Validate file upload (PDF, size, security)
   ├── Generate unique session ID
   ├── Apply rate limiting checks
   └── Log request initiation

2. Resume Processing
   ├── Call Module 1: parse PDF and extract text
   ├── Call Module 1: generate embeddings and store in Astra DB
   ├── Validate processing success
   └── Handle processing errors

3. Interview Setup
   ├── Call Module 2: initialize interview session
   ├── Call Module 2: generate first question
   ├── Store session metadata
   └── Prepare response

4. Response Delivery
   ├── Format successful response
   ├── Update system metrics
   ├── Log successful interview start
   └── Return to client
```

### Response Processing Flow
```
1. Request Validation
   ├── Validate session exists and is active
   ├── Validate response content and format
   ├── Check rate limits and quotas
   └── Log request details

2. Response Analysis
   ├── Call Module 2: process user response
   ├── Call Module 1: retrieve relevant context (RAG)
   ├── Call Module 2: generate next question
   └── Handle generation errors

3. Flow Management
   ├── Determine interview phase and progress
   ├── Check completion criteria
   ├── Update session state
   └── Prepare appropriate response

4. Response Formatting
   ├── Format next question or completion message
   ├── Include metadata (phase, progress)
   ├── Update performance metrics
   └── Return formatted response
```

### Error Handling Flow
```
1. Error Detection
   ├── Module-specific errors
   ├── Network/connectivity errors
   ├── Rate limit violations
   └── Validation failures

2. Error Classification
   ├── Severity assessment (critical/warning/info)
   ├── Recovery possibility evaluation
   ├── User impact assessment
   └── Monitoring alert triggers

3. Recovery Strategy
   ├── Automatic retry with exponential backoff
   ├── Fallback to alternative methods
   ├── Circuit breaker activation
   └── Graceful degradation

4. User Communication
   ├── Transform technical errors to user-friendly messages
   ├── Provide actionable guidance
   ├── Include retry mechanisms
   └── Log for system monitoring
```

## 🧪 Testing Strategy

### Unit Tests
```python
class TestAPIEndpoints:
    def test_start_interview_valid_request(self):
        """Test successful interview initiation"""
        
    def test_start_interview_invalid_file(self):
        """Test handling of invalid file uploads"""
        
    def test_process_response_valid_session(self):
        """Test response processing for active session"""
        
    def test_process_response_expired_session(self):
        """Test handling of expired sessions"""

class TestRateLimiting:
    def test_rate_limit_enforcement(self):
        """Test rate limit application"""
        
    def test_rate_limit_recovery(self):
        """Test recovery after rate limit period"""
        
    def test_per_client_limiting(self):
        """Test individual client rate limiting"""

class TestServiceOrchestration:
    def test_module_coordination(self):
        """Test coordination between modules"""
        
    def test_error_propagation(self):
        """Test error handling across modules"""
        
    def test_transaction_management(self):
        """Test data consistency across operations"""

class TestIntegration:
    def test_stt_integration(self):
        """Test STT service integration"""
        
    def test_tts_integration(self):
        """Test TTS service integration"""
        
    def test_service_health_checks(self):
        """Test dependency health monitoring"""
```

### Integration Tests
```python
class TestFullAPIWorkflow:
    async def test_complete_interview_flow(self):
        """Test full interview from start to feedback"""
        
    async def test_concurrent_interviews(self):
        """Test handling multiple simultaneous interviews"""
        
    async def test_audio_interview_workflow(self):
        """Test complete audio interview integration"""

class TestPerformance:
    def test_response_time_benchmarks(self):
        """Test API response time requirements"""
        
    def test_concurrent_load_handling(self):
        """Test system under concurrent load"""
        
    def test_memory_usage_efficiency(self):
        """Test memory consumption under load"""
```

### End-to-End Tests
```python
class TestE2EScenarios:
    async def test_typical_user_journey(self):
        """Test complete user interview experience"""
        
    async def test_error_scenarios(self):
        """Test various error conditions and recovery"""
        
    async def test_system_limits(self):
        """Test behavior at system capacity limits"""
```

## 🚀 Performance Optimization

### Async Request Handling
```python
# Asynchronous endpoint handling for better performance
from flask import Flask
import asyncio

class AsyncAPILayer:
    def __init__(self):
        self.app = Flask(__name__)
        
    @app.route('/api/v1/interview/start', methods=['POST'])
    async def async_start_interview():
        """Async interview initiation for better throughput"""
        
        # Process file upload asynchronously
        resume_task = asyncio.create_task(
            self.orchestrator.process_resume_async(file)
        )
        
        # Initialize session concurrently
        session_task = asyncio.create_task(
            self.orchestrator.initialize_session_async(user_data)
        )
        
        # Wait for both operations
        resume_result, session_result = await asyncio.gather(
            resume_task, session_task
        )
        
        return self.format_response(resume_result, session_result)
```

### Caching Strategy
```python
# Redis-based caching for frequently accessed data
import redis
from functools import wraps

class CachingLayer:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
        
    def cache_response(self, expiry=300):
        """Decorator for caching API responses"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = self.generate_cache_key(func.__name__, args, kwargs)
                
                # Try to get cached response
                cached = self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
                
                # Generate new response and cache it
                response = await func(*args, **kwargs)
                self.redis_client.setex(
                    cache_key, 
                    expiry, 
                    json.dumps(response)
                )
                
                return response
            return wrapper
        return decorator
```

### Connection Pooling
```python
# Efficient database and HTTP connection management
import aiohttp
from aiohttp_session import setup
from aiohttp_session.redis_storage import RedisStorage

class ConnectionManager:
    def __init__(self):
        self.http_session = None
        self.redis_pool = None
        
    async def initialize_connections(self):
        """Initialize connection pools"""
        
        # HTTP connection pool for external services
        connector = aiohttp.TCPConnector(
            limit=100,          # Total connection pool size
            limit_per_host=30,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True
        )
        
        self.http_session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # Redis connection pool
        self.redis_pool = redis.ConnectionPool(
            host='localhost',
            port=6379,
            max_connections=20
        )
```

## 🔧 Configuration Management

### Application Configuration
```python
import os
from dataclasses import dataclass

@dataclass
class APIConfig:
    """Centralized configuration management"""
    
    # Flask Configuration
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG: bool = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    HOST: str = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT: int = int(os.getenv('FLASK_PORT', '5000'))
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    GLOBAL_RATE_LIMIT: str = os.getenv('GLOBAL_RATE_LIMIT', '100/hour')
    PER_CLIENT_RATE_LIMIT: str = os.getenv('PER_CLIENT_RATE_LIMIT', '20/hour')
    
    # File Upload
    MAX_CONTENT_LENGTH: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_EXTENSIONS: set = {'pdf'}
    
    # Service Integration
    STT_SERVICE_URL: str = os.getenv('STT_SERVICE_URL', 'http://localhost:8001')
    TTS_SERVICE_URL: str = os.getenv('TTS_SERVICE_URL', 'http://localhost:8002')
    
    # Monitoring
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 30
    
    # Security
    CORS_ORIGINS: list = os.getenv('CORS_ORIGINS', '').split(',')
    API_KEY_REQUIRED: bool = os.getenv('API_KEY_REQUIRED', 'false').lower() == 'true'

# Configuration factory
def create_config(env: str = None) -> APIConfig:
    """Create configuration based on environment"""
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()
```

### Runtime Configuration
```python
# Dynamic configuration updates
class ConfigManager:
    def __init__(self):
        self.config = create_config()
        self.watchers = {}
        
    def update_rate_limits(self, new_limits: Dict):
        """Dynamically update rate limiting configuration"""
        self.config.GLOBAL_RATE_LIMIT = new_limits.get('global')
        self.config.PER_CLIENT_RATE_LIMIT = new_limits.get('per_client')
        
        # Notify rate limiter of changes
        if 'rate_limiter' in self.watchers:
            self.watchers['rate_limiter'].update_limits(new_limits)
    
    def register_watcher(self, name: str, callback):
        """Register configuration change watchers"""
        self.watchers[name] = callback
```

## 🔍 Error Handling Strategy

### Error Classification System
```python
from enum import Enum
from dataclasses import dataclass

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"  
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    MODULE_ERROR = "module_error"
    INTEGRATION = "integration"
    SYSTEM = "system"

@dataclass
class APIError:
    code: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    details: dict = None
    recovery_suggestions: list = None

# Error definitions
ERROR_DEFINITIONS = {
    'INVALID_FILE_FORMAT': APIError(
        code='INVALID_FILE_FORMAT',
        message='Only PDF files are supported',
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        recovery_suggestions=['Upload a PDF file instead']
    ),
    'SESSION_NOT_FOUND': APIError(
        code='SESSION_NOT_FOUND',
        message='Interview session not found or expired',
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        recovery_suggestions=['Start a new interview session']
    ),
    'RATE_LIMIT_EXCEEDED': APIError(
        code='RATE_LIMIT_EXCEEDED',
        message='Too many requests. Please try again later.',
        category=ErrorCategory.RATE_LIMIT,
        severity=ErrorSeverity.MEDIUM,
        recovery_suggestions=['Wait before making another request', 'Check rate limit headers']
    )
}
```

### Recovery Mechanisms
```python
class ErrorRecoveryManager:
    def __init__(self):
        self.circuit_breakers = {}
        self.retry_policies = {}
        
    async def execute_with_recovery(self, operation, recovery_strategy):
        """Execute operation with automatic recovery"""
        
        max_retries = recovery_strategy.get('max_retries', 3)
        backoff_factor = recovery_strategy.get('backoff_factor', 2)
        
        for attempt in range(max_retries + 1):
            try:
                result = await operation()
                return result
                
            except Exception as e:
                if attempt == max_retries:
                    # Final attempt failed, apply fallback
                    return await self.apply_fallback(e, recovery_strategy)
                
                # Wait before retry with exponential backoff
                wait_time = backoff_factor ** attempt
                await asyncio.sleep(wait_time)
                
                logger.warning(
                    f"Operation failed, retrying in {wait_time}s",
                    attempt=attempt + 1,
                    error=str(e)
                )
    
    async def apply_fallback(self, error, strategy):
        """Apply fallback mechanism when all retries fail"""
        
        fallback_type = strategy.get('fallback_type')
        
        if fallback_type == 'cached_response':
            return await self.get_cached_fallback(error)
        elif fallback_type == 'degraded_service':
            return await self.provide_degraded_service(error)
        elif fallback_type == 'queue_for_retry':
            return await self.queue_for_later_processing(error)
        else:
            raise error  # No fallback available
```

## 📈 Monitoring & Observability

### Metrics Collection
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Define metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'Request duration')
ACTIVE_SESSIONS = Gauge('active_interview_sessions', 'Number of active sessions')
ERROR_COUNT = Counter('api_errors_total', 'Total API errors', ['error_type'])

class MetricsCollector:
    def __init__(self):
        self.custom_metrics = {}
        
    def record_request(self, method: str, endpoint: str, duration: float):
        """Record request metrics"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_DURATION.observe(duration)
        
    def record_error(self, error_type: str):
        """Record error metrics"""
        ERROR_COUNT.labels(error_type=error_type).inc()
        
    def update_active_sessions(self, count: int):
        """Update active session count"""
        ACTIVE_SESSIONS.set(count)
        
    @app.route('/metrics')
    def metrics_endpoint():
        """Prometheus metrics endpoint"""
        return generate_latest()
```

### Structured Logging
```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage throughout the API
@app.before_request
def log_request_info():
    logger.info(
        "api_request_started",
        method=request.method,
        endpoint=request.endpoint,
        client_ip=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )

@app.after_request  
def log_request_completion(response):
    logger.info(
        "api_request_completed",
        method=request.method,
        endpoint=request.endpoint,
        status_code=response.status_code,
        response_size=len(response.get_data())
    )
    return response
```

## 🔗 Integration Points

### Module Integration Interfaces
```python
# Standardized interfaces for module communication
from abc import ABC, abstractmethod

class ModuleInterface(ABC):
    """Base interface for all modules"""
    
    @abstractmethod
    async def health_check(self) -> Dict:
        """Check module health status"""
        pass
        
    @abstractmethod
    async def get_metrics(self) -> Dict:
        """Get module performance metrics"""
        pass

class ResumeProcessorInterface(ModuleInterface):
    """Interface for Module 1 - Resume Processor"""
    
    @abstractmethod
    async def process_resume(self, file_stream, user_id: str) -> Dict:
        """Process uploaded resume"""
        pass
        
    @abstractmethod
    async def retrieve_context(self, user_id: str, query: str) -> List[str]:
        """Get relevant resume context"""
        pass

class InterviewManagerInterface(ModuleInterface):
    """Interface for Module 2 - Interview Manager"""
    
    @abstractmethod  
    async def start_interview(self, user_id: str, resume_context: List[str]) -> Dict:
        """Start new interview session"""
        pass
        
    @abstractmethod
    async def process_response(self, session_id: str, response: str) -> Dict:
        """Process user response"""
        pass

class FeedbackGeneratorInterface(ModuleInterface):
    """Interface for Module 3 - Feedback Generator"""
    
    @abstractmethod
    async def generate_feedback(self, session_id: str) -> Dict:
        """Generate comprehensive feedback"""
        pass
```

### External Service Integration
```python
class ExternalServiceManager:
    """Manages integration with external services"""
    
    def __init__(self):
        self.services = {
            'stt': STTServiceClient(),
            'tts': TTSServiceClient()
        }
        self.health_checker = ServiceHealthChecker()
        
    async def call_stt_service(self, audio_file, session_id):
        """Call Speech-to-Text service"""
        try:
            response = await self.services['stt'].transcribe(
                audio_file=audio_file,
                session_id=session_id,
                timeout=30
            )
            return response
        except Exception as e:
            logger.error("STT service call failed", error=str(e))
            raise IntegrationError(f"STT service unavailable: {e}")
            
    async def call_tts_service(self, text, session_id):
        """Call Text-to-Speech service"""
        try:
            response = await self.services['tts'].synthesize(
                text=text,
                session_id=session_id,
                voice_settings={'speed': 'normal', 'pitch': 'medium'}
            )
            return response
        except Exception as e:
            logger.error("TTS service call failed", error=str(e))
            raise IntegrationError(f"TTS service unavailable: {e}")
```

## 🔄 Development Workflow

### Local Development Setup
```bash
# 1. Environment Setup
cd gemini-interview-engine/module4
python -m venv venv
source venv/bin/activate

# 2. Install Dependencies
pip install -r requirements-module4.txt

# 3. Start Redis (for rate limiting and caching)
docker run -d -p 6379:6379 redis:alpine

# 4. Environment Configuration
cp .env.example .env
# Configure all necessary environment variables

# 5. Initialize Database
python scripts/init_database.py

# 6. Start Development Server
export FLASK_ENV=development
export FLASK_DEBUG=true
python -m module4.app

# 7. Run Tests
pytest tests/module4/ -v --cov=module4

# 8. Start with hot-reload
flask --app module4.app run --reload --debug
```

### Production Deployment
```bash
# 1. Production Environment
export FLASK_ENV=production
export FLASK_DEBUG=false

# 2. Use Production WSGI Server
gunicorn -w 4 -b 0.0.0.0:5000 module4.app:create_app()

# 3. With Docker
docker build -t gemini-interview-api .
docker run -p 5000:5000 gemini-interview-api

# 4. With Load Balancing (nginx config)
upstream interview_api {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}
```

### Development Tasks
```python
# Priority 1: Core API Infrastructure
- [ ] Implement Flask application setup
- [ ] Create request validation system
- [ ] Build response formatting utilities
- [ ] Set up error handling framework

# Priority 2: Module Integration
- [ ] Implement ServiceOrchestrator class
- [ ] Create module communication interfaces
- [ ] Build transaction management system
- [ ] Add state synchronization logic

# Priority 3: Rate Limiting & Security
- [ ] Implement IntelligentRateLimiter
- [ ] Add file upload security validation
- [ ] Create CORS and authentication middleware
- [ ] Build request sanitization

# Priority 4: External Integration
- [ ] Implement STT/TTS service clients
- [ ] Create service health monitoring
- [ ] Build fallback mechanisms
- [ ] Add integration error handling

# Priority 5: Monitoring & Operations
- [ ] Implement metrics collection
- [ ] Add structured logging
- [ ] Create health check endpoints
- [ ] Build performance monitoring

# Priority 6: Testing & Documentation
- [ ] Write comprehensive unit tests
- [ ] Add integration tests
- [ ] Performance testing
- [ ] API documentation generation
```

---

## 📞 Support & Communication

### Getting Help
- **API Issues**: Create GitHub issue with `module-4` label
- **Integration Problems**: Coordinate with other module developers
- **Performance Issues**: Check monitoring dashboards first
- **Security Concerns**: Tag security team immediately

### Code Review Checklist
- [ ] All endpoints have proper validation
- [ ] Error handling comprehensive and consistent
- [ ] Rate limiting properly implemented
- [ ] Security measures in place
- [ ] Integration points well-defined
- [ ] Monitoring and logging comprehensive
- [ ] Performance optimized
- [ ] Documentation up-to-date

---

*This module serves as the gateway to the entire interview engine. Focus on reliability, security, and seamless integration to provide the best possible user experience.*