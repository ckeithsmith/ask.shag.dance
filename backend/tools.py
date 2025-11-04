"""
CSA Shag Archive Data Query Tools
Function calling tools for Claude to access real competition data
"""

import pandas as pd
import os
from pathlib import Path

# Tool definition for Claude function calling
TOOLS = [
    {
        "name": "query_csa_data",
        "description": "Query the CSA Shag Dance Archive database. Use this tool for ANY statistical question about wins, placements, dancers, or contests. This tool accesses the actual CSV data with 7,868 contest records.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "enum": ["count_wins", "dancer_record", "top_dancers", "contest_results", "judge_statistics", "custom_query"],
                    "description": "Type of query to run"
                },
                "filters": {
                    "type": "object",
                    "properties": {
                        "division": {
                            "type": "string",
                            "description": "Filter by division (e.g., 'Pro', 'Amateur', 'Novice', 'Sr Pro', 'Junior 1', 'Junior 2', 'Masters', 'Non-Pro', 'Overall')"
                        },
                        "organization": {
                            "type": "string",
                            "description": "Filter by organization ('CSA', 'NSDC', or 'Both')"
                        },
                        "placement": {
                            "type": "integer",
                            "description": "Filter by placement (1 for wins, 2-8 for other placements)"
                        },
                        "male_name": {
                            "type": "string",
                            "description": "Filter by male dancer name (exact match)"
                        },
                        "female_name": {
                            "type": "string",
                            "description": "Filter by female dancer name (exact match)"
                        },
                        "year": {
                            "type": "integer",
                            "description": "Filter by year"
                        },
                        "start_year": {
                            "type": "integer",
                            "description": "Filter by starting year (inclusive) - use with end_year for year ranges"
                        },
                        "end_year": {
                            "type": "integer",
                            "description": "Filter by ending year (inclusive) - use with start_year for year ranges"
                        },
                        "gender": {
                            "type": "string",
                            "enum": ["male", "female"],
                            "description": "Count wins by male or female dancers"
                        },
                        "contest": {
                            "type": "string",
                            "description": "Filter by contest name"
                        }
                    },
                    "description": "Filters to apply to the data"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return (default 10, max 50)",
                    "default": 10
                }
            },
            "required": ["query_type", "filters"]
        }
    }
]

