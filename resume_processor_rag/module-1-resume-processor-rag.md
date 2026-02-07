# Module 1: Resume Processor & RAG System

## 🎯 Module Overview

The **Resume Processor & RAG System** is the foundation of our AI Interview Engine. It transforms uploaded PDF resumes into searchable, contextual knowledge that powers intelligent interview questions. This module handles everything from parsing raw PDF files to storing vectorized content in Astra DB for lightning-fast retrieval.

## 🏗️ Architecture Diagram

```
PDF Upload
    │
    ▼
┌─────────────────┐
│  PDF Parser     │ ── Extracts raw text from PDF
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Text Chunker    │ ── Splits into logical sections
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Embedding Gen   │ ── Converts text to vectors
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Astra DB Store  │ ── Stores vectors & metadata
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Context Retriev │ ── RAG query processing
└─────────────────┘
```

## 🛠️ Core Components

### 1. PDF Resume Parser
**Purpose**: Extract clean, structured text from uploaded PDF resumes.

**Key Features**:
- Multi-page PDF support
- Text extraction with formatting preservation
- Error handling for corrupted/password-protected files
- Metadata extraction (creation date, author, etc.)

**Implementation Details**:
```python
class ResumeParser:
    def __init__(self):
        self.supported_formats = ['pdf']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
    def parse_pdf(self, file_stream):
        """Extract text from PDF file"""
        # Implementation using PyPDF2
```

### 2. Intelligent Text Chunker
**Purpose**: Break resume text into meaningful, searchable sections.

**Chunking Strategy**:
- **Section-based chunking**: Identifies resume sections (Experience, Education, Skills)
- **Content-aware splitting**: Maintains context within chunks
- **Optimal chunk size**: 200-500 tokens per chunk for embedding efficiency
- **Overlap handling**: Prevents context loss at chunk boundaries

**Section Detection Logic**:
```python
SECTION_KEYWORDS = {
    'EXPERIENCE': ['experience', 'work history', 'employment', 'professional'],
    'EDUCATION': ['education', 'academic', 'degree', 'university', 'school'],
    'SKILLS': ['skills', 'technologies', 'programming', 'tools'],
    'PROJECTS': ['projects', 'portfolio', 'accomplishments'],
    'SUMMARY': ['summary', 'objective', 'profile', 'about']
}
```

### 3. Embedding Generator
**Purpose**: Convert text chunks into high-dimensional vectors for similarity search.

**Model Selection**: 
- **Primary**: `all-MiniLM-L6-v2` (384 dimensions)
- **Advantages**: Fast inference, good semantic understanding, lightweight
- **Performance**: ~1000 tokens/second on CPU

**Vector Properties**:
- **Dimension**: 384 (optimal for Astra DB)
- **Normalization**: L2 normalized for cosine similarity
- **Batch processing**: Processes multiple chunks efficiently

### 4. Astra DB Integration
**Purpose**: Store and retrieve vectorized resume content with metadata.

**Database Schema**:
```python
# Collection: resume_embeddings
{
    "_id": "ObjectId",
    "user_id": "string",           # Session identifier
    "chunk_id": "integer",         # Chunk sequence number
    "section_type": "string",      # EXPERIENCE, EDUCATION, etc.
    "content": "string",           # Original text content
    "$vector": [float] * 384,      # Embedding vector
    "metadata": {
        "word_count": "integer",
        "char_count": "integer", 
        "extraction_confidence": "float",
        "section_position": "integer"
    },
    "created_at": "timestamp",
    "expires_at": "timestamp"      # TTL for cleanup
}
```

### 5. Context Retrieval System
**Purpose**: Find relevant resume sections based on interview context using RAG.

**Retrieval Methods**:
- **Semantic Search**: Vector similarity for contextual matching
- **Keyword Filtering**: Section-type filtering for targeted queries
- **Hybrid Search**: Combines vector + keyword search
- **Re-ranking**: Orders results by relevance score

## 🔧 Technical Implementation

### Dependencies & Setup
```bash
# Core dependencies
pip install PyPDF2==3.0.1
pip install sentence-transformers==2.2.2
pip install astrapy==1.0.0
pip install cassio==0.1.7
pip install numpy==1.24.0
pip install python-dotenv==1.0.0

# Development dependencies  
pip install pytest==7.4.0
pip install pytest-asyncio==0.21.0
pip install mock==5.1.0
```

