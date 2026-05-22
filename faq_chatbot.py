"""
BuildRight Renovations — FAQ Chatbot
Conversational AI assistant for renovation inquiries using LangChain, ChromaDB, and Claude.
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


class BuildRightChatbot:
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
        print("Initializing BuildRight Chatbot...")

        # Load environment variables
        load_dotenv()

        # Set API key
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Please set it in .env file or pass it as parameter.")

        # Load FAQ data
        self.faq_data = self._load_faq_data(data_path)
        print(f"Loaded {len(self.faq_data)} FAQ entries")

        # Initialize embeddings model
        print("Loading embedding model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

        # Create vector store
        print("Creating vector store...")
        self.vectorstore = self._create_vectorstore()

        # Initialize LLM
        print("Initializing Claude LLM...")
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=self.api_key,
            temperature=0.3,
            max_tokens=1024
        )

        # Create retrieval chain
        self.qa_chain = self._create_qa_chain()

        print("Chatbot initialization complete!")
    
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
        template = """You are a friendly and professional customer service assistant for BuildRight Renovations, a residential renovation company in the Greater Toronto Area.

Use the following FAQ context to answer the customer's question accurately.
If the answer is not in the context, politely say you don't have that specific detail and suggest they book a free consultation.

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
    
    def estimate_quote(self, project_type: str, sqft: float, tier: str) -> dict:
        """
        Calculate a rough renovation estimate.
        project_type: kitchen | bathroom | basement | full_renovation
        tier: basic | standard | premium
        """
        base_rates = {
            "kitchen": 150,
            "bathroom": 200,
            "basement": 80,
            "full_renovation": 120,
        }
        multipliers = {"basic": 1.0, "standard": 1.4, "premium": 2.0}

        rate = base_rates.get(project_type.lower().replace(" ", "_"))
        mult = multipliers.get(tier.lower(), 1.0)
        if rate is None:
            return {"error": f"Unknown project type: {project_type}"}

        mid = rate * sqft * mult
        low = round(mid * 0.85, -2)   # round to nearest 100
        high = round(mid * 1.15, -2)
        return {
            "project_type": project_type,
            "sqft": sqft,
            "tier": tier,
            "low": int(low),
            "high": int(high),
            "currency": "CAD",
        }

    def chat_with_history(self, user_message: str, conversation_history: list) -> dict:
        """
        对话式问答，支持多轮历史记忆

        conversation_history 格式:
        [
            {"role": "assistant", "content": "你好！请问..."},
            {"role": "user", "content": "我的订单没收到"},
            ...
        ]
        """
        # 1. 用 RAG 检索相关 FAQ（用最新一条用户消息检索）
        docs = self.vectorstore.similarity_search(user_message, k=3)
        context = "\n".join([doc.page_content for doc in docs])

        # 2. 把对话历史格式化成字符串
        history_text = ""
        for msg in conversation_history[-6:]:  # 只保留最近6条，控制 token
            role = "客户" if msg["role"] == "user" else "客服"
            history_text += f"{role}: {msg['content']}\n"

        # 3. 构建 prompt
        prompt = f"""You are a friendly and professional customer service assistant for BuildRight Renovations, a residential renovation company in the Greater Toronto Area. You help potential clients get information and book consultations.

Your approach:
1. Guide the conversation with one question at a time
2. When someone asks about cost or pricing, ask for: project type, approximate size (sq ft), and preferred material tier (Basic / Standard / Premium)
3. Once you have enough info, give a clear answer or estimated price range
4. When the conversation is wrapping up, ask for the client's name and email so the team can follow up

Use this FAQ knowledge to answer questions:
{context}

Conversation so far:
{history_text}
Client: {user_message}

Reply naturally and helpfully. Ask only one question at a time. Respond in the same language the client uses."""

        # 4. 调用 Claude
        from langchain.schema import HumanMessage
        response = self.llm.invoke([HumanMessage(content=prompt)])

        return {
            "answer": response.content,
            "source_questions": [doc.metadata.get("question", "") for doc in docs]
        }

    def summarize_conversation(self, raw_transcript: str) -> str:
        """
        Use Claude to turn a raw chat transcript into a clean owner-facing summary.
        Returns a short paragraph describing what the client wants.
        """
        from langchain.schema import HumanMessage
        prompt = f"""You are reading a conversation between a potential renovation client and the BuildRight virtual assistant.

Extract and summarize the key details the owner needs to follow up:
- What type of project the client wants (kitchen, bathroom, basement, etc.)
- Approximate size or scope if mentioned
- Budget range or tier preference if mentioned
- Timeline or urgency if mentioned
- Any other specific details or concerns raised
- Client's tone / how ready they seem to move forward

Be concise — 3 to 6 bullet points. If a detail wasn't mentioned, omit it.

Transcript:
{raw_transcript}

Summary (bullet points):"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            return f"(Summary unavailable: {e})\n\nRaw transcript:\n{raw_transcript}"

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