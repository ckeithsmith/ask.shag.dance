#!/usr/bin/env python3
"""
Data Update Script for Ask Shaggy Archive
Safely merge new contest data with existing records
"""

import pandas as pd
import sys
from pathlib import Path

def update_archive_data(new_data_file, backup=True):
    """
    Update the main archive with new contest data
    
    Args:
        new_data_file (str): Path to CSV with new/updated records
        backup (bool): Create backup of original data
    """
    
    # Paths
    current_dir = Path(__file__).parent.parent
    data_dir = current_dir / "data"
    original_file = data_dir / "Shaggy_Shag_Archives_Final.csv"
    backup_file = data_dir / f"Shaggy_Shag_Archives_Final_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    try:
        # Load existing data
        print(f"📊 Loading existing data from: {original_file}")
        existing_df = pd.read_csv(original_file)
        print(f"✅ Loaded {len(existing_df)} existing records")
        
        # Load new data
        print(f"📥 Loading new data from: {new_data_file}")
        new_df = pd.read_csv(new_data_file)
        print(f"✅ Loaded {len(new_df)} new records")
        
        # Validate columns match
        required_columns = [
            'Archive ID', 'Contest', 'Organization', 'Year', 'Host Club',
            'Placement', 'Division', 'Female Name', 'Male Name', 'Couple Name',
            'Judge 1', 'Judge 2', 'Judge 3', 'Judge 4', 'Judge 5', 'Record ID'
        ]
        
        missing_cols = set(required_columns) - set(new_df.columns)
        if missing_cols:
            print(f"❌ ERROR: Missing required columns in new data: {missing_cols}")
            return False
            
        print("✅ Column structure validated")
        
        # Create backup
        if backup:
            existing_df.to_csv(backup_file, index=False)
            print(f"💾 Backup created: {backup_file}")
        
        # Merge strategy: Update existing records, add new ones
        # Use 'Archive ID' as the key for updates
        
        # Remove duplicates from new data based on Archive ID
        new_df_clean = new_df.drop_duplicates(subset=['Archive ID'], keep='last')
        
        # Update existing records
        updated_df = existing_df.set_index('Archive ID')
        new_df_indexed = new_df_clean.set_index('Archive ID')
        
        # Find records to update vs add
        update_mask = new_df_indexed.index.isin(updated_df.index)
        records_to_update = new_df_indexed[update_mask]
        records_to_add = new_df_indexed[~update_mask]
        
        print(f"🔄 Records to update: {len(records_to_update)}")
        print(f"➕ Records to add: {len(records_to_add)}")
        
        # Apply updates
        updated_df.update(records_to_update)
        
        # Add new records
        final_df = pd.concat([updated_df, records_to_add]).reset_index()
        
        # Sort by Year, Contest for consistency
        final_df = final_df.sort_values(['Year', 'Contest', 'Division', 'Placement'])
        
        # Save updated file
        final_df.to_csv(original_file, index=False)
        print(f"✅ Updated archive saved: {len(final_df)} total records")
        
        # Summary
        print(f"""
📊 UPDATE SUMMARY:
- Original records: {len(existing_df)}
- New file records: {len(new_df)}
- Records updated: {len(records_to_update)}
- Records added: {len(records_to_add)}
- Final total: {len(final_df)}
- Backup: {backup_file.name if backup else 'None'}

🚀 Ready to deploy! Run:
   git add data/Shaggy_Shag_Archives_Final.csv
   git commit -m "📊 Data update: +{len(records_to_add)} new, ~{len(records_to_update)} updated"
   git push origin main
        """)
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_data.py <new_data_file.csv>")
        sys.exit(1)
    
    new_file = sys.argv[1]
    if not Path(new_file).exists():
        print(f"❌ ERROR: File not found: {new_file}")
        sys.exit(1)
    
    success = update_archive_data(new_file)
    sys.exit(0 if success else 1)