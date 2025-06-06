# Implementation Plan: Agentic LLM System for Product Review Triage

## 1. Overview
Build an agentic LLM system to process user reviews, classify them, and take automated actions:
- Bug reports: Check for duplicates, create GitHub issues if unique.
- Feature requests: Generate research plan, analyze competitors, create a research report, and send to Slack.
- Positive feedback/irrelevant: Classify and ignore.

## 2. Architecture & Design Patterns
- **Triage/Routing Agent:** Classifies input and routes to specialized agents.
- **Bug Handler Agent:** Checks for duplicate issues and creates new GitHub issues if needed.
- **Feature Research Agent:** Uses LLM-as-a-Planner to generate a research plan, analyze competitors, and produce a research report.
- **Human-in-the-Loop:** Sends research reports to Slack for human review/decision.
- **Toolformer/Function Tool:** All agent actions are exposed as function tools.
- **External API Integration via MCP:** All external actions (GitHub, Slack) use MCP-based agents.

## 3. Implementation Steps

### 3.1 Data Input
- Read reviews from `viber.csv`.

### 3.2 Triage Agent
- Use an LLM agent to classify each review as 'bug report', 'feature request', 'positive feedback', or 'irrelevant'.
- Route bug reports to the bug handler agent, feature requests to the feature research agent.

### 3.3 Bug Handler Agent
- For bug reports:
  - Format the report according to policy.
  - Check for duplicates using LLM comparison against existing GitHub issues.
  - If unique, create a new GitHub issue via MCP.
  - Output only status: "Status: Duplicate issue found" or "Status: New issue created at [URL]".

### 3.4 Feature Research Agent
- For feature requests:
  - Use LLM-as-a-Planner to generate a research plan.
  - Identify and select top competitors.
  - Generate a detailed research report (market analysis, user impact, technical feasibility, recommendations).
  - Save the report to `feature_research.md` (with clean timestamp only).
  - Send the report to Slack via MCP-based agent.
  - Output only status: success/failure for Slack message.

### 3.5 Positive Feedback/Irrelevant
- Output only the classification label.

## 4. Integration & Orchestration
- Use a main orchestrator to:
  - Read reviews.
  - Run triage agent and route to sub-agents.
  - Print only essential status messages.

## 5. Best Practices
- Use clear, minimal logging.
- Keep all agent logic modular and encapsulated.
- Use environment variables for all secrets.
- Use OpenAI Agents SDK and MCP for all external integrations.

## 6. Design Pattern Summary
- **Triage/Routing**: triage agent
- **LLM-as-a-Planner**: feature research agent
- **Human-in-the-Loop**: Slack integration
- **Toolformer/Function Tool**: all agent actions
- **External API via MCP**: GitHub, Slack

