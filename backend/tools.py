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
                    "enum": ["count_wins", "dancer_record", "dancer_search", "smart_dancer_lookup", "top_dancers", "contest_results", "judge_statistics", "unique_counts", "win_statistics", "partnership_analysis", "career_statistics", "yearly_trends", "custom_query"],
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
                        },
                        "count_what": {
                            "type": "string",
                            "enum": ["male_dancers", "female_dancers", "all_dancers", "couples", "contests", "venues"],
                            "description": "What to count unique values of (for unique_counts query type)"
                        },
                        "metric": {
                            "type": "string",
                            "enum": ["wins", "entries", "win_rate"],
                            "description": "What metric to analyze (for statistics and trends)"
                        },
                        "dancer_name": {
                            "type": "string",
                            "description": "Search for a dancer name in both male and female columns"
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
    },
    {
        "name": "analyze_csa_data",
        "description": "Perform statistical analysis, aggregations, and trends on CSA database. Use for questions like 'how many', 'show trends', 'analyze', 'compare', 'what percentage'. Returns aggregated summaries, not individual records.",
        "input_schema": {
            "type": "object",
            "properties": {
                "analysis_type": {
                    "type": "string",
                    "enum": [
                        "yearly_active_dancers",
                        "judge_dancer_frequency",
                        "judge_panel_combinations",
                        "judge_dancer_outcomes",
                        "retention_analysis",
                        "career_progression_time",
                        "partnership_success_rates",
                        "division_migration_patterns",
                        "win_concentration_analysis"
                    ],
                    "description": "Type of statistical analysis to perform"
                },
                "filters": {
                    "type": "object",
                    "properties": {
                        "organization": {"type": "string"},
                        "division": {"type": "string"},
                        "start_year": {"type": "integer"},
                        "end_year": {"type": "integer"},
                        "judge_name": {"type": "string"},
                        "dancer_name": {"type": "string"},
                        "min_occurrences": {"type": "integer", "description": "Minimum threshold"}
                    }
                },
                "limit": {
                    "type": "integer",
                    "default": 20,
                    "description": "Max results to return"
                }
            },
            "required": ["analysis_type"]
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
    
    # SECURITY: Enforce absolute maximum limit
    if limit > 50:
        limit = 50
        print(f"🔒 SECURITY: Limit capped at 50 (was {limit})")
    
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
        
        elif query_type == "dancer_search":
            # Smart search for a dancer name - checks both gender columns AND common variations
            search_name = filters.get('dancer_name', '').strip()
            if not search_name:
                result["error"] = "dancer_name is required for dancer_search"
                return result
            
            # Search in both Male Name and Female Name columns
            male_matches = df[df['Male Name'].str.contains(search_name, case=False, na=False)]['Male Name'].unique()
            female_matches = df[df['Female Name'].str.contains(search_name, case=False, na=False)]['Female Name'].unique()
            
            all_matches = list(set(list(male_matches) + list(female_matches)))
            all_matches.sort()
            
            if len(all_matches) == 0:
                result["matches"] = []
                result["message"] = f"No dancers found matching '{search_name}'"
                result["suggestion"] = "Try checking the spelling or using fewer characters"
            elif len(all_matches) == 1:
                # Exact match found - return their competition summary
                exact_name = all_matches[0]
                dancer_df = df[(df['Male Name'] == exact_name) | (df['Female Name'] == exact_name)]
                
                # Apply any additional filters
                for filter_key, filter_value in filters.items():
                    if filter_key == 'dancer_name':
                        continue
                    if filter_key == 'organization' and filter_value and filter_value != 'Both':
                        dancer_df = dancer_df[dancer_df['Organization'] == filter_value]
                    elif filter_key == 'division' and filter_value:
                        dancer_df = dancer_df[dancer_df['Division'] == filter_value]
                    elif filter_key == 'start_year' and filter_value:
                        end_year = filters.get('end_year', 2024)
                        dancer_df = dancer_df[(dancer_df['Year'] >= filter_value) & (dancer_df['Year'] <= end_year)]
                
                total_contests = len(dancer_df)
                wins = len(dancer_df[dancer_df['Placement'] == 1])
                divisions = dancer_df['Division'].unique().tolist()
                years = f"{dancer_df['Year'].min()}-{dancer_df['Year'].max()}"
                
                result["exact_match"] = exact_name
                result["total_contests"] = total_contests
                result["wins"] = wins
                result["divisions"] = divisions
                result["years_active"] = years
                result["message"] = f"Found exact match: {exact_name} ({wins} wins, {total_contests} contests)"
            else:
                # Multiple matches - return list for user to pick
                result["matches"] = all_matches[:10]  # Limit to 10 suggestions
                result["match_count"] = len(all_matches)
                result["message"] = f"Found {len(all_matches)} potential matches for '{search_name}'"
                if len(all_matches) > 10:
                    result["note"] = "Showing first 10 matches. Try being more specific."
        
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
        
        # ========== SMART DANCER LOOKUP (PREVENTS MULTI-TURN CONVERSATIONS) ==========
        elif query_type == "smart_dancer_lookup":
            # This query type prevents the "Brittney Miller" multi-call issue from Heroku logs
            search_name = filters.get('dancer_name', '').strip()
            if not search_name:
                result["error"] = "dancer_name is required for smart_dancer_lookup"
                return result
            
            # Comprehensive search that handles all cases in ONE call
            print(f"🔍 Smart lookup for '{search_name}'")
            
            # 1. Try exact matches in both gender columns
            exact_male_df = df[df['Male Name'] == search_name]
            exact_female_df = df[df['Female Name'] == search_name]
            exact_combined_df = pd.concat([exact_male_df, exact_female_df]).drop_duplicates()
            
            if len(exact_combined_df) > 0:
                print(f"✅ Found exact match: {len(exact_combined_df)} records")
                dancer_df = exact_combined_df
            else:
                # 2. Try partial matches
                partial_male_df = df[df['Male Name'].str.contains(search_name, case=False, na=False)]
                partial_female_df = df[df['Female Name'].str.contains(search_name, case=False, na=False)]
                partial_combined_df = pd.concat([partial_male_df, partial_female_df]).drop_duplicates()
                
                if len(partial_combined_df) > 0:
                    print(f"🔍 Using partial match: {len(partial_combined_df)} records")
                    # Get unique name matches for user feedback
                    male_matches = partial_male_df['Male Name'].unique()
                    female_matches = partial_female_df['Female Name'].unique()
                    all_matches = list(set(list(male_matches) + list(female_matches)))
                    
                    result["possible_matches"] = all_matches[:10]  # Limit for readability
                    result["message"] = f"No exact match for '{search_name}'. Found {len(all_matches)} possible matches."
                    return result
                else:
                    result["message"] = f"No dancers found matching '{search_name}' in any form."
                    return result
            
            # Apply additional filters
            if 'organization' in filters and filters['organization'] and filters['organization'] != 'Both':
                dancer_df = dancer_df[dancer_df['Organization'] == filters['organization']]
            
            if 'division' in filters and filters['division']:
                dancer_df = dancer_df[dancer_df['Division'] == filters['division']]
            
            if 'start_year' in filters and filters['start_year']:
                end_year = filters.get('end_year', dancer_df['Year'].max())
                dancer_df = dancer_df[(dancer_df['Year'] >= filters['start_year']) & 
                                    (dancer_df['Year'] <= end_year)]
            
            # Return comprehensive summary to prevent follow-up queries
            total_contests = len(dancer_df)
            total_wins = len(dancer_df[dancer_df['Placement'] == 1])
            
            # Division breakdown
            division_summary = {}
            for div in dancer_df['Division'].unique():
                div_df = dancer_df[dancer_df['Division'] == div]
                div_wins = len(div_df[div_df['Placement'] == 1])
                division_summary[div] = {"contests": len(div_df), "wins": div_wins}
            
            # Career span
            if total_contests > 0:
                career_start = int(dancer_df['Year'].min())
                career_end = int(dancer_df['Year'].max())
                career_span = f"{career_start}-{career_end}" if career_start != career_end else str(career_start)
            else:
                career_span = "No data"
            
            result["dancer_name"] = search_name
            result["summary"] = {
                "total_contests": total_contests,
                "total_wins": total_wins, 
                "win_rate": round((total_wins/total_contests)*100, 1) if total_contests > 0 else 0,
                "career_span": career_span,
                "organizations": dancer_df['Organization'].unique().tolist(),
                "division_breakdown": division_summary
            }
            
            # Sample recent contests for context
            recent_contests = dancer_df.nlargest(min(5, limit), 'Year')[
                ['Contest', 'Year', 'Division', 'Placement', 'Organization']
            ].to_dict('records')
            
            result["recent_contests"] = recent_contests
            result["message"] = f"Complete profile for {search_name}: {total_wins} wins in {total_contests} contests"
            
        # ========== NEW HIGH-VALUE QUERY TYPES ==========
        
        # UNIQUE COUNTS
        elif query_type == "unique_counts":
            count_what = filters.get('count_what', 'all_dancers')
            
            if count_what == "all_dancers":
                all_names = pd.concat([filtered_df['Male Name'], filtered_df['Female Name']]).dropna().unique()
                unique_males = filtered_df['Male Name'].dropna().unique()
                unique_females = filtered_df['Female Name'].dropna().unique()
                
                return {
                    "query": "Total unique dancers",
                    "filters_applied": filters,
                    "unique_dancers_total": len(all_names),
                    "unique_male_dancers": len(unique_males),
                    "unique_female_dancers": len(unique_females),
                    "total_contest_entries": len(filtered_df)
                }
            
            elif count_what == "male_dancers":
                unique_males = filtered_df['Male Name'].dropna().unique()
                return {
                    "query": "Unique male dancers",
                    "filters_applied": filters,
                    "unique_count": len(unique_males),
                    "total_contest_entries": len(filtered_df)
                }
            
            elif count_what == "female_dancers":
                unique_females = filtered_df['Female Name'].dropna().unique()
                return {
                    "query": "Unique female dancers",
                    "filters_applied": filters,
                    "unique_count": len(unique_females),
                    "total_contest_entries": len(filtered_df)
                }
            
            elif count_what == "couples":
                unique_couples = filtered_df['Couple Name'].dropna().unique()
                return {
                    "query": "Unique couple pairings",
                    "filters_applied": filters,
                    "unique_count": len(unique_couples),
                    "total_contest_entries": len(filtered_df)
                }
            
            elif count_what == "contests":
                unique_contests = filtered_df['Contest'].dropna().unique()
                return {
                    "query": "Unique contests",
                    "filters_applied": filters,
                    "unique_count": len(unique_contests),
                    "total_contest_entries": len(filtered_df)
                }
            
            elif count_what == "venues":
                unique_venues = filtered_df['Host Club'].dropna().unique()
                return {
                    "query": "Unique venues",
                    "filters_applied": filters,
                    "unique_count": len(unique_venues),
                    "total_contest_entries": len(filtered_df)
                }
        
        # WIN STATISTICS
        elif query_type == "win_statistics":
            dancer_name = filters.get('dancer_name')
            if not dancer_name:
                return {"error": "dancer_name is required for win_statistics"}
            
            # Get dancer's records
            dancer_df = filtered_df[
                (filtered_df['Male Name'] == dancer_name) | 
                (filtered_df['Female Name'] == dancer_name)
            ]
            
            if len(dancer_df) == 0:
                return {"error": f"No records found for {dancer_name}"}
            
            total_contests = len(dancer_df)
            wins = len(dancer_df[dancer_df['Placement'] == 1])
            top_3 = len(dancer_df[dancer_df['Placement'] <= 3])
            win_rate = (wins / total_contests * 100) if total_contests > 0 else 0
            
            return {
                "query": f"Win statistics for {dancer_name}",
                "dancer": dancer_name,
                "filters_applied": filters,
                "total_contests": total_contests,
                "wins": wins,
                "top_3_finishes": top_3,
                "win_rate_percent": round(win_rate, 2)
            }
        
        # PARTNERSHIP ANALYSIS
        elif query_type == "partnership_analysis":
            dancer_name = filters.get('dancer_name')
            if not dancer_name:
                return {"error": "dancer_name is required for partnership_analysis"}
            
            dancer_df = filtered_df[
                (filtered_df['Male Name'] == dancer_name) | 
                (filtered_df['Female Name'] == dancer_name)
            ]
            
            if len(dancer_df) == 0:
                return {"error": f"No records found for {dancer_name}"}
            
            # Determine if male or female to find partners
            is_male = (dancer_df['Male Name'] == dancer_name).any()
            partner_col = 'Female Name' if is_male else 'Male Name'
            
            # Group by partner
            partnership_stats = []
            for partner in dancer_df[partner_col].dropna().unique():
                partner_df = dancer_df[dancer_df[partner_col] == partner]
                wins = len(partner_df[partner_df['Placement'] == 1])
                contests = len(partner_df)
                
                partnership_stats.append({
                    "partner": partner,
                    "contests_together": contests,
                    "wins_together": wins,
                    "win_rate": round(wins / contests * 100, 2) if contests > 0 else 0
                })
            
            # Sort by contests together (most partnerships first)
            partnership_stats.sort(key=lambda x: x['contests_together'], reverse=True)
            
            return {
                "query": f"Partnership analysis for {dancer_name}",
                "dancer": dancer_name,
                "filters_applied": filters,
                "total_partners": len(partnership_stats),
                "partnerships": partnership_stats[:limit]
            }
        
        # CAREER STATISTICS
        elif query_type == "career_statistics":
            dancer_name = filters.get('dancer_name')
            if not dancer_name:
                return {"error": "dancer_name is required for career_statistics"}
            
            dancer_df = filtered_df[
                (filtered_df['Male Name'] == dancer_name) | 
                (filtered_df['Female Name'] == dancer_name)
            ]
            
            if len(dancer_df) == 0:
                return {"error": f"No records found for {dancer_name}"}
            
            first_year = dancer_df['Year'].min()
            last_year = dancer_df['Year'].max()
            years_active = last_year - first_year + 1
            years_competed = dancer_df['Year'].nunique()
            
            # Partners
            is_male = (dancer_df['Male Name'] == dancer_name).any()
            partner_col = 'Female Name' if is_male else 'Male Name'
            partners = dancer_df[partner_col].dropna().unique()
            
            # Organizations and divisions
            orgs = dancer_df['Organization'].value_counts().to_dict()
            divisions = dancer_df['Division'].unique().tolist()
            
            return {
                "query": f"Career statistics for {dancer_name}",
                "dancer": dancer_name,
                "filters_applied": filters,
                "first_contest_year": int(first_year),
                "last_contest_year": int(last_year),
                "career_span_years": years_active,
                "years_competed": years_competed,
                "total_contests": len(dancer_df),
                "unique_partners": len(partners),
                "organizations": orgs,
                "divisions_competed": divisions
            }
        
        # YEARLY TRENDS  
        elif query_type == "yearly_trends":
            metric = filters.get('metric', 'entries')
            
            if metric == 'wins':
                yearly_data = filtered_df[filtered_df['Placement'] == 1].groupby('Year').size()
            else:  # entries
                yearly_data = filtered_df.groupby('Year').size()
            
            yearly_dict = yearly_data.to_dict()
            
            return {
                "query": f"Yearly trends - {metric}",
                "filters_applied": filters,
                "metric": metric,
                "yearly_data": {int(year): int(count) for year, count in yearly_dict.items()},
                "total_years": len(yearly_data),
                "peak_year": int(yearly_data.idxmax()) if len(yearly_data) > 0 else None,
                "peak_count": int(yearly_data.max()) if len(yearly_data) > 0 else None
            }
        
        return result
    
    except Exception as e:
        print(f"🔥 QUERY ERROR: {type(e).__name__}: {str(e)}")
        return {
            "error": f"Query execution failed: {type(e).__name__}: {str(e)}",
            "query_type": query_type,
            "filters": filters
        }

def execute_analyze_csa_data(analysis_type, filters={}, limit=20):
    """
    Execute analytical queries returning aggregated/summarized data
    Different from query_csa_data which returns individual records
    """
    try:
        # Load CSV
        current_dir = Path(__file__).parent
        csv_path = current_dir.parent / "data" / "Shaggy_Shag_Archives_Final.csv"

        if not csv_path.exists():
            csv_path = Path("/app/data/Shaggy_Shag_Archives_Final.csv")

        if not csv_path.exists():
            return {"error": f"Database not found at {csv_path}"}

        df = pd.read_csv(csv_path)

        # Apply base filters
        if filters.get('organization') and filters['organization'] != 'Both':
            df = df[df['Organization'] == filters['organization']]

        if filters.get('division'):
            df = df[df['Division'] == filters['division']]

        if filters.get('start_year') and filters.get('end_year'):
            df = df[(df['Year'] >= filters['start_year']) & (df['Year'] <= filters['end_year'])]

        # Route to analysis functions
        if analysis_type == "yearly_active_dancers":
            yearly = df.groupby('Year').agg({
                'Male Name': pd.Series.nunique,
                'Female Name': pd.Series.nunique
            }).rename(columns={'Male Name': 'Male', 'Female Name': 'Female'})
            yearly['Total'] = yearly['Male'] + yearly['Female']
            yearly['Change'] = yearly['Total'].diff()

            return {
                "analysis": "Yearly active dancers",
                "filters_applied": filters,
                "yearly_data": yearly.reset_index().to_dict('records')
            }

        elif analysis_type == "judge_dancer_frequency":
            judge_name = filters.get('judge_name')
            if not judge_name:
                return {"error": "judge_name required for this analysis"}

            # Find contests where this judge participated
            judge_mask = (
                (df['Judge 1'] == judge_name) |
                (df['Judge 2'] == judge_name) |
                (df['Judge 3'] == judge_name) |
                (df['Judge 4'] == judge_name) |
                (df['Judge 5'] == judge_name)
            )
            judge_contests = df[judge_mask]

            # Count male dancers
            male_counts = judge_contests['Male Name'].value_counts().head(limit)

            results = []
            for dancer, count in male_counts.items():
                dancer_with_judge = judge_contests[judge_contests['Male Name'] == dancer]
                wins = len(dancer_with_judge[dancer_with_judge['Placement'] == 1])
                win_rate = (wins / count * 100) if count > 0 else 0

                results.append({
                    "dancer": dancer,
                    "times_judged_by": judge_name,
                    "count": int(count),
                    "wins_when_judged": int(wins),
                    "win_rate_pct": round(win_rate, 1)
                })

            return {
                "analysis": f"Dancers most frequently judged by {judge_name}",
                "judge": judge_name,
                "total_contests_judged": len(judge_contests),
                "results": results
            }

        elif analysis_type == "judge_panel_combinations":
            from itertools import combinations

            min_occ = filters.get('min_occurrences', 5)
            panels = []

            for _, row in df.iterrows():
                judges = []
                for i in range(1, 6):
                    judge = row.get(f'Judge {i}')
                    if pd.notna(judge):
                        judges.append(judge)

                if len(judges) >= 2:
                    for combo in combinations(sorted(judges), 2):
                        panels.append(combo)

            panel_counts = pd.Series(panels).value_counts()
            panel_counts = panel_counts[panel_counts >= min_occ]

            results = []
            for panel, count in panel_counts.head(limit).items():
                results.append({
                    "judge_1": panel[0],
                    "judge_2": panel[1],
                    "times_together": int(count)
                })

            return {
                "analysis": "Judge panel combinations",
                "min_occurrences": min_occ,
                "total_unique_combinations": len(panel_counts),
                "results": results
            }

        elif analysis_type == "judge_dancer_outcomes":
            dancer_name = filters.get('dancer_name')
            if not dancer_name:
                return {"error": "dancer_name required for this analysis"}

            min_contests = filters.get('min_occurrences', 10)

            # Get dancer's contests
            dancer_df = df[(df['Male Name'] == dancer_name) | (df['Female Name'] == dancer_name)]

            if len(dancer_df) == 0:
                return {"error": f"No records found for {dancer_name}"}

            # Calculate overall win rate
            overall_wins = len(dancer_df[dancer_df['Placement'] == 1])
            overall_rate = (overall_wins / len(dancer_df) * 100) if len(dancer_df) > 0 else 0

            # Analyze each judge
            judge_stats = {}
            for judge_col in ['Judge 1', 'Judge 2', 'Judge 3', 'Judge 4', 'Judge 5']:
                for judge in df[judge_col].dropna().unique():
                    with_judge = dancer_df[
                        (dancer_df['Judge 1'] == judge) |
                        (dancer_df['Judge 2'] == judge) |
                        (dancer_df['Judge 3'] == judge) |
                        (dancer_df['Judge 4'] == judge) |
                        (dancer_df['Judge 5'] == judge)
                    ]

                    if len(with_judge) >= min_contests:
                        wins = len(with_judge[with_judge['Placement'] == 1])
                        win_rate = (wins / len(with_judge) * 100)

                        if judge not in judge_stats:
                            judge_stats[judge] = {
                                "judge": judge,
                                "contests": int(len(with_judge)),
                                "wins": int(wins),
                                "win_rate_pct": round(win_rate, 1),
                                "vs_overall": round(win_rate - overall_rate, 1)
                            }

            results = sorted(judge_stats.values(), key=lambda x: x['win_rate_pct'], reverse=True)

            return {
                "analysis": f"Judge-specific outcomes for {dancer_name}",
                "dancer": dancer_name,
                "overall_contests": len(dancer_df),
                "overall_wins": int(overall_wins),
                "overall_win_rate_pct": round(overall_rate, 1),
                "min_contests_threshold": min_contests,
                "judge_specific_outcomes": results[:limit]
            }

        elif analysis_type == "retention_analysis":
            # Find Amateur dancers
            amateur_dancers = set(
                df[df['Division'] == 'Amateur']['Male Name'].dropna().unique().tolist() +
                df[df['Division'] == 'Amateur']['Female Name'].dropna().unique().tolist()
            )

            # Find Pro dancers
            pro_dancers = set(
                df[df['Division'] == 'Pro']['Male Name'].dropna().unique().tolist() +
                df[df['Division'] == 'Pro']['Female Name'].dropna().unique().tolist()
            )

            made_it_to_pro = amateur_dancers.intersection(pro_dancers)

            return {
                "analysis": "Amateur to Pro retention",
                "total_amateur_dancers": len(amateur_dancers),
                "reached_pro": len(made_it_to_pro),
                "retention_rate_pct": round(len(made_it_to_pro) / len(amateur_dancers) * 100, 1) if amateur_dancers else 0,
                "still_amateur_only": len(amateur_dancers) - len(made_it_to_pro)
            }

        elif analysis_type == "career_progression_time":
            # Calculate average time from Amateur to Pro
            amateur_dancers = set(
                df[df['Division'] == 'Amateur']['Male Name'].dropna().unique().tolist() +
                df[df['Division'] == 'Amateur']['Female Name'].dropna().unique().tolist()
            )

            pro_dancers = set(
                df[df['Division'] == 'Pro']['Male Name'].dropna().unique().tolist() +
                df[df['Division'] == 'Pro']['Female Name'].dropna().unique().tolist()
            )

            made_it = amateur_dancers.intersection(pro_dancers)
            progression_times = []

            for dancer in made_it:
                amateur_years = df[
                    ((df['Male Name'] == dancer) | (df['Female Name'] == dancer)) &
                    (df['Division'] == 'Amateur')
                ]['Year']

                pro_years = df[
                    ((df['Male Name'] == dancer) | (df['Female Name'] == dancer)) &
                    (df['Division'] == 'Pro')
                ]['Year']

                if len(amateur_years) > 0 and len(pro_years) > 0:
                    first_amateur = int(amateur_years.min())
                    first_pro = int(pro_years.min())
                    years_to_pro = first_pro - first_amateur

                    if years_to_pro > 0:
                        progression_times.append(years_to_pro)

            return {
                "analysis": "Time to progress from Amateur to Pro",
                "dancers_analyzed": len(progression_times),
                "avg_years_to_pro": round(sum(progression_times) / len(progression_times), 1) if progression_times else None,
                "fastest_progression_years": int(min(progression_times)) if progression_times else None,
                "slowest_progression_years": int(max(progression_times)) if progression_times else None
            }

        else:
            return {"error": f"Analysis type '{analysis_type}' not yet implemented"}

    except Exception as e:
        import traceback
        return {
            "error": f"Analysis failed: {str(e)}",
            "traceback": traceback.format_exc()
        }