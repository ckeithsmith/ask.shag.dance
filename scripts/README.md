# 📊 Data Management Scripts

## Quick Data Update

### Using the Smart Update Script (Recommended)

```bash
# 1. Prepare your new data file (CSV format)
# 2. Run the update script
python scripts/update_data.py path/to/your/new_data.csv

# 3. Deploy the changes
git add data/Shaggy_Shag_Archives_Final.csv
git commit -m "📊 Data update: Added new contest results"
git push origin main
```

### Manual File Replacement

```bash
# Replace the entire dataset
cp your-complete-updated-file.csv data/Shaggy_Shag_Archives_Final.csv
git add data/Shaggy_Shag_Archives_Final.csv
git commit -m "📊 Complete data refresh"
git push origin main
```

## Required CSV Format

Your CSV must have these exact columns:

```
Archive ID, Contest, Organization, Year, Host Club, Placement, Division, Female Name, Male Name, Couple Name, Judge 1, Judge 2, Judge 3, Judge 4, Judge 5, Record ID
```

## Notes

- **Archive ID**: Unique identifier for each contest entry
- **Organization**: CSA, NSDC, or other
- **Year**: Contest year (used for trends)
- **Division**: Pro, Amateur, Novice, Junior 1, Junior 2, etc.
- **Placement**: 1-8 (1 = win)
- **Judge columns**: Can be empty for contests without judge data
- **Heroku deployment**: Changes automatically deploy when pushed to main branch

## Backup Policy

The update script automatically creates timestamped backups before making changes.