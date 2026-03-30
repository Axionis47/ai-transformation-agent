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
    CompanyBundle(
        "Clearview Financial",
        "financial_services",
        "100-200",
        "Manual compliance review process for regulatory changes, slow turnaround",
    ),
    CompanyBundle(
        "Pinnacle Wealth Advisors",
        "financial_services",
        "50-100",
        "Client onboarding takes 2 weeks due to manual document verification",
    ),
    CompanyBundle(
        "Summit Credit Union",
        "financial_services",
        "200-500",
        "High volume of member inquiries; support team overwhelmed during peak periods",
    ),
    CompanyBundle(
        "Ironbridge Capital",
        "financial_services",
        "500-2000",
        "Fraud detection relies on rule-based system with high false-positive rate",
    ),
    CompanyBundle(
        "Harbor Insurance Group",
        "financial_services",
        "200-500",
        "Claims processing is paper-heavy; adjusters spend 60% of time on data entry",
    ),
    CompanyBundle(
        "Meridian Health Partners",
        "healthcare",
        "200-500",
        "Regional clinic network with high no-show rates affecting revenue",
    ),
    CompanyBundle(
        "CarePlus Home Health",
        "healthcare",
        "100-200",
        "Scheduling home visits manually; coordinators unable to optimise routes",
    ),
    CompanyBundle(
        "Northgate Medical Center",
        "healthcare",
        "500-2000",
        "Prior authorisation requests take 3-5 days; denials run at 20%",
    ),
    CompanyBundle(
        "Sunrise Behavioral Health",
        "healthcare",
        "50-100",
        "Clinician documentation takes 2 hours per day, reducing patient capacity",
    ),
    CompanyBundle(
        "Alliance Diagnostics Lab",
        "healthcare",
        "100-200",
        "Lab report distribution is fax-based; results take 24h to reach ordering physicians",
    ),
]

# --- logistics (4) + manufacturing (4) + professional_services (4) + retail + unseen (3) ---
_BUNDLES_PART2: list[CompanyBundle] = [
    CompanyBundle(
        "Apex Logistics Solutions",
        "logistics",
        "500-2000",
        "Fleet management and dispatch coordination challenges; high fuel costs",
    ),
    CompanyBundle(
        "Coastal Freight Partners",
        "logistics",
        "200-500",
        "Last-mile delivery success rate is 82%; customer complaints about missed windows",
    ),
    CompanyBundle(
        "Inland Express Carriers",
        "logistics",
        "100-200",
        "Driver scheduling done via spreadsheet; frequent overtime and compliance issues",
    ),
    CompanyBundle(
        "PrimeShip Distribution",
        "logistics",
        "500-2000",
        "Warehouse pick-and-pack error rate at 3%; high returns processing cost",
    ),
    CompanyBundle(
        "Steelbridge Manufacturing",
        "manufacturing",
        "200-500",
        "CNC equipment with frequent unplanned downtime; maintenance is reactive",
    ),
    CompanyBundle(
        "Keystone Plastics",
        "manufacturing",
        "100-200",
        "Quality inspection is manual; defect detection happens late in production line",
    ),
    CompanyBundle(
        "Atlas Industrial Components",
        "manufacturing",
        "500-2000",
        "Demand forecasting accuracy is poor; overstock and stockouts both common",
    ),
    CompanyBundle(
        "Redstone Fabrication",
        "manufacturing",
        "50-100",
        "Custom order quoting takes 3 days; sales team losing deals to faster competitors",
    ),
    CompanyBundle(
        "Vantage Consulting Group",
        "professional_services",
        "100-200",
        "Proposal writing takes 15 hours per engagement; inconsistent win rate",
    ),
    CompanyBundle(
        "Meridian Law Partners",
        "professional_services",
        "50-100",
        "Contract review is manual; associates spend 40% of billable time on document analysis",
    ),
    CompanyBundle(
        "Clarity HR Solutions",
        "professional_services",
        "200-500",
        "Employee onboarding is fragmented across 6 systems; new hires report low satisfaction",
    ),
    CompanyBundle(
        "Bluepoint Accounting",
        "professional_services",
        "50-100",
        "Month-end close takes 10 days; manual reconciliation across multiple ERP exports",
    ),
    CompanyBundle(
        "RetailEdge Group",
        "retail",
        "500-2000",
        "Multi-location inventory management with shrinkage and stockout issues",
    ),
    CompanyBundle(
        "Brightfield Academy",
        "education",
        "200-500",
        "Student retention is 70%; advisors struggle to identify at-risk students early",
    ),
    CompanyBundle(
        "Cornerstone Real Estate",
        "real_estate",
        "100-200",
        "Lead qualification is manual; agents spend 30% of time on low-probability prospects",
    ),
]

BUNDLES: list[CompanyBundle] = _BUNDLES_PART1 + _BUNDLES_PART2


def get_bundles() -> list[CompanyBundle]:
    """Return all 25 company bundles."""
    return list(BUNDLES)