### Environment Configuration
```env
# Astra DB Configuration
ASTRA_DB_ID=your_astra_database_id
ASTRA_DB_REGION=us-east1
ASTRA_DB_KEYSPACE=interview_system
ASTRA_DB_TOKEN=your_astra_db_application_token

# Module Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_CHUNK_SIZE=500
CHUNK_OVERLAP=50
VECTOR_DIMENSION=384
```

### Core Classes Structure

```python
class ResumeProcessorRAG:
    """Main orchestrator class for the module"""
    
    def __init__(self):
        self.parser = ResumeParser()
        self.chunker = TextChunker()
        self.embedder = EmbeddingGenerator()
        self.db_connector = AstraDBConnector()
        
    async def process_resume(self, file_stream, user_id):
        """Complete resume processing pipeline"""
        
    async def retrieve_context(self, user_id, query, top_k=3):
        """RAG-based context retrieval"""

class ResumeParser:
    """PDF parsing and text extraction"""
    
    def parse_pdf(self, file_stream) -> str:
        """Extract text from PDF"""
        
    def validate_file(self, file_stream) -> bool:
        """Validate file format and size"""

class TextChunker:
    """Intelligent text segmentation"""
    
    def chunk_by_sections(self, text: str) -> List[Dict]:
        """Section-aware chunking"""
        
    def detect_sections(self, text: str) -> Dict:
        """Identify resume sections"""

class EmbeddingGenerator:
    """Vector embedding generation"""
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Convert texts to embeddings"""

class AstraDBConnector:
    """Database operations and vector search"""
    
    def __init__(self):
        self.setup_connection()
        
    async def store_embeddings(self, user_id: str, chunks: List[Dict]):
        """Store resume chunks with embeddings"""
        
    async def vector_search(self, user_id: str, query_vector: np.ndarray, top_k: int):
        """Perform similarity search"""
```

## 🎯 Key Algorithms

### 1. Section Detection Algorithm
```python
def detect_sections(self, text: str) -> Dict[str, List[str]]:
    """
    Detects resume sections using keyword matching and position analysis
    
    Returns:
        Dict mapping section types to text content
    """
    lines = text.split('\n')
    sections = {'UNKNOWN': []}
    current_section = 'UNKNOWN'
    
    for line in lines:
        line_upper = line.strip().upper()
        
        # Check if line is a section header
        for section_type, keywords in SECTION_KEYWORDS.items():
            if any(keyword in line_upper for keyword in keywords):
                current_section = section_type
                if section_type not in sections:
                    sections[section_type] = []
                break
        
        # Add content to current section
        if line.strip():
            sections[current_section].append(line.strip())
    
    return sections
```

### 2. Chunking Algorithm
```python
def create_chunks(self, sections: Dict[str, List[str]]) -> List[Dict]:
    """
    Creates overlapping chunks while preserving section context
    """
    chunks = []
    chunk_id = 0
    
    for section_type, content_lines in sections.items():
        section_text = ' '.join(content_lines)
        
        # Split long sections into smaller chunks
        if len(section_text) > self.max_chunk_size:
            sub_chunks = self.split_with_overlap(section_text)
            
            for i, sub_chunk in enumerate(sub_chunks):
                chunks.append({
                    'chunk_id': chunk_id,
                    'section_type': section_type,
                    'content': sub_chunk,
                    'position': i,
                    'total_chunks': len(sub_chunks)
                })
                chunk_id += 1
        else:
            chunks.append({
                'chunk_id': chunk_id,
                'section_type': section_type,
                'content': section_text,
                'position': 0,
                'total_chunks': 1
            })
            chunk_id += 1
    
    return chunks
```

### 3. Vector Search Algorithm
```python
async def hybrid_search(self, user_id: str, query: str, section_filter: str = None):
    """
    Combines vector similarity with metadata filtering
    """
    # Generate query embedding
    query_vector = self.embedder.encode([query])[0]
    
    # Build search filter
    filter_conditions = {"user_id": user_id}
    if section_filter:
        filter_conditions["section_type"] = section_filter
    
    # Perform vector search with filtering
    results = await self.collection.vector_search(
        vector=query_vector.tolist(),
        limit=10,
        filter=filter_conditions
    )
    
    # Re-rank results by relevance
    ranked_results = self.rerank_results(results, query)
    
    return ranked_results[:3]  # Return top 3 results
```

