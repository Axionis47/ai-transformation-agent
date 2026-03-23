"""25 synthetic company bundles for evaluation across 6+ industries."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CompanyBundle:
    company_name: str
    industry: str
    employee_count_band: str
    notes: str


# --- financial_services (5) + healthcare (5) ---
_BUNDLES_PART1: list[CompanyBundle] = [
    CompanyBundle("Clearview Financial", "financial_services", "100-200",
                  "Manual compliance review process for regulatory changes, slow turnaround"),
    CompanyBundle("Pinnacle Wealth Advisors", "financial_services", "50-100",
                  "Client onboarding takes 2 weeks due to manual document verification"),
    CompanyBundle("Summit Credit Union", "financial_services", "200-500",
                  "High volume of member inquiries; support team overwhelmed during peak periods"),
    CompanyBundle("Ironbridge Capital", "financial_services", "500-2000",
                  "Fraud detection relies on rule-based system with high false-positive rate"),
    CompanyBundle("Harbor Insurance Group", "financial_services", "200-500",
                  "Claims processing is paper-heavy; adjusters spend 60% of time on data entry"),
    CompanyBundle("Meridian Health Partners", "healthcare", "200-500",
                  "Regional clinic network with high no-show rates affecting revenue"),
    CompanyBundle("CarePlus Home Health", "healthcare", "100-200",
                  "Scheduling home visits manually; coordinators unable to optimise routes"),
    CompanyBundle("Northgate Medical Center", "healthcare", "500-2000",
                  "Prior authorisation requests take 3-5 days; denials run at 20%"),
    CompanyBundle("Sunrise Behavioral Health", "healthcare", "50-100",
                  "Clinician documentation takes 2 hours per day, reducing patient capacity"),
    CompanyBundle("Alliance Diagnostics Lab", "healthcare", "100-200",
                  "Lab report distribution is fax-based; results take 24h to reach ordering physicians"),
]
