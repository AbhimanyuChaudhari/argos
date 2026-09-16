from enum import Enum


class BillStatus(str, Enum):
    """
    Status of a legislative bill in the US Congress.
    Tracks the full lifecycle from introduction to law.
    """

    # Introduction
    INTRODUCED = "introduced"              # Bill first filed in chamber
    REFERRED_TO_COMMITTEE = "referred"     # Sent to relevant committee

    # Committee Stage
    IN_COMMITTEE = "in_committee"          # Under committee review
    COMMITTEE_HEARING = "committee_hearing"  # Public hearing scheduled
    COMMITTEE_MARKUP = "committee_markup"  # Committee amending the bill
    PASSED_COMMITTEE = "passed_committee"  # Committee approved it

    # Chamber Votes
    FLOOR_VOTE_SCHEDULED = "floor_scheduled"  # Vote date set
    PASSED_HOUSE = "passed_house"          # House of Representatives passed
    PASSED_SENATE = "passed_senate"        # Senate passed
    PASSED_BOTH_CHAMBERS = "passed_both"   # Both chambers passed

    # Reconciliation
    IN_CONFERENCE = "in_conference"        # Chambers reconciling differences
    CONFERENCE_REPORT = "conference_report"  # Reconciled version published

    # Presidential Action
    SENT_TO_PRESIDENT = "sent_to_president"  # Enrolled bill sent to White House
    SIGNED_INTO_LAW = "signed"             # President signed — now law
    VETOED = "vetoed"                      # President rejected
    VETO_OVERRIDDEN = "veto_overridden"    # Congress overrode veto — now law

    # Terminal States
    FAILED = "failed"                      # Did not pass
    WITHDRAWN = "withdrawn"                # Sponsor pulled the bill
    EXPIRED = "expired"                    # Congress ended without passing


class BillType(str, Enum):
    """
    Type of legislative instrument.
    Each has different procedural rules and effects.
    """

    HR = "hr"              # House Bill — originates in House
    S = "s"                # Senate Bill — originates in Senate
    HJRES = "hjres"        # House Joint Resolution — constitutional amendments
    SJRES = "sjres"        # Senate Joint Resolution
    HCONRES = "hconres"    # House Concurrent Resolution — non-binding
    SCONRES = "sconres"    # Senate Concurrent Resolution
    HRES = "hres"          # House Simple Resolution — internal House rules
    SRES = "sres"          # Senate Simple Resolution — internal Senate rules


class BillChamber(str, Enum):
    """
    Which chamber of Congress the bill is currently in.
    """

    HOUSE = "house"
    SENATE = "senate"
    JOINT = "joint"        # Joint session or conference
    PRESIDENT = "president"  # At presidential stage


class PolicyArea(str, Enum):
    """
    Policy domain of the bill.
    Maps to congressional committee jurisdictions.
    Critical for Argos — lets users filter bills
    by the sectors they affect financially.
    """

    ECONOMICS = "economics"              # Budget, taxes, fiscal policy
    FINANCE = "finance"                  # Banking, securities, insurance
    TRADE = "trade"                      # Import, export, tariffs
    ENERGY = "energy"                    # Oil, gas, renewables
    HEALTHCARE = "healthcare"            # Medicare, pharma, insurance
    TECHNOLOGY = "technology"            # AI, data, cybersecurity
    DEFENSE = "defense"                  # Military, weapons, contractors
    ENVIRONMENT = "environment"          # Climate, EPA, emissions
    INFRASTRUCTURE = "infrastructure"    # Roads, broadband, utilities
    AGRICULTURE = "agriculture"          # Farm policy, food, commodities
    HOUSING = "housing"                  # Real estate, mortgages, HUD
    LABOR = "labor"                      # Employment, wages, unions
    IMMIGRATION = "immigration"          # Visas, border, citizenship
    FOREIGN_POLICY = "foreign_policy"    # Sanctions, treaties, diplomacy
    OTHER = "other"                      # Catch-all