## 📊 Data Flow

### Resume Processing Flow
```
1. File Upload Validation
   ├── Check file type (PDF only)
   ├── Verify file size (<10MB)
   └── Scan for password protection

2. PDF Text Extraction  
   ├── Use PyPDF2 for text extraction
   ├── Handle multi-page documents
   ├── Preserve basic formatting
   └── Extract metadata

3. Section Detection
   ├── Analyze text structure
   ├── Identify section headers
   ├── Group content by sections
   └── Handle edge cases

4. Intelligent Chunking
   ├── Respect section boundaries
   ├── Create overlapping chunks
   ├── Optimize chunk sizes
   └── Add metadata

5. Embedding Generation
   ├── Load SentenceTransformer model
   ├── Generate 384-dim vectors
   ├── Normalize embeddings
   └── Batch process for efficiency

6. Astra DB Storage
   ├── Create collection if needed
   ├── Insert documents with vectors
   ├── Set TTL for cleanup
   └── Index for fast retrieval
```

### Context Retrieval Flow
```
1. Query Processing
   ├── Receive user response/query
   ├── Extract key entities/topics
   └── Generate query embedding

2. Vector Search
   ├── Query Astra DB with vector
   ├── Apply metadata filters
   ├── Get similarity scores
   └── Return top candidates

3. Result Re-ranking
   ├── Calculate relevance scores
   ├── Consider section importance
   ├── Apply business rules
   └── Return final context
```

## 🧪 Testing Strategy

### Unit Tests
```python
class TestResumeParser:
    def test_pdf_parsing_valid_file(self):
        """Test successful PDF parsing"""
        
    def test_pdf_parsing_invalid_file(self):
        """Test handling of corrupted PDFs"""
        
    def test_file_size_validation(self):
        """Test file size limits"""

class TestTextChunker:
    def test_section_detection(self):
        """Test section identification accuracy"""
        
    def test_chunking_logic(self):
        """Test chunk creation and overlap"""
        
    def test_edge_cases(self):
        """Test unusual resume formats"""

class TestEmbeddingGenerator:
    def test_embedding_generation(self):
        """Test vector generation"""
        
    def test_batch_processing(self):
        """Test efficiency with multiple texts"""

class TestAstraDBConnector:
    def test_connection_setup(self):
        """Test database connection"""
        
    def test_document_insertion(self):
        """Test storing embeddings"""
        
    def test_vector_search(self):
        """Test similarity search"""
```

### Integration Tests
```python
class TestFullPipeline:
    def test_end_to_end_processing(self):
        """Test complete resume processing"""
        
    def test_retrieval_accuracy(self):
        """Test context retrieval quality"""
        
    def test_performance_benchmarks(self):
        """Test processing speed and memory usage"""
```

## 🚀 Performance Optimization

### Processing Speed
- **PDF Parsing**: ~2-5 seconds for typical resume
- **Text Chunking**: ~0.1 seconds for 1000 words  
- **Embedding Generation**: ~0.5 seconds for 10 chunks
- **Database Storage**: ~0.2 seconds for insertion
- **Total Processing Time**: ~3-6 seconds per resume

### Memory Optimization
```python
# Streaming processing for large files
def process_large_resume(self, file_stream):
    """Process resume in chunks to minimize memory usage"""
    
    # Process page by page instead of loading entire PDF
    for page_num in range(len(pdf_reader.pages)):
        page_text = pdf_reader.pages[page_num].extract_text()
        yield self.process_page(page_text)
```

### Caching Strategy
```python
# Cache embeddings model to avoid reloading
@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

# Cache frequent queries
@lru_cache(maxsize=100)
def get_cached_embeddings(text_hash):
    return self.generate_embeddings(text)
```

## 🔧 Configuration Options

### Module Settings
```python
MODULE_CONFIG = {
    # PDF Processing
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'supported_formats': ['.pdf'],
    
    # Text Chunking
    'max_chunk_size': 500,
    'chunk_overlap': 50,
    'min_chunk_size': 50,
    
    # Embedding Settings
    'embedding_model': 'all-MiniLM-L6-v2',
    'vector_dimension': 384,
    'batch_size': 32,
    
    # Database Settings
    'collection_name': 'resume_embeddings',
    'ttl_hours': 24,
    'max_results': 10,
    
    # Search Settings
    'default_top_k': 3,
    'similarity_threshold': 0.7,
    'rerank_enabled': True
}
```

