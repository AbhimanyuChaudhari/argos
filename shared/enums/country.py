from enum import Enum


class CountryCode(str, Enum):
    """
    ISO 3166-1 alpha-2 country codes.
    str mixin makes these JSON serializable automatically.
    Add countries here as you onboard new data sources.
    """

    # Americas
    US = "US"  # United States
    CA = "CA"  # Canada
    BR = "BR"  # Brazil
    MX = "MX"  # Mexico
    AR = "AR"  # Argentina
    CO = "CO"  # Colombia

    # Europe
    GB = "GB"  # United Kingdom
    DE = "DE"  # Germany
    FR = "FR"  # France
    IT = "IT"  # Italy
    ES = "ES"  # Spain
    NL = "NL"  # Netherlands
    CH = "CH"  # Switzerland
    SE = "SE"  # Sweden
    NO = "NO"  # Norway
    DK = "DK"  # Denmark

    # Asia Pacific
    IN = "IN"  # India
    CN = "CN"  # China
    JP = "JP"  # Japan
    HK = "HK"  # Hong Kong
    SG = "SG"  # Singapore
    AU = "AU"  # Australia
    KR = "KR"  # South Korea
    TW = "TW"  # Taiwan

    # Middle East & Africa
    SA = "SA"  # Saudi Arabia
    AE = "AE"  # United Arab Emirates
    ZA = "ZA"  # South Africa
    IL = "IL"  # Israel
    QA = "QA"  # Qatar


class RegionCode(str, Enum):
    """
    Broad geographic regions for grouping countries.
    Used for filtering and display in the terminal.
    """

    AMER = "AMER"   # Americas
    EMEA = "EMEA"   # Europe Middle East Africa
    APAC = "APAC"   # Asia Pacific
    GLOBAL = "GLOBAL"  # Cross-region data


# Maps every country to its region
# Used by the normalisation layer to auto-assign region
COUNTRY_TO_REGION: dict[CountryCode, RegionCode] = {
    # Americas
    CountryCode.US: RegionCode.AMER,
    CountryCode.CA: RegionCode.AMER,
    CountryCode.BR: RegionCode.AMER,
    CountryCode.MX: RegionCode.AMER,
    CountryCode.AR: RegionCode.AMER,
    CountryCode.CO: RegionCode.AMER,

    # Europe
    CountryCode.GB: RegionCode.EMEA,
    CountryCode.DE: RegionCode.EMEA,
    CountryCode.FR: RegionCode.EMEA,
    CountryCode.IT: RegionCode.EMEA,
    CountryCode.ES: RegionCode.EMEA,
    CountryCode.NL: RegionCode.EMEA,
    CountryCode.CH: RegionCode.EMEA,
    CountryCode.SE: RegionCode.EMEA,
    CountryCode.NO: RegionCode.EMEA,
    CountryCode.DK: RegionCode.EMEA,

    # Asia Pacific
    CountryCode.IN: RegionCode.APAC,
    CountryCode.CN: RegionCode.APAC,
    CountryCode.JP: RegionCode.APAC,
    CountryCode.HK: RegionCode.APAC,
    CountryCode.SG: RegionCode.APAC,
    CountryCode.AU: RegionCode.APAC,
    CountryCode.KR: RegionCode.APAC,
    CountryCode.TW: RegionCode.APAC,

    # Middle East & Africa
    CountryCode.SA: RegionCode.EMEA,
    CountryCode.AE: RegionCode.EMEA,
    CountryCode.ZA: RegionCode.EMEA,
    CountryCode.IL: RegionCode.EMEA,
    CountryCode.QA: RegionCode.EMEA,
}