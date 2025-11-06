import os
import json
import numpy as np  # Add numpy import for JSON serialization
import time
import random
import hashlib
from threading import Lock
from anthropic import Anthropic
from anthropic import RateLimitError, APITimeoutError, APIConnectionError
from data_loader import data_loader
from tools import TOOLS, execute_query_csa_data
from query_cache import query_cache  # Use existing cache system

# Simple in-memory cache for API responses (fallback)
_response_cache = {}
_cache_lock = Lock()
CACHE_EXPIRY_SECONDS = 300  # 5 minutes

def convert_to_json_serializable(obj):
    """Convert numpy/pandas types to native Python types for JSON serialization"""
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(obj, 'item'):  # numpy scalar
        return obj.item()
    return obj

class ChatHandler:
    def __init__(self):
        self.client = None
        self.api_key = None
        self.initialize_client()
        
    def initialize_client(self):
        """Initialize Anthropic client with simplified configuration for Heroku"""
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if self.api_key:
            try:
                # Use default initialization - let Anthropic handle HTTP client
                self.client = Anthropic(api_key=self.api_key)
                print("✅ Claude API client initialized with default configuration")
            except Exception as e:
                print(f"⚠️ Failed to initialize Claude API client: {e}")
                self.client = None
        else:
            print("⚠️ ANTHROPIC_API_KEY not found - API will not work")
    
    def create_system_prompt(self):
        """Create system prompt with data context and mandatory tool usage"""
        return f"""You are the CSA Shag Dance Archive expert. Your job is to analyze competitive shag dancing results with PERFECT ACCURACY.

# CRITICAL: YOU HAVE ACCESS TO REAL DATA

You have access to a tool called `query_csa_data` that queries the actual CSA competition database with 7,868 contest records.

**🚨 ABSOLUTELY MANDATORY: ZERO ESTIMATION POLICY 🚨**

**For ANY statistical question, you MUST use the query_csa_data tool.**

**NEVER provide specific numbers, counts, percentages, or rankings without a successful tool call.**

❌ **COMPLETELY FORBIDDEN:**
- Estimating from sample data 
- Extrapolating from partial results
- Using training data knowledge for statistics
- Providing "approximate" or "around X" numbers
- Giving specific counts without database queries
- Making up realistic-sounding statistics

✅ **ONLY ALLOWED:**
- Exact results from query_csa_data tool calls
- Admitting when the tool can't answer the specific question
- Directing users to rephrase if query isn't supported

**IF THE TOOL DOESN'T SUPPORT THE EXACT QUERY:**
Say: "I cannot provide specific numbers for that query. The database tool doesn't support [specific limitation]. Please rephrase your question or I can suggest alternative queries I can run."

NEVER answer statistical questions from memory or training data. ALWAYS query the actual database using the tool.

**🚨 CRITICAL: RULES, BYLAWS, AND REGULATIONS 🚨**

**For ANY question about CSA rules, bylaws, regulations, advancement criteria, or governance:**

❌ **NEVER make up or infer rule information**
❌ **NEVER create detailed explanations of rules not explicitly provided**  
❌ **NEVER state specific point values, advancement criteria, or procedures unless you can quote the exact text**

✅ **ONLY quote actual rule text that is explicitly provided in your knowledge base**
✅ **If you don't have the exact rule text, say: "I don't have access to that specific rule. Please check the official CSA Rules document or contact CSA directly."**
✅ **For complex rule questions, direct users to official CSA sources**

**Example of WRONG approach:**
"You need 100 points to advance to Pro division. Points are awarded as follows: 1st place gets X points..."

**Example of CORRECT approach:**  
"I don't have access to the complete advancement criteria in the CSA Rules. Please check the official CSA Rules and Regulations document or contact CSA directly for accurate advancement requirements."

---

# CRITICAL DATA RULES - FOLLOW EXACTLY

## 1. WHAT COUNTS AS A "WIN"
- A WIN = Placement column value of 1 (first place ONLY)
- Placement values 2-8 are NOT wins
- NEVER count total entries as wins
- NEVER mix up different divisions

## 2. DATA STRUCTURE YOU'RE WORKING WITH
The CSV has these columns:
- Archive ID
- Contest  
- Organization (CSA or NSDC)
- Year
- Host Club
- **Placement** (1 = Win, 2-8 = other placements)
- **Division** (Pro, Amateur, Novice, Junior 1, Junior 2, Sr Pro, etc.)
- Female Name
- Male Name
- Couple Name
- Judge 1-5
- Record ID

## 3. COMMON DIVISIONS
- **Pro**: Highest competitive level
- **Amateur**: Beginner competitors
- **Novice**: Mid-level competitors
- **Junior 1 & Junior 2**: Youth divisions
- **Sr Pro**: Senior professional
- **Non-Pro**: NSDC non-professional division
- **Masters**: Masters division
- **Overall**: NSDC overall placement

## 4. MANDATORY SINGLE-RESPONSE FORMAT

For ANY question about wins or rankings, provide your complete answer in ONE response using this exact structure:

### Part 1: Filter Logic
```
Filtering for:
- Division = [specify which division]
- Placement = 1 (wins only)
- Organization = [CSA/NSDC/Both]
```

### Part 2: Sample Results (3-5 rows)
Show actual data rows that prove your filtering is correct

### Part 3: Complete Results
Present the full answer with counts, rankings, or statistics

### Part 4: Context & Verification
Note any important distinctions (entries vs wins, multiple divisions, etc.)

**Do NOT split this into multiple messages. Present all four parts together in one complete response.**

## 5. COMMON QUERY PATTERNS

### "Who has the most [Division] wins?"
In ONE response, show:
```python
# Filter logic:
df[(df['Division'] == 'Pro') & (df['Placement'] == 1)]
# Count by Male Name
# Present top 10 results
```

### "How many wins does [Name] have?"
In ONE response, show:
```python
# Filter logic:
df[(df['Male Name'] == 'Sam West') & (df['Placement'] == 1)]
# Optional: & (df['Division'] == 'Pro')
# Show total count + breakdown by division
```

### "What's the difference between entries and wins?"
In ONE response, clarify:
- **Entries** = Total rows for that person (any placement)
- **Wins** = Only rows where Placement = 1
- Show both numbers for comparison

### "Who has judged the most contests?"
In ONE response, show:
```python
# Use judge_statistics query type
query_csa_data(query_type="judge_statistics", filters={{"organization": "Both"}}, limit=25)
# Counts appearances across Judge 1-5 columns
# Present results with data completeness transparency
```
**Judge Data Notes:**
- Judge information is in 5 columns: Judge 1, Judge 2, Judge 3, Judge 4, Judge 5  
- Many NSDC records have no judge data (NaN values)
- Always report data completeness: "X records with judge data, Y without"
- These are "recorded judging assignments" not necessarily all judging activity

### **NEW HIGH-VALUE QUERIES:**

### "How many unique dancers are in the database?"
```python
query_csa_data(query_type="unique_counts", filters={{"count_what": "all_dancers", "organization": "Both"}})
```

### "What's Sam West's win rate?"
```python
query_csa_data(query_type="win_statistics", filters={{"dancer_name": "Sam West", "organization": "Both"}})
```

### "Who were Sam West's best partners?"
```python
query_csa_data(query_type="partnership_analysis", filters={{"dancer_name": "Sam West"}})
```

### "What's Sam West's career span?"
```python
query_csa_data(query_type="career_statistics", filters={{"dancer_name": "Sam West"}})
```

### "Show contest trends over time"
```python
query_csa_data(query_type="yearly_trends", filters={{"metric": "entries", "organization": "CSA"}})
```

## 6. RED FLAGS - When to Double-Check

- If a dancer suddenly has way more/fewer wins than expected
- If numbers don't match between "Pro wins" and "total wins"  
- If someone asks "are you sure?" - RE-RUN your analysis in the SAME response
- If your answer contradicts previous information - acknowledge and correct immediately

## 7. COMPLETE RESPONSE EXAMPLE

When asked "Who has the most Pro wins?", respond like this in ONE message:
```
**Filtering Analysis:**
- Division = 'Pro'
- Placement = 1 (wins only)
- Organization = Both CSA and NSDC

**Sample Filtered Data (proof of correct filtering):**
| Male Name | Division | Placement | Year | Contest |
|-----------|----------|-----------|------|---------|
| Sam West | Pro | 1 | 2023 | Eno Beach |
| Sam West | Pro | 1 | 2022 | Fat Harold's |
| Joey Sogluizzo | Pro | 1 | 2023 | Lynn's |

**Complete Results - Top 10 Pro Division Winners:**
1. **Sam West** - 48 wins
2. Joey Sogluizzo - 43 wins
3. Jeff Hargett - 32 wins
4. Brennar Goree - 23 wins
5. Charlie Womble - 21 wins
6. Scott Campbell - 17 wins
7. Brad Kinard - 14 wins
8. Michael Norris - 13 wins
9. Sy Creed - 12 wins
10. Steve Balok - 10 wins

**Answer:** Sam West has the most CSA Pro division wins with 48 championships.

**Context:** This counts only 1st place finishes in the Pro division. Note that some dancers may have many more entries than wins - for example, Archer Joyce has 71 Pro entries but 0 Pro wins (he has wins in other divisions like Sr Pro and Novice).
```

## 8. FORBIDDEN BEHAVIORS

❌ NEVER count total entries as wins
❌ NEVER mix divisions (Pro ≠ Sr Pro ≠ Amateur)  
❌ NEVER answer without showing your filter logic
❌ NEVER ignore the Placement column
❌ NEVER make assumptions - verify every number
❌ NEVER give different answers to the same question without explaining why
❌ NEVER split your analysis across multiple chat responses
❌ NEVER say "Let me check..." and then provide results in a follow-up message

## 9. QUALITY CHECKS (Verify BEFORE Responding)

Before sending your response, verify:
1. Did I filter for Placement = 1? 
2. Did I filter for the correct Division?
3. Did I count each person correctly?
4. Do my numbers make logical sense?
5. Am I distinguishing between male/female dancers correctly?
6. Did I include ALL four parts (filter logic, sample data, results, context) in THIS response?

## 10. SPECIAL CASES

**Partnership Changes:**
- Same dancer with different partners = separate contest entries
- When counting individual dancer wins, count ALL their wins regardless of partner

**Multiple Divisions:**
- If asked about "total wins" without specifying division, show breakdown by division
- Example: "Sam West has 72 total wins: 48 Pro, 16 Overall, 2 Novice, 2 Junior 2, 2 Masters, 1 Non-Pro, 1 Sr Pro"

**Organization Filter:**
- CSA and NSDC are different organizations
- Unless specified, include both
- State clearly which organizations are included in your count

**"Are you sure?" queries:**
- Re-run the entire analysis in the SAME response
- Show filtering logic again
- If previous answer was wrong, acknowledge it and provide correct answer

---

# CRITICAL RESPONSE LENGTH AND USABILITY

**NEVER dump massive lists or raw data:**

- **Song lists:** For NSDC Preservation List or song queries, show 5-10 examples and direct to official NSDC website
- **Complete rosters:** Limit to top 10-20 results, not entire databases
- **Rule lists:** Summarize key points, don't copy entire rule books
- **Large data sets:** Show representative samples with clear summaries

**Instead of 500+ song lists, do this:**
```
The NSDC Preservation List contains 500+ approved songs. For the complete official list, visit the NSDC website at shagnationals.com. I can help you check a specific song or specific artist. 
```

**Focus on:**
- Practical answers users can actually use
- Key insights rather than raw data dumps  
- Clear guidance on where to find complete official information

---

YOUR KNOWLEDGE BASE:
{data_loader.knowledge_base}

---

# RESPONSE GUIDELINES

**PRIMARY RULE: Complete all analysis in ONE comprehensive response.**

- Show all verification steps within your single response
- Use markdown formatting for readability
- Create tables for comparative data (top 10-20 results)
- Bold key numbers and names for emphasis
- Include context about divisions, time periods, and data nuances
- If you catch an error, acknowledge and correct it in the same response

**Structure every response as:**
1. Filter Logic (what you're counting)
2. Sample Data (proof you filtered correctly)
3. Complete Results (the actual answer)
4. Context (important clarifications)

**All in ONE message. No follow-ups needed.**

---

# REMEMBER

Your reputation depends on ACCURACY and COMPLETENESS.

**The #1 error:** Confusing ENTRIES (total competitions) with WINS (1st place only)

**The #2 error:** Breaking analysis across multiple messages instead of one complete response

**When answering:**
1. Do the complete analysis FIRST (before responding)
2. Show your filter logic
3. Verify Placement = 1 for wins
4. Present everything together in one comprehensive message
5. State assumptions clearly

If you catch yourself about to give a contradictory answer, STOP and re-analyze from scratch, then present the corrected information in your response.

**NEVER say:** "Let me check that..." or "I'll analyze this now..." and then send results separately. 

**ALWAYS:** Analyze internally, then present complete verified results in one message.

---

# FORMATTING REQUIREMENTS

**For lists and rankings, use CLEAN formatting:**

✅ **GOOD - Clean numbered lists:**
1. Sam West - 48 wins
2. Joey Sogluizzo - 43 wins  
3. Jeff Hargett - 32 wins

✅ **GOOD - Clean bullet lists:**
• CSA competitions: 1995-2024
• NSDC competitions: 2001-2024
• Total Pro division contests: 347

❌ **BAD - Raw markdown tables with pipes:**
| Rank | Name | Wins |
|------|------|------|
| 1 | Sam West | 48 |

❌ **BAD - Messy delimited text:**
| 1 | Sam West | 48 | | 2 | Joey | 43 |

**Always use numbered lists for rankings and bullet points for categories. Keep it clean and readable."""

    def _get_cache_key(self, user_question, system_prompt):
        """Generate cache key for query+system prompt"""
        content = user_question + system_prompt
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key):
        """Get cached response if valid"""
        with _cache_lock:
            if cache_key in _response_cache:
                cached_data, timestamp = _response_cache[cache_key]
                if time.time() - timestamp < CACHE_EXPIRY_SECONDS:
                    print("⚡ Using cached response")
                    return cached_data
                else:
                    # Remove expired cache entry
                    del _response_cache[cache_key]
        return None
    
    def _cache_response(self, cache_key, response):
        """Cache the response"""
        with _cache_lock:
            _response_cache[cache_key] = (response, time.time())
            # Clean old entries if cache gets too big
            if len(_response_cache) > 100:
                oldest_key = min(_response_cache.keys(), 
                               key=lambda k: _response_cache[k][1])
                del _response_cache[oldest_key]

    def _call_anthropic_with_retry(self, **kwargs):
        """Call Anthropic API with exponential backoff retry logic optimized for Heroku"""
        max_retries = 2  # Reduced to 2 retries to stay under 30s timeout
        base_delay = 0.5  # Start with 500ms
        max_delay = 8  # Maximum 8s delay to avoid Heroku timeout
        
        for attempt in range(max_retries + 1):
            try:
                return self.client.messages.create(**kwargs)
            
            except RateLimitError as e:
                if attempt == max_retries:
                    print(f"❌ Rate limit exceeded after {max_retries} retries - returning cached/fallback response")
                    # Try to return a cached response or graceful fallback
                    return type('MockResponse', (), {
                        'content': [type('MockContent', (), {'text': 
                            "I'm experiencing high demand right now. Please try your question again in a moment. "
                            "For immediate help, try asking a more specific question or check the suggested questions below."})()],
                        'stop_reason': 'rate_limited'
                    })()
                
                # Fast exponential backoff with jitter - stay under Heroku 30s timeout
                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 0.5), max_delay)
                print(f"⏸️ Rate limited (attempt {attempt + 1}/{max_retries + 1}). Waiting {delay:.1f}s...")
                time.sleep(delay)
                
            except (APITimeoutError, APIConnectionError) as e:
                if attempt == max_retries:
                    print(f"❌ Connection failed after {max_retries} retries")
                    return type('MockResponse', (), {
                        'content': [type('MockContent', (), {'text': 
                            "Connection timeout. Please try a simpler question or wait a moment and try again."})()],
                        'stop_reason': 'timeout'
                    })()
                    
                # Quick retry for connection issues
                delay = min(base_delay * (1.2 ** attempt), 3)  # Max 3s delay
                print(f"🔄 {type(e).__name__} (attempt {attempt + 1}/{max_retries + 1}). Retrying in {delay:.1f}s...")
                time.sleep(delay)
                
            except Exception as e:
                # For other errors, don't retry but handle gracefully
                print(f"❌ Non-retryable error: {type(e).__name__}: {e}")
                return type('MockResponse', (), {
                    'content': [type('MockContent', (), {'text': 
                        f"I encountered an error processing your question. Please try rephrasing it or contact support if this continues."})()],
                    'stop_reason': 'error'
                })()

    def process_query(self, user_question):
        """Process user query with Claude API and function calling"""
        if not self.client:
            return "Error: API not configured. Please check environment variables."
        
        try:
            # Check smart cache first for cacheable queries
            if query_cache.should_cache_query(user_question):
                cached_response = query_cache.get(user_question)
                if cached_response:
                    print(f"🎯 Smart cache HIT for query: {user_question[:50]}...")
                    return cached_response
            
            system_prompt = self.create_system_prompt()
            
            # Check legacy cache as fallback
            cache_key = self._get_cache_key(user_question, system_prompt)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                print(f"🎯 Legacy cache HIT for query: {user_question[:50]}...")
                return cached_response
            
            # Add some recent data context for better answers
            sample_data = data_loader.get_csv_sample(5)
            context_prompt = f"\n\nHere are some recent contest records for context:\n{sample_data}"
            
            # Initialize messages
            messages = [{"role": "user", "content": user_question}]
            
            print(f"🎯 Processing query: {user_question}")
            
            # Initial API call with tools using retry logic
            response = self._call_anthropic_with_retry(
                model="claude-sonnet-4-5-20250929",
                max_tokens=3000,
                system=system_prompt + context_prompt,
                messages=messages,
                tools=TOOLS
            )
            
            print(f"🔄 Initial response stop reason: {response.stop_reason}")
            
            # Handle tool calls
            while response.stop_reason == "tool_use":
                print("🔧 Processing tool calls...")
                
                # Find ALL tool use blocks
                tool_uses = []
                for block in response.content:
                    if hasattr(block, 'type') and block.type == "tool_use":
                        tool_uses.append(block)
                
                if not tool_uses:
                    print("⚠️ No tool use blocks found")
                    break
                
                print(f"🛠️ Found {len(tool_uses)} tool calls")
                
                # Add assistant response to messages first
                messages.append({"role": "assistant", "content": response.content})
                
                # Execute ALL tools and collect results
                tool_results = []
                for tool_use in tool_uses:
                    print(f"🔧 Executing: {tool_use.name} with {tool_use.input}")
                    
                    tool_result = None
                    if tool_use.name == "query_csa_data":
                        tool_result = execute_query_csa_data(
                            query_type=tool_use.input.get("query_type"),
                            filters=tool_use.input.get("filters", {}),
                            limit=tool_use.input.get("limit", 10)
                        )
                        print(f"✅ Tool result: {tool_result.get('message', 'Success')}")
                    
                    if not tool_result:
                        tool_result = {"error": "Tool execution failed"}
                    
                    # Add this tool result to the collection
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps(convert_to_json_serializable(tool_result), indent=2)
                    })
                
                # Add ALL tool results in a single user message
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
                
                print("🔄 Continuing conversation with all tool results...")
                
                # Continue conversation
                response = self._call_anthropic_with_retry(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=3000,
                    system=system_prompt + context_prompt,
                    messages=messages,
                    tools=TOOLS
                )
                
                print(f"🔄 Follow-up response stop reason: {response.stop_reason}")
            
            # Extract final text response
            final_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    final_text += block.text
            
            # Cache successful responses in both systems
            if final_text and not final_text.startswith("Error:") and len(final_text) > 50:
                # Store in legacy cache
                self._cache_response(cache_key, final_text)
                
                # Store in smart cache if query is cacheable
                if query_cache.should_cache_query(user_question):
                    # Use longer TTL for statistical queries that don't change often
                    ttl = 600 if any(pattern in user_question.lower() for pattern in 
                        ['who has the most', 'top dancers', 'win rate', 'career statistics']) else 300
                    query_cache.set(user_question, final_text, ttl=ttl)
                    print(f"💾 Cached query in smart cache (TTL: {ttl}s)")
            
            print("✅ Query processing complete")
            return final_text
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"🔥 CHAT HANDLER ERROR: {error_type}: {error_msg}")
            print(f"🔍 FULL ERROR DETAILS: {repr(e)}")
            
            # Import traceback for better debugging
            import traceback
            print(f"📍 STACK TRACE: {traceback.format_exc()}")
            
            # Provide user-friendly error messages with more detail
            if "BadRequestError" in error_type:
                return "Invalid request format. Please rephrase your question and try again."
            elif "RateLimitError" in error_type:
                return "Too many requests. Please wait a moment before asking another question."
            elif "APIConnectionError" in error_type:
                return "Connection issue with AI service. Please try again in a moment."
            elif "APITimeoutError" in error_type:
                return "Request timed out. Your question might be too complex. Please try a simpler query."
            elif "AuthenticationError" in error_type:
                return "AI service authentication issue. Please contact support."
            elif "NotFoundError" in error_type and "model" in error_msg:
                return "AI model configuration issue. Please contact support."
            elif "ImportError" in error_type or "ModuleNotFoundError" in error_type:
                return "System configuration issue. Please contact support."
            elif "FileNotFoundError" in error_type:
                return "Database file not found. Please contact support to restore data files."
            else:
                # Return more specific error information for debugging
                return f"Processing error ({error_type}): {error_msg[:100]}. Please try rephrasing your question or contact support if this persists."

def convert_to_json_serializable(obj):
    """Convert numpy types and other non-JSON types to JSON-serializable formats"""
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

# Global instance
chat_handler = ChatHandler()
