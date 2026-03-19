// TODO: Replace with GET /v1/solutions when backend endpoint is available.
// Data sourced from tests/fixtures/rag_seeds/victories.json (Library A -- Tenex delivered solutions).
// Only active records with the fields needed by SolutionCard are included here.

import type { SolutionRecord } from "@/components/SolutionCard";

export const SOLUTIONS: SolutionRecord[] = [
  {
    id: "win-001",
    engagement_title: "Route Optimization for Regional LTL Carrier",
    industry: "logistics",
    company_profile: { size_label: "mid-market" },
    results: { primary_metric: { label: "Fuel Cost Reduction", value: "14%" } },
    solution_category: "predictive_model",
    engagement_details: { duration_months: 4 },
    maturity_at_engagement: "Developing",
  },
  {
    id: "win-002",
    engagement_title: "Carrier Scoring for B2B Supply Chain SaaS",
    industry: "logistics",
    company_profile: { size_label: "startup" },
    results: {
      primary_metric: {
        label: "Per-shipment carrier cost savings",
        value: "12% average reduction",
      },
    },
    solution_category: "scoring_model",
    engagement_details: { duration_months: 3 },
    maturity_at_engagement: "Developing",
  },
  {
    id: "win-003",
    engagement_title: "Shipment Delay Prediction for Cold Chain Distributor",
    industry: "logistics",
    company_profile: { size_label: "mid-market" },
    results: {
      primary_metric: {
        label: "Reduction in late deliveries",
        value: "63% fewer late deliveries",
      },
    },
    solution_category: "classification",
    engagement_details: { duration_months: 5 },
    maturity_at_engagement: "Developing",
  },
  {
    id: "win-004",
    engagement_title: "Fraud Detection for Mid-Market Payment Processor",
    industry: "financial_services",
    company_profile: { size_label: "mid-market" },
    results: {
      primary_metric: {
        label: "Fraud caught rate",
        value: "31% more fraud intercepted",
      },
    },
    solution_category: "classification",
    engagement_details: { duration_months: 4 },
    maturity_at_engagement: "Developing",
  },
  {
    id: "win-005",
    engagement_title: "Credit Risk Scoring for Regional Business Lender",
    industry: "financial_services",
    company_profile: { size_label: "mid-market" },
    results: {
      primary_metric: {
        label: "Default rate reduction",
        value: "22% reduction in default rate",
      },
    },
    solution_category: "classification",
    engagement_details: { duration_months: 6 },
    maturity_at_engagement: "Developing",
  },
  {
    id: "win-006",
    engagement_title: "AML Transaction Monitoring for Community Bank",
    industry: "financial_services",
    company_profile: { size_label: "mid-market" },
    results: {
      primary_metric: {
        label: "False positive alert reduction",
        value: "68% reduction in analyst-reviewed alerts",
      },
    },
    solution_category: "classification",
    engagement_details: { duration_months: 5 },
    maturity_at_engagement: "Developing",
  },
  {
    id: "win-007",
    engagement_title: "Clinical Triage NLP for Urgent Care Network",
    industry: "healthcare",
    company_profile: { size_label: "mid-market" },
    results: {
      primary_metric: {
        label: "Reduction in average wait time to triage assignment",
        value: "35% reduction",
      },
    },
    solution_category: "nlp",
    engagement_details: { duration_months: 6 },
    maturity_at_engagement: "Developing",
  },
  {
    id: "win-008",
    engagement_title: "Readmission Risk Prediction for Regional Health System",
    industry: "healthcare",
    company_profile: { size_label: "enterprise" },
    results: {
      primary_metric: {
        label: "30-day readmission rate reduction",
        value: "19% relative reduction",
      },
    },
    solution_category: "predictive_model",
    engagement_details: { duration_months: 8 },
    maturity_at_engagement: "Developing",
  },
];
