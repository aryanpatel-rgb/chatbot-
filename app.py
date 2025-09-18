from flask import Flask, render_template, jsonify, request, session
from src.helper import download_hugging_face_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from src.prompt import *
import os
import uuid
from datetime import datetime


app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# Dictionary to store conversation history for each session
conversation_history = {}
MAX_SESSIONS = 100  # Limit number of concurrent sessions

load_dotenv()

PINECONE_API_KEY=os.environ.get('PINECONE_API_KEY')
OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY')

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


embeddings = download_hugging_face_embeddings()

index_name = "medical-chatbot" 
# Embed each chunk and upsert the embeddings into your Pinecone index.
docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)




retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k":3})

chatModel = ChatOpenAI(model="gpt-4o")
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(chatModel, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)



@app.route("/")
def index():
    # Initialize session if not exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        conversation_history[session['session_id']] = []
    return render_template('chat.html')



@app.route("/get", methods=["GET", "POST"])
def chat():
    try:
        msg = request.form.get("msg", "").strip()
        if not msg:
            return jsonify({"error": "Empty message"}), 400
            
        # Validate message length
        if len(msg) > 1000:
            return "Message too long. Please keep it under 1000 characters.", 400
            
        print(f"User input: {msg}")
        
        # Get or create session
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            conversation_history[session['session_id']] = []
            
            # Clean up old sessions if we exceed the limit
            if len(conversation_history) > MAX_SESSIONS:
                # Remove oldest sessions (keep most recent MAX_SESSIONS)
                oldest_sessions = list(conversation_history.keys())[:-MAX_SESSIONS]
                for old_session in oldest_sessions:
                    del conversation_history[old_session]
        
        session_id = session['session_id']
        
        # Get conversation history for this session
        history = conversation_history.get(session_id, [])
        
        # Format conversation history as a string
        history_text = ""
        if history:
            for i, (user_msg, bot_response) in enumerate(history[-5:]):  # Keep last 5 exchanges
                history_text += f"User: {user_msg}\nAssistant: {bot_response}\n\n"
        else:
            history_text = "No previous conversation."
        
        # Invoke the chain with conversation history
        response = rag_chain.invoke({
            "input": msg,
            "conversation_history": history_text
        })
        
        answer = response["answer"]
        print("Response : ", answer)
        
        # Store this exchange in conversation history
        conversation_history[session_id].append((msg, answer))
        
        # Keep only last 10 exchanges per session to prevent memory issues
        if len(conversation_history[session_id]) > 10:
            conversation_history[session_id] = conversation_history[session_id][-10:]
        
        return str(answer)
        
    except Exception as e:
        print(f"Error in chat route: {str(e)}")
        return "I'm sorry, I encountered an error processing your request. Please try again.", 500


@app.route("/clear", methods=["POST"])
def clear_history():
    """Clear conversation history for the current session"""
    try:
        if 'session_id' in session:
            session_id = session['session_id']
            conversation_history[session_id] = []
            return jsonify({"status": "success", "message": "Conversation history cleared"})
        return jsonify({"status": "error", "message": "No active session"})
    except Exception as e:
        print(f"Error clearing history: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to clear history"}), 500


@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(conversation_history)
    })


@app.route("/stats")
def stats():
    """Statistics endpoint"""
    total_conversations = sum(len(history) for history in conversation_history.values())
    return jsonify({
        "active_sessions": len(conversation_history),
        "total_conversations": total_conversations,
        "uptime": datetime.now().isoformat()
    })


if __name__ == '__main__':
    app.run(host="0.0.0.0", port= 8080, debug= True)
