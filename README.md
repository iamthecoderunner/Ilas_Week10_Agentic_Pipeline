# Ilas_Week10_Agentic_Pipeline


# Ilas Week 10 Agentic Pipeline

## Activity

**Week 10 Individual Activity:** Orchestrating Event-Driven Agentic Pipelines

This repository contains a simulation-only Event-Driven Agentic Deployment Pipeline implemented using Python and LangGraph `StateGraph`.

The solution uses exactly three specialized agents:

- Guard-Agent
- Infra-Agent
- Watchman-Agent

The workflow demonstrates:

- unit-test validation,
- Docker build simulation,
- database migration assessment,
- human-in-the-loop migration approval,
- simulated deployment,
- post-deployment monitoring,
- deterministic recovery evaluation,
- bounded rollback,
- rollback verification,
- and manual escalation when recovery cannot be verified as safe.

## Project Files

```text
activity_notes.md
prompt_v1.md
ai_output_v1.md
prompt_v2_correction.md
ai_output_v2_corrected.md
prompt_v3_code_generation.md
ai_output_v3_code_generation.md
agentic_pipeline.py
requirements.txt
FINAL_REPORT.md

Framework
- Python
- LangGraph
- StateGraph
- InMemorySaver
- interrupt()
- Command(resume=...)
Setup
Create and activate a virtual environment:
python -m venv .venv
source .venv/bin/activate

Install the required dependency:
python -m pip install -r requirements.txt

Run the Prototype
Successful Deployment
python agentic_pipeline.py --scenario success

When prompted, enter:
approve

Expected verified final state:
SUCCESS

Failed Unit Test
python agentic_pipeline.py --scenario test_fail

Expected verified final state:
FAILED

Rejected Migration Approval
python agentic_pipeline.py --scenario approval_reject

When prompted, enter:
reject

Expected verified final state:
FAILED

Docker Build Failure
python agentic_pipeline.py --scenario docker_fail

Expected verified final state:
FAILED

Post-Deployment Rollback
python agentic_pipeline.py --scenario rollback

When prompted, enter:
approve

Expected verified final state:
ROLLED_BACK

Migration Failure Requiring Manual Intervention
python agentic_pipeline.py --scenario migration_fail

When prompted, enter:
approve

Expected verified final state:
MANUAL_INTERVENTION_REQUIRED

Safety Scope
This prototype does not:
- build real Docker images,
- modify a real production database,
- call cloud deployment APIs,
- or interact with real production infrastructure.
All external operations are simulated deterministically for educational use.
Final Submission
See:
FINAL_REPORT.md

for the complete Week 10 activity submission, including:
- Deployment Workflow Blueprint
- Framework Orchestration Code
- Prompt Engineering & Correction Log
- Validation results