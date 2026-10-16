# 1. requirements.txt contents

```
langgraph>=1.0,<2.0
```

Download the dependency file:

requirements.txt

# 2. agentic_pipeline.py

I've created the complete Python prototype as a single file, ready to add to your GitHub Codespaces project.

agentic_pipeline.py

Python 3 · LangGraph StateGraph · Approximately 14 KB

Download the complete agentic_pipeline.py

The file contains the full `TypedDict` shared state, all three specialized agent nodes, eight deterministic simulation tool functions, conditional routing, a real LangGraph human approval interrupt, recovery evaluation, rollback execution and verification, and five terminal states.

It uses `StateGraph`, `InMemorySaver`, `interrupt()`, and `Command(resume=...)`, following LangGraph's documented graph and human-in-the-loop APIs.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://reference.langchain.com\&sz=32)

LangChain Reference

+2



Safety: The prototype does not execute real unit tests, build real Docker images, modify databases, or deploy containers. All external operations are simulated.

Validation status: The Python file passed a syntax compilation check. Full LangGraph execution testing could not be completed in this environment because the dependency installation was blocked by network access. The scenario results below are expected paths, not observed execution results.

# 3. Concise explanation of each graph node

| Graph node             | Responsibility                                                          |
| ---------------------- | ----------------------------------------------------------------------- |
| `Guard-Agent`          | Runs simulated unit tests and blocks progression on failure             |
| `Infra-Agent`          | Receives validated test clearance and begins infrastructure preparation |
| `DEPENDENCIES`         | Simulates dependency building                                           |
| `DOCKER_BUILD`         | Simulates image creation and records an image identifier                |
| `MIGRATION_ASSESSMENT` | Evaluates the proposed migration                                        |
| `HUMAN_APPROVAL`       | Pauses graph execution until the console user approves or rejects       |
| `MIGRATION_EXECUTING`  | Simulates the approved migration                                        |
| `DEPLOYING`            | Simulates container deployment                                          |
| `Watchman-Agent`       | Reads simulated HTTP error metrics and evaluates the threshold          |
| `RECOVERY_EVALUATION`  | Determines whether to fail, roll back, or escalate                      |
| `ROLLBACK_EXECUTING`   | Performs at most one simulated rollback                                 |
| `ROLLBACK_VERIFYING`   | Checks whether recovery succeeded                                       |

The five terminal nodes are `SUCCESS`, `FAILED`, `ROLLED_BACK`, `ROLLBACK_FAILED`, and `MANUAL_INTERVENTION_REQUIRED`. Every terminal node connects directly to LangGraph's `END`.

The supporting graph nodes are deterministic workflow operations, not additional autonomous agents.

# 4. Exact terminal commands to install dependencies and run the prototype

In GitHub Codespaces, upload both files into the same project directory.

Open the Codespaces terminal and execute:

Step 1 — Create and activate a Python virtual environment

```
python -m venv .venv
source .venv/bin/activate
```

Step 2 — Install dependencies

```
python -m pip install -r requirements.txt
```

Step 3 — Execute the successful deployment scenario

```
python agentic_pipeline.py --scenario success
```

The workflow should stop at the approval gate and display:

```
WORKFLOW PAUSED: HUMAN_APPROVAL
Type approve or reject:
```

Enter:

```
approve
```

This resumes the graph through the migration, deployment, and monitoring stages.

The expected terminal state is `SUCCESS`, assuming the simulation executes as designed.

# 5. Example scenario inputs

Use the following scenario commands to test the required paths.

| Scenario                    | Terminal command                                        | Expected terminal state        |
| --------------------------- | ------------------------------------------------------- | ------------------------------ |
| Successful deployment       | `python agentic_pipeline.py --scenario success`         | `SUCCESS` after approval       |
| Failed unit test            | `python agentic_pipeline.py --scenario test_fail`       | `FAILED`                       |
| Rejected migration approval | `python agentic_pipeline.py --scenario approval_reject` | `FAILED` after typing `reject` |
| Docker build failure        | `python agentic_pipeline.py --scenario docker_fail`     | `FAILED`                       |
| Post-deployment rollback    | `python agentic_pipeline.py --scenario rollback`        | `ROLLED_BACK` after approval   |

For the rollback scenario, type `approve` when prompted. The simulated Watchman-Agent will then receive an 8% HTTP error rate, exceeding the configured 5% threshold, and route through recovery evaluation, rollback execution, and rollback verification.

### Additional recovery test scenarios

The prototype also supports these tests for validating the corrected architecture:

```
# Migration failure requiring manual intervention
python agentic_pipeline.py --scenario migration_fail

# Deployment failure followed by recovery evaluation
python agentic_pipeline.py --scenario deployment_fail

# Simulated rollback operation failure
python agentic_pipeline.py --scenario rollback_fail

# Rollback completes but verification fails
python agentic_pipeline.py --scenario rollback_unverified

# Database incompatibility blocks automatic recovery
python agentic_pipeline.py --scenario incompatible_db

# Unknown migration outcome triggers escalation
python agentic_pipeline.py --scenario migration_unknown
```

These scenarios require approval before reaching the simulated production migration.

For this Week 10 activity, the implementation demonstrates the central architectural requirement: three specialized agents coordinated through deterministic LangGraph routing, a mandatory human approval pause, and a bounded recovery state machine without automatic infinite retries.

The checkpoint is in memory, so the approval pause works within the running program; it is not designed to survive a Codespaces process restart.