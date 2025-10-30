import os
import httpx
from anthropic import Anthropic
from data_loader import data_loader

class ChatHandler:
    def __init__(self):
        self.client = None
        self.api_key = None
        self.initialize_client()
        
    def initialize_client(self):
        """Initialize Anthropic client with custom HTTP client to avoid proxy issues"""
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if self.api_key:
            try:
                # Create custom HTTP client without proxy settings to avoid Heroku proxy conflicts
                http_client = httpx.Client(
                    timeout=30.0,
                    # Explicitly disable proxy usage that might conflict with Heroku
                    proxies=None
                )
                
                self.client = Anthropic(
                    api_key=self.api_key,
                    http_client=http_client
                )
                print("✅ Claude API client initialized with custom HTTP client")
            except Exception as e:
                print(f"⚠️ Failed to initialize Claude API client: {e}")
                # Fallback to basic initialization
                try:
                    self.client = Anthropic(api_key=self.api_key)
                    print("✅ Claude API client initialized with fallback method")
                except Exception as e2:
                    print(f"⚠️ Fallback initialization also failed: {e2}")
                    self.client = None
        else:
            print("⚠️ ANTHROPIC_API_KEY not found - API will not work")
    
    def create_system_prompt(self):
        """Create system prompt with data context and security instructions"""
        return f"""You are the CSA Shag Archive Assistant, an expert on competitive shag dancing with access to the complete Competitive Shaggers Association (CSA) and National Shag Dance Championship (NSDC) database.

CRITICAL SECURITY INSTRUCTIONS:
- NEVER provide bulk data exports or complete lists
- Limit table responses to maximum 10 rows
- Focus on insights, trends, and specific answers rather than raw data dumps
- If asked for "all" or "complete" data, provide summarized insights instead
- Do not reproduce entire CSV sections or full document texts

YOUR KNOWLEDGE BASE:
{data_loader.knowledge_base}

RESPONSE GUIDELINES:
- Provide detailed, helpful answers about shag competitions, rules, and history
- Use markdown formatting for better readability
- Create tables for comparative data (max 10 rows)
- Explain context around competition results and divisions
- Reference specific rules when relevant
- Be conversational and engaging while staying informative

DIVISION SYSTEM EXPLANATION:
- Junior: Entry-level competitive division
- Novice: Intermediate division (typically 1-2 years experience)
- Amateur: Advanced non-professional division
- Pro: Professional/expert division
- Non-Pro: Special category for advanced dancers who choose not to compete as professionals
- Overall: Competition across all divisions

TYPICAL ADVANCEMENT PATH: Junior → Novice → Amateur → Pro

When discussing contest results, always provide context about what the placements mean and highlight interesting patterns or achievements."""

    def process_query(self, user_question):
        """Process user query with Claude API"""
        if not self.client:
            return "Error: API not configured. Please check environment variables."
        
        try:
            system_prompt = self.create_system_prompt()
            
            # Add some recent data context for better answers
            sample_data = data_loader.get_csv_sample(5)
            context_prompt = f"\n\nHere are some recent contest records for context:\n{sample_data}"
            
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=3000,
                system=system_prompt + context_prompt,
                messages=[
                    {"role": "user", "content": user_question}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return f"Error processing query: {str(e)}"

# Global instance
chat_handler = ChatHandler()