## 🔍 Error Handling

### Common Error Scenarios
```python
class ResumeProcessingError(Exception):
    """Base exception for resume processing errors"""
    
class PDFParsingError(ResumeProcessingError):
    """PDF parsing failed"""
    
class EmbeddingError(ResumeProcessingError):
    """Embedding generation failed"""
    
class DatabaseError(ResumeProcessingError):
    """Astra DB operation failed"""

# Error handling strategy
try:
    result = await self.process_resume(file, user_id)
except PDFParsingError:
    # Fallback to alternative parser
    result = await self.fallback_parser(file, user_id)
except EmbeddingError:
    # Use cached embeddings or retry
    result = await self.retry_with_backoff(file, user_id)
except DatabaseError:
    # Queue for retry or use backup storage
    await self.queue_for_retry(file, user_id)
```

## 📈 Monitoring & Metrics

### Key Performance Indicators
```python
METRICS_TO_TRACK = {
    'processing_time': 'Average resume processing duration',
    'parsing_success_rate': 'Percentage of successfully parsed resumes',
    'embedding_quality': 'Semantic similarity scores',
    'database_latency': 'Astra DB query response times',
    'retrieval_accuracy': 'Relevance of retrieved context',
    'error_rates': 'Frequency of different error types'
}
```

### Logging Strategy
```python
import logging
import structlog

logger = structlog.get_logger(__name__)

# Structured logging for better monitoring
logger.info(
    "resume_processed",
    user_id=user_id,
    file_size=file_size,
    processing_time=duration,
    chunks_created=len(chunks),
    sections_detected=list(sections.keys())
)
```

## 🔗 Integration Points

### Input Interfaces
```python
# From Module 4 (API Layer)
async def process_resume_endpoint(file_stream, user_id):
    """Called when resume is uploaded"""
    
# From Module 2 (Interview Manager) 
async def get_context_for_response(user_id, user_response):
    """Called during interview for context"""
```

### Output Interfaces  
```python
# To Module 2 (Interview Manager)
def provide_resume_context(user_id) -> List[str]:
    """Provides resume sections for interview setup"""
    
def retrieve_relevant_context(user_id, query) -> List[str]:
    """Provides RAG-based context during interview"""
```

## 🔄 Development Workflow

### Setup Instructions
```bash
# 1. Clone repository
git clone <repo-url>
cd gemini-interview-engine

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements-module1.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your Astra DB credentials

# 5. Initialize Astra DB
python scripts/setup_astra_db.py

# 6. Run tests
pytest tests/module1/ -v

# 7. Start development
python -m module1.main
```

### Development Tasks
```python
# Priority 1: Core Implementation
- [ ] Implement PDF parser with PyPDF2
- [ ] Create section detection algorithm  
- [ ] Set up embedding generation
- [ ] Configure Astra DB connection
- [ ] Implement vector storage

# Priority 2: RAG System
- [ ] Build context retrieval system
- [ ] Implement hybrid search
- [ ] Add result re-ranking
- [ ] Optimize query performance

# Priority 3: Quality & Testing  
- [ ] Add comprehensive error handling
- [ ] Write unit tests (>80% coverage)
- [ ] Performance benchmarking
- [ ] Integration test with sample resumes

# Priority 4: Optimization
- [ ] Implement caching strategies
- [ ] Add monitoring and logging
- [ ] Memory optimization
- [ ] Security hardening
```

---

## 📞 Support & Communication

### Getting Help
- **Technical Issues**: Create GitHub issue with `module-1` label
- **Architecture Questions**: Tag `@team-lead` in discussions  
- **Database Issues**: Check Astra DB documentation first
- **Integration**: Coordinate with Module 2 & 4 developers

### Code Review Checklist
- [ ] Functions have type hints and docstrings
- [ ] Error handling for all external calls
- [ ] Unit tests for new functionality
- [ ] Performance considerations documented
- [ ] Security review for file handling
- [ ] Integration points clearly defined

---

*This module serves as the foundation for intelligent resume-based interviewing. Focus on accuracy, performance, and robust error handling to ensure high-quality context for the interview engine.*