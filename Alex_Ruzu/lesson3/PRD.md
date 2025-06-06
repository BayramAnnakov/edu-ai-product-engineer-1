# Product Requirements Document (PRD): Agentic LLM System for Product Review Triage

## 1. Problem Statement
Product teams receive large volumes of user reviews. Manually triaging, classifying, and acting on this feedback is slow, error-prone, and limits responsiveness to user needs.

## 2. Goals
- Automate the classification and handling of user reviews.
- Instantly create actionable bug reports in GitHub.
- Generate and deliver high-quality feature research reports to product teams via Slack.
- Minimize manual effort and reduce duplicate work.

## 3. User Stories
- **As a product manager**, I want bug reports from users to be automatically checked for duplicates and filed in GitHub, so I can focus on new and unique issues.
- **As a product manager**, I want feature requests to be researched, compared with competitors, and delivered as a structured report in Slack, so I can make informed roadmap decisions.
- **As a team**, we want positive feedback and irrelevant reviews to be filtered out, so we can focus on actionable items.

## 4. Workflow Overview
1. **Input:** System ingests user reviews from `viber.csv`.
2. **Triage:** LLM agent classifies each review as a bug report, feature request, positive feedback, or irrelevant.
3. **Bug Handling:**
    - For bug reports, check for duplicates in GitHub Issues.
    - If unique, create a new issue using a strict bug report policy.
    - Output only status: "Status: Duplicate issue found" or "Status: New issue created at [URL]".
4. **Feature Research:**
    - For feature requests, use LLM-as-a-Planner to generate a research plan.
    - Identify and select top competitors.
    - Generate a detailed research report (market analysis, user impact, technical feasibility, recommendations).
    - Save the report to `feature_research.md` (with clean timestamp only).
    - Send the report to Slack via MCP-based agent.
    - Output only status: success/failure for Slack message.
5. **Other:**
    - For positive feedback/irrelevant, output only the classification label.

## 5. Agent Responsibilities
- **Triage Agent:** Classifies and routes reviews to the correct sub-agent.
- **Bug Handler Agent:** Formats, deduplicates, and files bug reports in GitHub.
- **Feature Research Agent:** Plans, researches, and delivers feature research to Slack.

## 6. Design Patterns Used
- **Triage/Routing:** Triage agent classifies and routes input.
- **LLM-as-a-Planner:** Feature research agent generates a research plan before execution.
- **Human-in-the-Loop:** Slack delivery enables human review and decision-making.
- **Toolformer/Function Tool:** All agent actions are exposed as function tools.
- **External API via MCP:** All external actions (GitHub, Slack) use MCP-based agents.

## 7. Success Criteria
- All bug reports are checked for duplicates and only unique issues are filed.
- All feature requests result in a research report delivered to Slack.
- No manual triage or duplicate bug filing is required.
- All actions are logged with clear, minimal status messages.

## 8. Out of Scope
- Manual review of positive feedback or irrelevant reviews.
- Any workflow not using MCP-based integrations.

