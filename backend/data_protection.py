"""
Data Protection Layer
Enforces limits and prevents raw data extraction
"""

class DataProtectionError(Exception):
    """Raised when a query violates data protection rules"""
    pass

class DataProtector:
    # Maximum records that can be returned in any response
    MAX_RECORDS = 100  # Allows comprehensive rankings (top dancer: 72 wins, top judge: 400+ placements)
    MAX_SAMPLE_RECORDS = 20  # Increased for better context in individual profiles

    # Forbidden query patterns
    FORBIDDEN_PATTERNS = [
        'export', 'download', 'csv', 'excel', 'dump', 'all records',
        'full database', 'complete list', 'entire dataset'
    ]

    @staticmethod
    def validate_query(user_question: str) -> tuple:
        """
        Check if query attempts to extract raw data
        Returns: (is_valid, error_message)
        """
        question_lower = user_question.lower()

        # Check for forbidden patterns
        for pattern in DataProtector.FORBIDDEN_PATTERNS:
            if pattern in question_lower:
                return (False,
                    f"This system provides statistical insights and analysis, not raw data exports. "
                    f"Please ask for specific analysis like 'top 10 winners' or 'trends by year'.")

        # Check for suspicious requests for all data
        if any(word in question_lower for word in ['all', 'every', 'complete']) and \
           any(word in question_lower for word in ['dancer', 'contest', 'record', 'entry']):
            if not any(word in question_lower for word in ['top', 'best', 'most', 'analysis', 'trend']):
                return (False,
                    "For data protection, I can provide top lists, statistics, and analysis - "
                    "but not complete unfiltered datasets. Try: 'top 100 Pro dancers' or 'analyze retention rates'.")

        return (True, "")

    @staticmethod
    def enforce_limit(data_list: list, limit: int, data_type: str = "records") -> list:
        """
        Enforce maximum limit on returned data
        Raises DataProtectionError if limit exceeded without user consent
        """
        if limit > DataProtector.MAX_RECORDS:
            raise DataProtectionError(
                f"Maximum {DataProtector.MAX_RECORDS} {data_type} can be returned. "
                f"Use filters or ask for 'top N' where N ≤ {DataProtector.MAX_RECORDS}."
            )

        return data_list[:min(limit, DataProtector.MAX_RECORDS)]

    @staticmethod
    def sanitize_sample_data(records: list, max_samples: int = MAX_SAMPLE_RECORDS) -> list:
        """
        Return only a sample of records for context, never full dataset
        """
        return records[:min(len(records), max_samples)]

    @staticmethod
    def create_summary_only_response(full_data: list, summary_stats: dict) -> dict:
        """
        Create response with summary statistics only, no raw records
        Use for large datasets where individual records aren't needed
        """
        return {
            "summary": summary_stats,
            "total_records_analyzed": len(full_data),
            "note": "Summary statistics shown. Individual records not included for data protection.",
            "sample_available": "Ask for specific dancer/contest for detailed records"
        }
