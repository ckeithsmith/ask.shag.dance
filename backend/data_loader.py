import pandas as pd
import PyPDF2
import os
from pathlib import Path

class DataLoader:
    def __init__(self):
        self.csv_data = None
        self.pdf_content = {}
        self.knowledge_base = ""
        
        # Get the data directory path relative to this file
        # This ensures it works whether running from backend/ or repo root
        current_file_dir = Path(__file__).parent
        self.data_dir = current_file_dir.parent / "data"
        print(f"🔍 Data directory path: {self.data_dir.absolute()}")
        
    def load_all_data(self):
        """Load CSV and extract all PDF content"""
        self.load_csv()
        self.extract_all_pdfs()
        self.create_knowledge_base()
        
    def load_csv(self):
        """Load the main contest archive CSV"""
        csv_path = self.data_dir / "Shaggy_Shag_Archives_Final.csv"
        try:
            if not csv_path.exists():
                print(f"❌ CSV file not found at: {csv_path.absolute()}")
                print(f"📁 Directory contents: {list(self.data_dir.glob('*')) if self.data_dir.exists() else 'Directory does not exist'}")
                return
                
            self.csv_data = pd.read_csv(csv_path)
            print(f"✅ Loaded CSV: {len(self.csv_data)} contest records")
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            
    def extract_pdf_text(self, pdf_path):
        """Extract text from a single PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            print(f"❌ Error extracting PDF {pdf_path}: {e}")
            return ""
            
    def extract_all_pdfs(self):
        """Extract text from all PDF files in data directory"""
        pdf_files = [
            ("CSA_Bylaws", "ByLawsCompleted10-2020.pdf"),
            ("CSA_Rules", "CSARulesAndRegsREVISED120223.pdf"), 
            ("NSDC_Rules", "NSDC NATIONAL SHAG DANCE CHAMPIONSHIP RULES.pdf"),
            ("NSDC_Songs", "NSDC Required Song List.pdf")
        ]
        
        for key, filename in pdf_files:
            pdf_path = self.data_dir / filename
            if pdf_path.exists():
                text = self.extract_pdf_text(pdf_path)
                self.pdf_content[key] = text
                print(f"✅ Extracted PDF: {key} ({len(text)} characters)")
            else:
                print(f"❌ PDF not found: {filename} at {pdf_path.absolute()}")
                
    def create_knowledge_base(self):
        """Create a comprehensive knowledge base string"""
        if self.csv_data is None:
            return
            
        # CSV Data Summary
        total_records = len(self.csv_data)
        years = f"{self.csv_data['Year'].min()}-{self.csv_data['Year'].max()}"
        organizations = self.csv_data['Organization'].value_counts()
        divisions = self.csv_data['Division'].value_counts()
        top_contests = self.csv_data['Contest'].value_counts().head(10)
        
        # Top competitors
        top_couples = self.csv_data['Couple Name'].value_counts().head(15)
        
        knowledge_base = f"""
COMPETITIVE SHAGGERS ASSOCIATION (CSA) ARCHIVE DATABASE
=======================================================

CONTEST DATA OVERVIEW:
- Total Records: {total_records} contest entries
- Time Period: {years} (35 years of competition data)
- Organizations: {dict(organizations)}
- Divisions: {dict(divisions)}

TOP 10 MOST FREQUENT CONTESTS:
{top_contests.to_string()}

TOP 15 MOST SUCCESSFUL COUPLES (by total contest entries):
{top_couples.to_string()}

DIVISION HIERARCHY (typical progression):
Junior → Novice → Amateur → Pro
Non-Pro and Overall are special categories

MAJOR ORGANIZATIONS:
- CSA: Competitive Shaggers Association (regional competitions)
- NSDC: National Shag Dance Championship (national championship)

"""
        
        # Add PDF content
        if self.pdf_content:
            knowledge_base += "\nRULES AND REGULATIONS CONTENT:\n"
            knowledge_base += "=" * 50 + "\n\n"
            
            for key, content in self.pdf_content.items():
                if content:
                    knowledge_base += f"{key.replace('_', ' ').upper()}:\n"
                    knowledge_base += content[:2000] + "\n\n"  # First 2000 chars of each PDF
                    
        self.knowledge_base = knowledge_base
        print(f"✅ Knowledge base created: {len(self.knowledge_base)} characters")
        
    def get_csv_sample(self, n=10):
        """Get sample CSV data for context"""
        if self.csv_data is not None:
            return self.csv_data.head(n).to_dict('records')
        return []
        
    def search_contests(self, query_terms):
        """Simple search in contest data"""
        if self.csv_data is None:
            return []
            
        results = self.csv_data.copy()
        
        # Simple text search across string columns
        text_columns = ['Contest', 'Host Club', 'Division', 'Female Name', 'Male Name', 'Couple Name']
        
        for term in query_terms:
            mask = False
            for col in text_columns:
                if col in results.columns:
                    mask |= results[col].str.contains(term, case=False, na=False)
            results = results[mask]
            
        return results.head(20).to_dict('records')

# Global instance
data_loader = DataLoader()