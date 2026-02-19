"""
E-commerce FAQ Chatbot
A conversational AI assistant that answers frequently asked questions about e-commerce operations
using LangChain, ChromaDB vector store, and Anthropic Claude LLM.
"""

import os
import json
import pandas as pd
from typing import List, Dict
from dotenv import load_dotenv

# LangChain imports
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA


class EcommerceFAQChatbot:
    """
    FAQ Chatbot for E-commerce platform using RAG (Retrieval-Augmented Generation)
    """
    
    def __init__(self, data_path: str, api_key: str = None):
        """
        Initialize the chatbot with FAQ data and API credentials
        
        Args:
            data_path: Path to the JSON file containing FAQ data
            api_key: Anthropic API key (optional, can be loaded from .env)
        """
        print("🚀 Initializing E-commerce FAQ Chatbot...")
        
        # Load environment variables
        load_dotenv()
        
        # Set API key
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Please set it in .env file or pass it as parameter.")
        
        # Load FAQ data
        self.faq_data = self._load_faq_data(data_path)
        print(f"✅ Loaded {len(self.faq_data)} FAQ entries")
        
        # Initialize embeddings model
        print("📦 Loading embedding model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Create vector store
        print("🗄️ Creating vector store...")
        self.vectorstore = self._create_vectorstore()
        
        # Initialize LLM
        print("🤖 Initializing Claude LLM...")
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=self.api_key,
            temperature=0.3,
            max_tokens=1024
        )
        
        # Create retrieval chain
        self.qa_chain = self._create_qa_chain()
        
        print("✅ Chatbot initialization complete!\n")
    
    def _load_faq_data(self, data_path: str) -> List[Dict]:
        """Load FAQ data from JSON file"""
        with open(data_path, 'r') as f:
            data = json.load(f)
        return data['questions']
    
    def _create_vectorstore(self) -> Chroma:
        """Create ChromaDB vector store from FAQ data"""
        # Convert FAQ data to LangChain Documents
        documents = []
        for idx, item in enumerate(self.faq_data):
            # Combine question and answer for better context
            content = f"Question: {item['question']}\nAnswer: {item['answer']}"
            metadata = {
                'question': item['question'],
                'answer': item['answer'],
                'id': idx
            }
            documents.append(Document(page_content=content, metadata=metadata))
        
        # Create vector store
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name="ecommerce_faq"
        )
        
        return vectorstore
    
    def _create_qa_chain(self) -> RetrievalQA:
        """Create the Question-Answering chain with custom prompt"""
        
        # Custom prompt template
        template = """You are a helpful e-commerce customer support assistant. 
Your role is to answer customer questions based on the FAQ information provided.

Use the following FAQ context to answer the customer's question. 
If the answer is not in the context, politely say that you don't have that specific information 
and suggest they contact customer support for personalized assistance.

Context:
{context}

Customer Question: {question}

Helpful Answer:"""
        
        # Create prompt
        prompt = ChatPromptTemplate.from_template(template)
        
        # Create retrieval chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 3}  # Retrieve top 3 most relevant FAQs
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        
        return qa_chain
    
    def ask(self, question: str) -> Dict:
        """
        Ask a question to the chatbot
        
        Args:
            question: User's question
            
        Returns:
            Dictionary containing answer and source documents
        """
        result = self.qa_chain.invoke({"query": question})
        return {
            'answer': result['result'],
            'source_questions': [doc.metadata['question'] for doc in result['source_documents']]
        }
    
    def get_similar_questions(self, question: str, k: int = 5) -> List[str]:
        """
        Find similar questions in the FAQ database
        
        Args:
            question: User's question
            k: Number of similar questions to return
            
        Returns:
            List of similar questions
        """
        docs = self.vectorstore.similarity_search(question, k=k)
        return [doc.metadata['question'] for doc in docs]
    
    def export_faq_to_dataframe(self) -> pd.DataFrame:
        """Export FAQ data to pandas DataFrame for analysis"""
        return pd.DataFrame(self.faq_data)
    
    def chat(self):
        """Start interactive chat session"""
        print("="*70)
        print("🛍️  E-COMMERCE FAQ CHATBOT - Interactive Mode")
        print("="*70)
        print("Ask me anything about our e-commerce policies, shipping, returns, etc.")
        print("Type 'quit', 'exit', or 'bye' to end the conversation.")
        print("Type 'similar' followed by your question to see related FAQs.")
        print("="*70 + "\n")
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("\n👋 Thank you for using our FAQ Chatbot! Have a great day!")
                    break
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Handle 'similar' command
                if user_input.lower().startswith('similar'):
                    query = user_input[7:].strip()
                    if query:
                        similar = self.get_similar_questions(query, k=5)
                        print("\n🔍 Similar questions in our FAQ:")
                        for i, q in enumerate(similar, 1):
                            print(f"   {i}. {q}")
                        print()
                    else:
                        print("Please provide a question after 'similar'.\n")
                    continue
                
                # Get answer from chatbot
                print("\nBot: ", end="", flush=True)
                result = self.ask(user_input)
                print(result['answer'])
                
                # Show source questions (optional)
                if result['source_questions']:
                    print("\n📚 Related FAQ topics:")
                    for q in result['source_questions'][:2]:  # Show top 2
                        print(f"   • {q}")
                
                print()  # Empty line for readability
                
            except KeyboardInterrupt:
                print("\n\n👋 Chatbot interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")


def main():
    """Main function to run the chatbot"""
    
    # Path to FAQ data - using relative path for cross-platform compatibility
    data_path = "Ecommerce_FAQ_Chatbot_dataset.json"
    
    # Alternative: if file is in different location, specify full path
    # data_path = "/path/to/Ecommerce_FAQ_Chatbot_dataset.json"
    
    try:
        # Initialize chatbot
        chatbot = EcommerceFAQChatbot(data_path)
        
        # Demonstration mode: Show sample queries
        print("\n" + "="*70)
        print("📊 DEMONSTRATION MODE - Sample Queries")
        print("="*70 + "\n")
        
        sample_questions = [
            "How can I track my order?",
            "What is your return policy?",
            "Do you offer international shipping?",
            "How do I contact customer support?",
            "Can I cancel my order?"
        ]
        
        for question in sample_questions:
            print(f"Q: {question}")
            result = chatbot.ask(question)
            print(f"A: {result['answer']}\n")
            print("-" * 70 + "\n")
        
        # Export FAQ data to CSV for analysis
        df = chatbot.export_faq_to_dataframe()
        df.to_csv('faq_data_export.csv', index=False)
        print("✅ FAQ data exported to 'faq_data_export.csv'\n")
        
        # Start interactive chat
        chatbot.chat()
        
    except FileNotFoundError:
        print(f"❌ Error: FAQ data file not found at '{data_path}'")
        print("Please ensure the Ecommerce_FAQ_Chatbot_dataset.json file is in the correct location.")
    except Exception as e:
        print(f"❌ Error initializing chatbot: {str(e)}")
        print("\nPlease ensure:")
        print("1. All dependencies are installed (run: pip install -r requirements.txt)")
        print("2. ANTHROPIC_API_KEY is set in .env file")
        print("3. FAQ data file exists at the specified path")


if __name__ == "__main__":
    main()