def execute_query_csa_data(query_type, filters, limit=10):
    """
    Execute queries against the CSA database
    
    Args:
        query_type (str): Type of query to execute
        filters (dict): Filters to apply to the data
        limit (int): Number of results to return
        
    Returns:
        dict: Query results with metadata
    """
    
    try:
        # Load the CSV data - handle both development and production paths
        current_dir = Path(__file__).parent
        csv_path = current_dir.parent / "data" / "Shaggy_Shag_Archives_Final.csv"
        
        if not csv_path.exists():
            # Fallback for different deployment structures
            csv_path = Path("/app/data/Shaggy_Shag_Archives_Final.csv")
        
        if not csv_path.exists():
            return {
                "error": f"Database file not found. Searched: {csv_path}",
                "query_type": query_type,
                "filters": filters
            }
        
        print(f"🔍 Loading CSV from: {csv_path}")
        df = pd.read_csv(csv_path)
        print(f"📊 Loaded {len(df)} total records")
        
        # Apply filters
        filtered_df = df.copy()
        original_count = len(filtered_df)
        
        # Apply each filter
        if 'division' in filters and filters['division']:
            filtered_df = filtered_df[filtered_df['Division'] == filters['division']]
            print(f"🎯 Division filter '{filters['division']}': {len(filtered_df)} records")
        
        if 'organization' in filters and filters['organization'] and filters['organization'] != 'Both':
            filtered_df = filtered_df[filtered_df['Organization'] == filters['organization']]
            print(f"🏢 Organization filter '{filters['organization']}': {len(filtered_df)} records")
        
        if 'placement' in filters and filters['placement'] is not None:
            filtered_df = filtered_df[filtered_df['Placement'] == filters['placement']]
            print(f"🏆 Placement filter '{filters['placement']}': {len(filtered_df)} records")
        
        if 'male_name' in filters and filters['male_name']:
            filtered_df = filtered_df[filtered_df['Male Name'] == filters['male_name']]
            print(f"👨 Male name filter '{filters['male_name']}': {len(filtered_df)} records")
        
        if 'female_name' in filters and filters['female_name']:
            filtered_df = filtered_df[filtered_df['Female Name'] == filters['female_name']]
            print(f"👩 Female name filter '{filters['female_name']}': {len(filtered_df)} records")
        
        if 'year' in filters and filters['year']:
            filtered_df = filtered_df[filtered_df['Year'] == filters['year']]
            print(f"📅 Year filter '{filters['year']}': {len(filtered_df)} records")
        
        # Year range filtering (for queries like "last 10 years")
        if 'start_year' in filters and 'end_year' in filters and filters['start_year'] and filters['end_year']:
            filtered_df = filtered_df[
                (filtered_df['Year'] >= filters['start_year']) & 
                (filtered_df['Year'] <= filters['end_year'])
            ]
            print(f"📅 Year range filter {filters['start_year']}-{filters['end_year']}: {len(filtered_df)} records")
        
        if 'contest' in filters and filters['contest']:
            filtered_df = filtered_df[filtered_df['Contest'].str.contains(filters['contest'], case=False, na=False)]
            print(f"🏆 Contest filter '{filters['contest']}': {len(filtered_df)} records")
        
        # Ensure limit is reasonable
        limit = min(limit, 50)
        
        # Execute query based on type
        result = {
            "query_type": query_type,
            "filters_applied": filters,
            "total_database_records": original_count,
            "filtered_records": len(filtered_df),
            "limit": limit
        }
        
        if query_type == "count_wins" or query_type == "top_dancers":
            gender = filters.get('gender', 'male')
            name_column = 'Male Name' if gender == 'male' else 'Female Name'
            
            if len(filtered_df) == 0:
                result["results"] = []
                result["message"] = f"No records found matching the filters"
            else:
                counts = filtered_df[name_column].value_counts().head(limit)
                
                result["results"] = [
                    {"name": name, "count": int(count)} 
                    for name, count in counts.items()
                ]
                result["message"] = f"Top {min(len(counts), limit)} {gender} dancers"
        
        elif query_type == "dancer_record":
            # Get complete record for a specific dancer
            if len(filtered_df) == 0:
                result["records"] = []
                result["message"] = "No records found for this dancer with the specified filters"
            else:
                records = filtered_df[['Contest', 'Year', 'Division', 'Organization', 'Placement', 'Male Name', 'Female Name', 'Host Club']].head(limit)
                result["records"] = records.to_dict('records')
                result["message"] = f"Found {len(filtered_df)} total records, showing first {min(len(records), limit)}"
        
        elif query_type == "contest_results":
            # Get results from specific contests
            if len(filtered_df) == 0:
                result["records"] = []
                result["message"] = "No contest results found matching the filters"
            else:
                records = filtered_df[['Contest', 'Year', 'Division', 'Placement', 'Male Name', 'Female Name', 'Organization']].head(limit)
                result["records"] = records.to_dict('records')
                result["message"] = f"Found {len(filtered_df)} contest results, showing first {min(len(records), limit)}"
        
        elif query_type == "judge_statistics":
            # Count judges across all 5 judge columns
            judge_columns = ['Judge 1', 'Judge 2', 'Judge 3', 'Judge 4', 'Judge 5']
            
            # Check if judge columns exist in the data
            available_judge_columns = [col for col in judge_columns if col in filtered_df.columns]
            
            if not available_judge_columns:
                result["results"] = []
                result["message"] = "No judge columns found in the database"
                result["note"] = "Judge data may not be available for this dataset"
            else:
                # Combine all judge columns into one series
                all_judges_list = []
                for col in available_judge_columns:
                    judges_in_col = filtered_df[col].dropna()
                    all_judges_list.extend(judges_in_col.tolist())
                
                if not all_judges_list:
                    result["results"] = []
                    result["message"] = "No judge data found in the filtered records"
                    result["records_with_judge_data"] = 0
                    result["records_without_judge_data"] = len(filtered_df)
                else:
                    # Count judge occurrences
                    judge_series = pd.Series(all_judges_list)
                    judge_counts = judge_series.value_counts().head(limit)
                    
                    # Calculate statistics about judge data completeness
                    records_with_judges = filtered_df[available_judge_columns].notna().any(axis=1).sum()
                    records_without_judges = len(filtered_df) - records_with_judges
                    
                    result["results"] = [
                        {"judge_name": judge, "times_judged": int(count)} 
                        for judge, count in judge_counts.items()
                    ]
                    result["message"] = f"Top {min(len(judge_counts), limit)} judges by contest appearances"
                    result["total_contest_records"] = len(filtered_df)
                    result["records_with_judge_data"] = int(records_with_judges)
                    result["records_without_judge_data"] = int(records_without_judges)
                    result["note"] = f"{records_without_judges} records have no judge data (likely NSDC contests or incomplete data)"
        
        elif query_type == "custom_query":
            # Return filtered data sample
            if len(filtered_df) == 0:
                result["sample_records"] = []
                result["message"] = "No records found matching the custom filters"
            else:
                sample = filtered_df.head(limit)
                result["sample_records"] = sample.to_dict('records')
                result["message"] = f"Custom query returned {len(filtered_df)} records, showing first {min(len(sample), limit)}"
        
        return result
    
    except Exception as e:
        print(f"🔥 QUERY ERROR: {type(e).__name__}: {str(e)}")
        return {
            "error": f"Query execution failed: {type(e).__name__}: {str(e)}",
            "query_type": query_type,
            "filters": filters
        }