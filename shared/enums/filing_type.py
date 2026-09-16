from enum import Enum


class FilingType(str, Enum):
    """
    SEC EDGAR filing types.
    These are the most financially significant forms
    that Argos will track and surface to users.
    """

    # Annual & Quarterly Reports
    FORM_10K = "10-K"        # Annual report — full year financials
    FORM_10K_A = "10-K/A"    # Amendment to annual report
    FORM_10Q = "10-Q"        # Quarterly report — 3 months financials
    FORM_10Q_A = "10-Q/A"    # Amendment to quarterly report

    # Current Reports & Material Events
    FORM_8K = "8-K"          # Material event — earnings, acquisitions, CEO change
    FORM_8K_A = "8-K/A"      # Amendment to 8-K

    # Registration & Offerings
    FORM_S1 = "S-1"          # IPO registration statement
    FORM_S1_A = "S-1/A"      # Amendment to S-1
    FORM_S3 = "S-3"          # Shelf registration
    FORM_424B4 = "424B4"     # Final prospectus — price and shares confirmed

    # Proxy & Governance
    FORM_DEF14A = "DEF 14A"  # Proxy statement — shareholder votes, exec pay
    FORM_DEFA14A = "DEFA14A" # Additional proxy materials

    # Insider & Ownership
    FORM_3 = "3"             # Initial statement of beneficial ownership
    FORM_4 = "4"             # Change in beneficial ownership — insider trades
    FORM_5 = "5"             # Annual statement of beneficial ownership
    FORM_SC13G = "SC 13G"    # Passive investor owns >5% of shares
    FORM_SC13D = "SC 13D"    # Active investor owns >5% — may seek control

    # Foreign Private Issuers
    FORM_20F = "20-F"        # Annual report for foreign companies
    FORM_6K = "6-K"          # Current report for foreign companies

    # Government & Municipal
    FORM_DOGE = "DOGE"       # Department of Government Efficiency reports
    FORM_USG = "USG"         # General US government filing


class FilingStatus(str, Enum):
    """
    Processing status of a filing in our system.
    Tracks where a filing is in the ingestion pipeline.
    """

    PENDING = "pending"        # Fetched, not yet normalised
    PROCESSING = "processing"  # Currently being normalised
    COMPLETED = "completed"    # Normalised and stored
    FAILED = "failed"          # Failed during processing
    STALE = "stale"            # Superseded by an amendment


class FilingSource(str, Enum):
    """
    Which data source the filing came from.
    Allows tracing every record back to its origin.
    """

    SEC_EDGAR = "sec_edgar"
    GOVTRACK = "govtrack"
    USASPENDING = "usaspending"
    OPENSECRETS = "opensecrets"
    MANUAL = "manual"