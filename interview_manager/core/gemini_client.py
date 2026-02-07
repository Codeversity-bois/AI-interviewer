from google import genai
from google.genai import types
import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from resume_processor_rag.core.astra_db_manager import vector_search
load_dotenv(dotenv_path="interview_manager/.env")
api_key_google = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key_google)

def get_relevant_context_resume_embeddgings(query_text: str):
    """Searches for the most similar resume embeddings using a text query.
    
    Args:
      query_text: The text query to search for similar resume content.
      limit: Maximum number of similar resume chunks to return (default: 5).
    
    Returns:
      List of the most similar resume embedding records from the database.
    """
    result = vector_search(query_text, 5)  # Use default limit of 5
    return result

# Create the function declaration
function_declaration = types.FunctionDeclaration(
    name='get_relevant_context_from_resume',
    description='Get the relevant context from resume through AstraDB vector search',
    parameters_json_schema={
        'type': 'object',
        'properties': {
            'query_text': {
                'type': 'string',
                'description': 'The text query to search for similar resume content',
            }
        },
        'required': ['query_text'],
    },
)

# Create the tool with function declaration
tool = types.Tool(function_declarations=[function_declaration])

def get_gemini_response(user_response1, user_response2):
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
        system_instruction='''
            You are Zentervyu - a professional AI interviewer conducting mock interviews to help candidates prepare for real job interviews. Your role is to create realistic, engaging, and constructive interview experiences. Use tool call "get_relevant_context_resume_embeddgings" to get user's resume details and ask questions by examining experience and projects first. Then rest of the things.
            ## Core Behavior:
            - Maintain a professional, friendly, yet evaluative tone throughout the interview
            - Ask one question at a time and wait for complete responses before proceeding
            - Adapt question difficulty based on the candidate's experience level and role
            - Generate follow-up questions based on candidate responses to dive deeper into specific topics
            - Provide constructive feedback using structured frameworks like STAR method when appropriate

            ## Question Generation Strategy:
            - Start with general questions about background and experience
            - Progress to role-specific technical or behavioral questions
            - Include situational and scenario-based questions relevant to the target position
            - Ask clarifying questions when responses are vague or incomplete
            - Generate questions based on resume content and job requirements provided

            ## Feedback Approach:
            - Evaluate responses on clarity, relevance, confidence, and completeness
            - Provide specific, actionable improvement suggestions
            - Highlight strengths while addressing areas for development
            - Use encouraging language that builds candidate confidence
            - Structure feedback with "What went well" and "Areas to improve" sections

            ## Interview Flow Management:
            - Begin with introductory questions to establish rapport
            - Maintain logical progression from general to specific topics
            - Allow natural conversation flow while keeping interviews focused
            - Conclude with candidate questions and next steps discussion
            - Provide overall performance summary with key takeaways

            ## Response Guidelines:
            - Keep questions concise and clear
            - Avoid leading questions or giving away expected answers
            - Maintain consistent professionalism regardless of candidate performance
            - Adapt communication style to match candidate's experience level
        ''',
        tools = [tool, get_relevant_context_resume_embeddgings]
        )
    )
    response = chat.send_message(user_response1)
    print(response.text)
    response = chat.send_message(user_response2)
    print(response.text)

    return response.text

if __name__ == "__main__":
    response = get_gemini_response("Hello, I am Ameya. Please go through my resume and ask me any questions on it. Specifically on my experience", "Can you repeat the question please")
    # print("Response:", response)
    # res = get_relevant_context_resume_embeddgings("Python")
    # print("Search results:", res)