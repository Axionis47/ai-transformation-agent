from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OpportunityTemplate:
    template_id: str
    name: str
    description: str
    solution_shape: str        # automation | copilot | decision_support
    workflow_area: str          # support | finance_ops | operations | rev_ops
    win_signals: list[str]      # keywords in evidence that suggest this applies
    anti_signals: list[str]     # keywords that suggest it does not apply
    roi_drivers: list[str]      # what drives ROI for this pattern
    typical_timeline_weeks: int
    applicable_industries: list[str]
    engagement_ids: list[str]   # linked seed engagements


def get_templates() -> list[OpportunityTemplate]:
    return [
        OpportunityTemplate(
            template_id="tpl-support-auto",
            name="Customer Support Automation",
            description=(
                "Automate repetitive customer support tasks: ticket triage, routing, "
                "deflection of routine inquiries via chatbot, and resolution of common issues."
            ),
            solution_shape="automation",
            workflow_area="support",
            win_signals=[
                "support", "triage", "ticket", "routing", "chatbot",
                "customer service", "deflection", "contact centre", "help desk",
            ],
            anti_signals=["no customer interaction", "b2b only", "no inbound requests"],
            roi_drivers=["ticket_volume", "agent_headcount", "resolution_time"],
            typical_timeline_weeks=8,
            applicable_industries=["financial_services", "retail", "healthcare"],
            engagement_ids=["eng-001", "eng-011"],
        ),
        OpportunityTemplate(
            template_id="tpl-finance-auto",
            name="Financial Process Automation",
            description=(
                "Automate high-volume, rule-based financial workflows: claims processing, "
                "invoice handling, accounts payable, time tracking, and billing reconciliation."
            ),
            solution_shape="automation",
            workflow_area="finance_ops",
            win_signals=[
                "claims", "invoice", "billing", "accounts payable", "time tracking",
                "payroll", "finance", "reconciliation", "accounts receivable",
            ],
            anti_signals=["no financial operations", "cash-only", "no billing system"],
            roi_drivers=["transaction_volume", "error_cost", "finance_headcount"],
            typical_timeline_weeks=11,
            applicable_industries=["healthcare", "logistics", "professional_services"],
            engagement_ids=["eng-005", "eng-008", "eng-016"],
        ),
        OpportunityTemplate(
            template_id="tpl-ops-auto",
            name="Operations Automation",
            description=(
                "Automate operational workflows: scheduling, quality inspection, inventory, "
                "loss prevention, and repetitive back-office operations tasks."
            ),
            solution_shape="automation",
            workflow_area="operations",
            win_signals=[
                "scheduling", "quality", "inspection", "inventory", "shrinkage",
                "defect", "operations", "appointment", "workflow",
            ],
            anti_signals=["no physical operations", "fully manual preferred", "no volume"],
            roi_drivers=["throughput", "error_rate", "operations_headcount"],
            typical_timeline_weeks=13,
            applicable_industries=["healthcare", "manufacturing", "retail"],
            engagement_ids=["eng-004", "eng-012", "eng-018"],
        ),
        OpportunityTemplate(
            template_id="tpl-fraud-copilot",
            name="Risk and Fraud Analysis Copilot",
            description=(
                "Augment analyst workflows with AI-assisted risk scoring and fraud detection, "
                "reducing false positives and freeing analysts for complex decisions."
            ),
            solution_shape="copilot",
            workflow_area="finance_ops",
            win_signals=[
                "fraud", "risk", "compliance", "alert", "flagged", "suspicious",
                "false positive", "transaction review", "anomaly",
            ],
            anti_signals=["no financial risk", "no transaction monitoring", "no analyst team"],
            roi_drivers=["analyst_headcount", "fraud_loss_rate", "transaction_volume"],
            typical_timeline_weeks=12,
            applicable_industries=["financial_services"],
            engagement_ids=["eng-002"],
        ),
        OpportunityTemplate(
            template_id="tpl-docs-copilot",
            name="Documentation and Content Copilot",
            description=(
                "Assist knowledge workers in creating documentation, proposals, clinical notes, "
                "and reports faster with AI-generated drafts and context retrieval."
            ),
            solution_shape="copilot",
            workflow_area="operations",
            win_signals=[
                "documentation", "proposal", "report", "content", "writing",
                "clinical notes", "notes", "drafting", "document creation",
            ],
            anti_signals=["no document creation", "no written output required"],
            roi_drivers=["knowledge_worker_time", "document_volume", "win_rate"],
            typical_timeline_weeks=10,
            applicable_industries=["healthcare", "professional_services"],
            engagement_ids=["eng-006", "eng-015"],
        ),
        OpportunityTemplate(
            template_id="tpl-predictive-ops",
            name="Predictive Analytics",
            description=(
                "Apply predictive models to forecast demand, detect maintenance needs early, "
                "and reduce unplanned downtime using historical operational data."
            ),
            solution_shape="decision_support",
            workflow_area="operations",
            win_signals=[
                "predictive", "forecast", "maintenance", "demand", "trend",
                "prediction", "sensor", "breakdown", "downtime", "iot",
            ],
            anti_signals=["no historical data", "no sensors", "less than 6 months data"],
            roi_drivers=["downtime_cost", "forecast_accuracy", "maintenance_cost"],
            typical_timeline_weeks=12,
            applicable_industries=["logistics", "manufacturing", "retail"],
            engagement_ids=["eng-009", "eng-010", "eng-013"],
        ),
        OpportunityTemplate(
            template_id="tpl-compliance",
            name="Compliance and Document Review",
            description=(
                "Accelerate regulatory document review, policy change monitoring, and "
                "compliance reporting using AI to flag changes and summarise obligations."
            ),
            solution_shape="decision_support",
            workflow_area="finance_ops",
            win_signals=[
                "compliance", "regulatory", "audit", "policy", "review",
                "regulation", "legal", "governance", "sox", "gdpr",
            ],
            anti_signals=["no regulatory requirements", "exempt from regulation"],
            roi_drivers=["compliance_risk", "fte_cost", "review_frequency"],
            typical_timeline_weeks=10,
            applicable_industries=["financial_services", "healthcare"],
            engagement_ids=["eng-003"],
        ),
        OpportunityTemplate(
            template_id="tpl-resource-opt",
            name="Resource and Dispatch Optimization",
            description=(
                "Optimise resource allocation, dispatch routing, and staffing decisions "
                "using AI recommendations to reduce waste and improve utilisation."
            ),
            solution_shape="decision_support",
            workflow_area="operations",
            win_signals=[
                "resource", "dispatch", "allocation", "staffing", "routing",
                "supplier", "scheduling", "utilization", "fleet", "workforce",
            ],
            anti_signals=["no resource constraints", "fully automated already", "no dispatch"],
            roi_drivers=["utilization_rate", "fuel_cost", "overtime_cost"],
            typical_timeline_weeks=10,
            applicable_industries=["logistics", "manufacturing", "professional_services"],
            engagement_ids=["eng-007", "eng-014", "eng-017"],
        ),
    ]
