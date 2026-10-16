# Week 10 Individual Activity
## Orchestrating Event-Driven Agentic Pipelines

**Student:** Gio Malcolm P. Ilas  
**Course:** Applied Generative AI for IT Solution Development  

---

# 1. Deployment Workflow Blueprint

## 1.1 Manual Production Deployment Baseline

The original production deployment workflow follows this manual sequence:

```text
[Code Push]
    |
    v
[Run Unit Tests]
    |
    v
[Build Docker Image]
    |
    v
[DB Migration]
    |
    v
[Monitor Logs]

The process relies on engineers to manually move the deployment from one stage to the next. This creates delays during testing, build execution, database migration, and post-deployment monitoring.
1.2 Human Intervention and Delay Points
Deployment Stage	Human Intervention	Data / Variable Passed Forward	Possible Failure
Code Push	Developer pushes the code	Commit hash / source revision	Wrong or incomplete code pushed
Run Unit Tests	Engineer starts and reviews the tests	Test result, pass/fail status, commit hash	Unit test failure or incorrect interpretation of results
Build Docker Image	Engineer manually starts the build	Build result, image/tag, commit reference	Build or dependency failure
DB Migration	Engineer manually applies the migration	Migration version, migration result, deployment context	Failed, partial, or unsafe database migration
Monitor Logs	Engineer observes runtime logs	Runtime logs and HTTP error information	Errors may be detected late or overlooked


The main human delay points are:
1. Manual review of unit-test results before the deployment can continue.
2. Manual initiation of the Docker build and deployment process.
3. Human validation before database migration is applied to production.
4. Manual observation of logs after deployment.
5. Delayed reaction when a production problem requires recovery or rollback.
1.3 Data and State Transitions
The manual deployment process was decomposed into discrete operational states so that the workflow can later be controlled by an event-driven state machine.
CODE_PUSHED
    |
    v
TESTING
    |
    +--> TEST_PASSED
    |
    +--> TEST_FAILED

TEST_PASSED
    |
    v
BUILDING_IMAGE
    |
    +--> BUILD_SUCCEEDED
    |
    +--> BUILD_FAILED

BUILD_SUCCEEDED
    |
    v
AWAITING_MIGRATION
    |
    +--> MIGRATION_SUCCEEDED
    |
    +--> MIGRATION_FAILED

MIGRATION_SUCCEEDED
    |
    v
MONITORING
    |
    +--> HEALTHY
    |
    +--> ROLLBACK_REQUIRED

These state names are working implementation labels created for the prototype and are not prescribed state names from the activity sheet.
The main state information passed through the workflow includes:
- workflow identifier
- commit SHA
- test status
- dependency status
- Docker build status
- Docker image digest
- migration risk
- migration status
- human approval status
- deployment status
- monitoring status
- HTTP error rate
- previous healthy deployment version
- database compatibility
- recovery status
- rollback attempt count
1.4 Event-Driven Agentic Pipeline
The manual process was redesigned into an event-driven agentic pipeline using exactly three specialized agents:
- Guard-Agent
- Infra-Agent
- Watchman-Agent
The overall agentic workflow is:
Code Push / Webhook
        |
        v
   Guard-Agent
   Run Unit Tests
        |
   +----+----+
   |         |
 PASS       FAIL
   |         |
   v         v
Infra-Agent FAILED
   |
Build Dependencies
   |
Build Docker Image
   |
Migration Assessment
   |
   v
HUMAN APPROVAL GATE
   |
+--+--+
|     |
APPROVE REJECT
|       |
v       v
DB Migration
        FAILED
   |
Deploy Container
   |
   v
Watchman-Agent
   |
Monitor Logs / HTTP Errors
   |
+--+----------------+
|                   |
HEALTHY          FAILURE /
|                THRESHOLD BREACH
v                   |
SUCCESS             v
             RECOVERY_EVALUATION
                    |
          +---------+----------+
          |         |          |
       FAILED   ROLLBACK    MANUAL
                  |        INTERVENTION
                  v
          ROLLBACK_EXECUTING
                  |
                  v
          ROLLBACK_VERIFYING
                  |
             +----+----+
             |         |
          VERIFIED   FAILED
             |         |
             v         v
         ROLLED_BACK  ROLLBACK_FAILED

The workflow is event-driven because each stage activates based on a verified event or workflow state instead of requiring an engineer to manually trigger every next step.
The workflow orchestrator controls the state transitions but is not considered a fourth autonomous agent.
1.5 Agent Responsibilities
Guard-Agent
The Guard-Agent acts as the quality-control entry point of the pipeline.
Its responsibilities are to:
- receive the code push or webhook event,
- trigger the unit-test process,
- capture and evaluate test results,
- determine whether testing passed or failed,
- prevent the deployment workflow from continuing when testing fails.
The Guard-Agent passes the validated commit and test result forward only when the test status is verified as successful.
A failed unit test terminates the workflow before the Infra-Agent is allowed to continue.
Infra-Agent
The Infra-Agent handles infrastructure preparation and deployment execution.
Its responsibilities are to:
- receive the successful Guard-Agent handoff,
- prepare or build application dependencies,
- build the Docker image,
- assess the database migration,
- request human approval before production migration,
- apply an approved database migration,
- deploy the container,
- pass deployment information to the Watchman-Agent.
The Infra-Agent cannot continue when:
- Guard-Agent validation failed,
- dependency preparation failed,
- Docker image creation failed,
- migration assessment is unsafe,
- human approval is rejected,
- or the migration itself fails.
Watchman-Agent
The Watchman-Agent performs post-deployment monitoring.
Its responsibilities are to:
- receive the successful deployment state,
- monitor runtime information,
- monitor HTTP error rates,
- identify unhealthy conditions,
- determine whether the new deployment remains healthy,
- initiate recovery evaluation when a defined failure threshold is exceeded.
A healthy deployment completes the workflow in the SUCCESS state.
An unhealthy deployment routes to RECOVERY_EVALUATION.
1.6 Human-in-the-Loop Migration Gate
A mandatory human-in-the-loop approval gate is positioned after database migration assessment and before any production migration is executed.
MIGRATION_ASSESSMENT
        |
        v
APPROVAL_PENDING
        |
     +--+--+
     |     |
 APPROVE  REJECT
     |     |
     v     v
MIGRATION_EXECUTING
           FAILED

The human approval gate is treated as a hard execution barrier.
The workflow cannot automatically execute the production database migration without explicit approval.
The approval decision applies to the migration being reviewed.
If the migration is rejected, the workflow terminates safely before production database changes are applied.
This design keeps a human engineer involved in the highest-risk production database step while still automating the surrounding deployment process.
1.7 Failure and Rollback Routing
The first AI-generated architecture contained a structural weakness in the recovery path.
The state RECOVERY_EVALUATION was introduced, but its outgoing transitions were not fully defined. Migration failures and deployment failures could enter this state, but the architecture did not completely specify how the workflow should leave it.
The architecture was corrected so that RECOVERY_EVALUATION became a deterministic decision state.
It now evaluates:
- whether production was actually changed,
- whether the production state is known,
- whether a previous healthy deployment exists,
- whether the previous deployment artifact is available and verified,
- whether the current database remains compatible with the previous application version,
- whether the proposed recovery method is safe,
- whether the recovery operation is authorized,
- whether an automatic rollback has already been attempted.
The corrected recovery routing is:
RECOVERY_EVALUATION
        |
        +--> Production verified unchanged
        |        |
        |        v
        |      FAILED
        |
        +--> Recovery safety cannot be verified
        |        |
        |        v
        |   MANUAL_INTERVENTION_REQUIRED
        |
        +--> Recovery verified safe and authorized
                 |
                 v
          ROLLBACK_EXECUTING
                 |
            +----+----+
            |         |
         SUCCESS    FAILURE
            |         |
            v         v
   ROLLBACK_VERIFYING
                      |
                      v
               ROLLBACK_FAILED

ROLLBACK_VERIFYING
        |
    +---+---+
    |       |
 VERIFIED  FAILED /
    |      UNVERIFIED
    v       |
ROLLED_BACK v
       ROLLBACK_FAILED

Automatic rollback is permitted only when all required recovery conditions are verified.
The prototype allows a maximum of one automatic rollback attempt.
A failed or uncertain rollback is not retried automatically.
Database migration recovery is treated differently from application or container rollback because restoring a previous Docker image does not automatically restore the previous database state.
When recovery safety, database compatibility, rollback artifacts, or authorization cannot be verified, the system stops in:
MANUAL_INTERVENTION_REQUIRED
This prevents an uncertain production condition from triggering an unsafe automatic recovery operation.
The corrected architecture therefore guarantees that every recovery path reaches a defined outcome:
- FAILED
- SUCCESS
- ROLLED_BACK
- ROLLBACK_FAILED
- MANUAL_INTERVENTION_REQUIRED
No terminal state automatically restarts the deployment pipeline. A corrected release requires a new workflow execution.

---

# 2. Framework Orchestration Code

## 2.1 Framework Selection

The prototype was implemented using:

- Python
- LangGraph
- `StateGraph`
- `TypedDict` for shared workflow state
- `InMemorySaver` for graph checkpointing
- `interrupt()` for the human-in-the-loop approval gate
- `Command(resume=...)` to resume the workflow after human input

The implementation is intentionally simulation-only.

It does not:

- execute real Docker builds,
- modify a real database,
- deploy to a cloud platform,
- call production infrastructure,
- or perform real Large Language Model API calls.

This makes the prototype safe to execute in GitHub Codespaces while still demonstrating the required agentic orchestration logic.

The complete generated implementation is stored in:

`agentic_pipeline.py`

The required Python dependency is stored in:

`requirements.txt`

The dependency specification used was:

```text
langgraph>=1.0,<2.0

2.2 Shared Workflow State
The LangGraph pipeline uses a shared WorkflowState implemented as a Python TypedDict.
The main state fields include:
class WorkflowState(TypedDict):    workflow_id: str    scenario: str    current_state: str    commit_sha: str    test_status: str    dependency_status: str    docker_status: str    image_digest: str | None    migration_risk: str    migration_status: str    approval_status: str    deployment_status: str    monitoring_status: str    http_error_rate: float | None    production_changed: bool | None    previous_version: str | None    previous_image_digest: str | None    previous_version_verified: bool    database_compatible: bool | None    recovery_safe: bool    recovery_authorized: bool    rollback_attempt_count: int    rollback_status: str    recovery_reason: str    recovery_target: str    events: list[str]


This shared state serves as the data carrier between graph nodes.
It allows each stage to inspect the result of previous operations before deciding whether the workflow may proceed.
Examples include:
- Guard-Agent writes test_status.
- Docker build writes docker_status and image_digest.
- Human approval writes approval_status.
- Watchman-Agent writes monitoring_status and http_error_rate.
- Recovery evaluation reads production and recovery information before selecting a recovery route.
- Rollback execution updates rollback_attempt_count.
2.3 Agent Tools
The three specialized agents use deterministic tool functions.
These tools simulate real infrastructure operations without modifying an actual production environment.
Unit Test Tool
def run_unit_tests(state: WorkflowState) -> bool:    return state["scenario"] != "test_fail"


This allows the Guard-Agent to simulate either a passing or failing test result.
Dependency Build Tool
def build_dependencies(state: WorkflowState) -> bool:    return state["scenario"] != "dependency_fail"


Docker Build Tool
def build_docker_image(state: WorkflowState) -> tuple[bool, str | None]:    if state["scenario"] == "docker_fail":        return False, None    return True, "sha256:simulated-fixed-image-digest"


A successful simulated build produces a deterministic image digest.
Migration Assessment Tool
def assess_database_migration(state: WorkflowState) -> tuple[bool, str]:    if state["scenario"] == "unsafe_migration":        return False, "HIGH_BLOCKED"    return True, "LOW_REQUIRES_APPROVAL"


Database Migration Tool
def apply_database_migration(state: WorkflowState) -> tuple[bool, bool | None]:    if state["scenario"] == "migration_fail":        return False, True    if state["scenario"] == "migration_unknown":        return False, None    return True, True


The second returned value represents whether production may have been changed.
This is important because a failed migration does not automatically mean that the database remained unchanged.
Container Deployment Tool
def deploy_container(state: WorkflowState) -> tuple[bool, bool | None]:    if state["scenario"] == "deployment_fail":        return False, True    return True, True


Runtime Monitoring Tool
def read_runtime_monitoring_data(    state: WorkflowState) -> tuple[float | None, bool]:    if state["scenario"] == "monitoring_unknown":        return None, False    if state["scenario"] in {        "rollback",        "rollback_fail",        "rollback_unverified",    }:        return 8.0, True    return 0.5, True


The prototype uses a simulated 5% HTTP 5xx error threshold.
A rollback scenario produces an 8% error rate, which causes the Watchman-Agent to initiate recovery evaluation.
Rollback Tools
def perform_rollback(state: WorkflowState) -> bool:    return state["scenario"] != "rollback_fail"def verify_rollback(state: WorkflowState) -> bool:    return state["scenario"] != "rollback_unverified"


Rollback execution and rollback verification are deliberately separated.
A recovery operation is not considered successful until the restored system has been verified.
2.4 LangGraph StateGraph
The pipeline is implemented using LangGraph's StateGraph.
Only three graph nodes represent autonomous agents:
nodes = {    "Guard-Agent": guard_agent,    "Infra-Agent": infra_agent,    "Watchman-Agent": watchman_agent,}


Supporting nodes are deterministic workflow operations, including:
- DEPENDENCIES
- DOCKER_BUILD
- MIGRATION_ASSESSMENT
- HUMAN_APPROVAL
- MIGRATION_EXECUTING
- DEPLOYING
- RECOVERY_EVALUATION
- ROLLBACK_EXECUTING
- ROLLBACK_VERIFYING
These supporting nodes are not additional autonomous agents.
The terminal states are:
terminal_states = (    "SUCCESS",    "FAILED",    "ROLLED_BACK",    "ROLLBACK_FAILED",    "MANUAL_INTERVENTION_REQUIRED",)


Every terminal state connects directly to LangGraph's END.
2.5 Conditional Routing
The pipeline uses conditional edges so that each major decision is controlled by explicit state values.
Guard-Agent Routing
graph.add_conditional_edges(    "Guard-Agent",    choose(        "test_status",        {            "PASSED": "Infra-Agent",            "FAILED": "FAILED",        },    ),)


This prevents the Infra-Agent from running when tests fail.
Dependency and Docker Routing
graph.add_conditional_edges(    "DEPENDENCIES",    choose(        "dependency_status",        {            "SUCCESS": "DOCKER_BUILD",            "FAILED": "FAILED",        },    ),)graph.add_conditional_edges(    "DOCKER_BUILD",    choose(        "docker_status",        {            "SUCCESS": "MIGRATION_ASSESSMENT",            "FAILED": "FAILED",        },    ),)


Migration Assessment Routing
graph.add_conditional_edges(    "MIGRATION_ASSESSMENT",    choose(        "current_state",        {            "MIGRATION_ASSESSED": "HUMAN_APPROVAL",            "MIGRATION_BLOCKED": "FAILED",        },    ),)


Human Approval Routing
graph.add_conditional_edges(    "HUMAN_APPROVAL",    choose(        "approval_status",        {            "APPROVED": "MIGRATION_EXECUTING",            "REJECTED": "FAILED",        },    ),)


Migration and Deployment Failure Routing
graph.add_conditional_edges(    "MIGRATION_EXECUTING",    choose(        "migration_status",        {            "SUCCESS": "DEPLOYING",            "FAILED": "RECOVERY_EVALUATION",            "BLOCKED": "RECOVERY_EVALUATION",        },    ),)graph.add_conditional_edges(    "DEPLOYING",    choose(        "deployment_status",        {            "SUCCESS": "Watchman-Agent",            "FAILED": "RECOVERY_EVALUATION",        },    ),)


Watchman-Agent Routing
graph.add_conditional_edges(    "Watchman-Agent",    choose(        "monitoring_status",        {            "HEALTHY": "SUCCESS",            "BREACHED": "RECOVERY_EVALUATION",            "UNKNOWN": "RECOVERY_EVALUATION",        },    ),)


A healthy deployment reaches SUCCESS.
An unhealthy or unknown monitoring result enters recovery evaluation.
2.6 Human-in-the-Loop Implementation
The human approval gate uses LangGraph's interrupt() function.
def human_approval(state: WorkflowState) -> dict[str, Any]:    answer = interrupt(        {            "question":                "Approve simulated production DB migration?",            "choices": ["approve", "reject"],            "risk": state["migration_risk"],            "image_digest": state["image_digest"],        }    )    approved = answer == "approve"    return update(        state,        "APPROVED" if approved else "APPROVAL_REJECTED",        approval_status=            "APPROVED" if approved else "REJECTED",    )


When the graph reaches this node, execution pauses.
The console driver then asks the engineer to enter:
approve

or:
reject

The graph resumes using:
Command(resume=answer)


This means the production migration cannot execute until a human decision is supplied.
Invalid console input is treated as rejection so that the workflow fails closed.
2.7 Recovery and Rollback Guardrails
The corrected architecture is implemented in the recovery_evaluation() node.
def recovery_evaluation(    state: WorkflowState) -> dict[str, Any]:    if state["production_changed"] is False:        target = "FAILED"    elif state["production_changed"] is None:        target = "MANUAL_INTERVENTION_REQUIRED"    elif state["rollback_attempt_count"] >= 1:        target = "MANUAL_INTERVENTION_REQUIRED"    elif not (        state["previous_version"]        and state["previous_image_digest"]        and state["previous_version_verified"]        and state["database_compatible"] is True        and state["recovery_safe"]        and state["recovery_authorized"]    ):        target = "MANUAL_INTERVENTION_REQUIRED"    else:        target = "ROLLBACK_EXECUTING"    return update(        state,        "RECOVERY_EVALUATION",        recovery_target=target,    )


The state can therefore route only to:
- FAILED
- ROLLBACK_EXECUTING
- MANUAL_INTERVENTION_REQUIRED
Automatic rollback requires all recovery prerequisites to be valid.
The rollback execution node also prevents more than one automatic attempt:
def rollback_execution(    state: WorkflowState) -> dict[str, Any]:    if state["rollback_attempt_count"] != 0:        return update(            state,            "ROLLBACK_FAILED",            rollback_status="FAILED",        )    attempt = state["rollback_attempt_count"] + 1    ok = perform_rollback(state)    return update(        state,        "ROLLBACK_EXECUTED"            if ok            else "ROLLBACK_FAILED",        rollback_attempt_count=attempt,        rollback_status=            "EXECUTED" if ok else "FAILED",    )


A successful rollback operation does not immediately become ROLLED_BACK.
It must first pass rollback verification:
def rollback_verification(    state: WorkflowState) -> dict[str, Any]:    ok = verify_rollback(state)    return update(        state,        "ROLLED_BACK"            if ok            else "ROLLBACK_FAILED",        rollback_status=            "VERIFIED" if ok else "UNVERIFIED",    )


This prevents the workflow from claiming recovery success without verification.
2.8 Execution Verification
The generated LangGraph prototype was executed in GitHub Codespaces.
The following scenarios were personally tested.
Scenario	Human Input	Observed Final State	Result
Successful deployment	approve	SUCCESS	Verified
Failed unit test	None	FAILED	Verified
Rejected migration approval	reject	FAILED	Verified
Docker build failure	None	FAILED	Verified
Post-deployment error threshold breach	approve	ROLLED_BACK	Verified
Migration failure with unsafe automatic recovery	approve	MANUAL_INTERVENTION_REQUIRED	Verified


Successful Deployment
The successful test produced the following state progression:
EVENT_RECEIVED
TEST_PASSED
INFRA_PENDING
DEPENDENCIES_READY
IMAGE_BUILT
MIGRATION_ASSESSED
APPROVED
MIGRATED
DEPLOYED
MONITORING_PASSED
SUCCESS

The graph visibly paused at the human approval gate before migration.
After entering:
approve

the workflow resumed and completed with:
FINAL STATE: SUCCESS
Rollback attempts: 0

Failed Unit Test
The failed-test scenario produced:
EVENT_RECEIVED
TEST_FAILED
FAILED

Observed final state:
FINAL STATE: FAILED

INFRA_PENDING did not appear, confirming that the Guard-Agent blocked the infrastructure stage.
Rejected Migration Approval
The workflow reached the human approval gate.
The input entered was:
reject

The resulting path included:
MIGRATION_ASSESSED
APPROVAL_REJECTED
FAILED

No migration or deployment occurred after the rejection.
Observed final state:
FINAL STATE: FAILED

Docker Build Failure
The Docker failure scenario produced:
TEST_PASSED
INFRA_PENDING
DEPENDENCIES_READY
BUILD_FAILED
FAILED

No human approval or migration stage was reached.
Observed final state:
FINAL STATE: FAILED

Post-Deployment Rollback
The rollback scenario was approved at the migration gate.
The deployment completed, after which the Watchman-Agent received a simulated HTTP 5xx error rate of:
8.0%

This exceeded the configured threshold.
The observed recovery path included:
ROLLBACK_REQUIRED
RECOVERY_EVALUATION
ROLLBACK_EXECUTED
ROLLED_BACK

Observed result:
FINAL STATE: ROLLED_BACK
Rollback attempts: 1
HTTP 5xx error rate: 8.0

This verified that the workflow could detect a post-deployment problem and execute one bounded rollback.
Migration Failure Requiring Manual Intervention
The migration-failure scenario reached the human approval gate and was approved.
The simulated migration then failed.
The observed path included:
MIGRATION_FAILED
RECOVERY_EVALUATION
MANUAL_INTERVENTION_REQUIRED

Observed result:
FINAL STATE: MANUAL_INTERVENTION_REQUIRED
Rollback attempts: 0

This demonstrated the fail-closed recovery behavior.
Because database compatibility and recovery safety were not verified for this scenario, the system did not automatically attempt a rollback.
2.9 Framework Verification Summary
The executed prototype demonstrated the required Week 10 orchestration behaviors:
- three specialized agents,
- shared workflow state,
- deterministic graph transitions,
- agent-bound tool functions,
- conditional routing,
- human-in-the-loop approval before database migration,
- failed-test blocking,
- Docker build failure handling,
- migration failure handling,
- post-deployment monitoring,
- recovery evaluation,
- bounded rollback,
- rollback verification,
- manual escalation when recovery cannot be proven safe,
- and terminal workflow states that do not automatically restart the pipeline.
The implementation therefore demonstrated both the normal deployment path and multiple guarded failure paths using an executable LangGraph StateGraph prototype.
---

# 3. Prompt Engineering & Correction Log

## 3.1 Initial Architecture Prompt

The first prompt was designed to generate the structural architecture before any implementation code was written.

The exact prompt used was:

```text
ROLE

Act as a Lead DevOps Engineer and Agentic Systems Architect assisting a 4th-year IT student.

CONTEXT

We are designing an Event-Driven Agentic Pipeline for an enterprise microservice production deployment workflow.

The current manual deployment process is:

1. Code Push
2. Run Unit Tests
3. Build Docker Image
4. DB Migration
5. Monitor Logs

The goal is to replace repetitive manual routing with a controlled event-driven multi-agent workflow.

The required autonomous ecosystem must contain exactly these three specialized agents:

1. Guard-Agent
   - listens for a code push or webhook event
   - triggers the unit test suite
   - parses raw console output
   - decides whether the build should pass or fail

2. Infra-Agent
   - activates only after the Guard-Agent gives a green light
   - builds dependencies
   - builds the Docker image
   - processes Entity Framework or SQL database migrations
   - deploys the container

3. Watchman-Agent
   - monitors live runtime logs after deployment
   - monitors HTTP error rates
   - detects anomalies
   - triggers rollback when defined error thresholds are exceeded

TASK

Design the structural architecture for this agentic deployment pipeline.

For each agent, define:

- trigger
- input state
- responsibilities
- output state
- decision points
- success path
- failure path
- data passed to the next state

Also define:

1. the shared workflow state,
2. the major deterministic states,
3. the conditional routing between agents,
4. where rollback can occur,
5. where a human-in-the-loop approval gate must pause the workflow before database migration reaches production,
6. terminal success and failure states.

FORMAT

Return the answer in this exact order:

1. Architecture Overview
2. Shared Workflow State
3. Guard-Agent
4. Infra-Agent
5. Watchman-Agent
6. Conditional Routing Logic
7. Human-in-the-Loop Gate
8. Rollback Logic
9. Final Text-Based State Flow

Do not write implementation code yet.

CONSTRAINTS

- Use only the three required agents: Guard-Agent, Infra-Agent, and Watchman-Agent.
- Do not introduce additional agents.
- Do not skip the human-in-the-loop approval gate before production database migration.
- Do not allow the Infra-Agent to proceed if testing fails.
- Do not allow deployment to proceed if the Docker build fails.
- Do not allow an unsafe migration to continue automatically.
- Do not create an infinite retry loop.
- Do not fabricate successful test, build, migration, deployment, or monitoring results.
- Keep routing logic explicit and deterministic where possible.
- Keep the design realistic for a Week 10 student activity.
- Do not generate LangGraph or Semantic Kernel code yet.

3.2 Initial AI-Generated Architecture
The first AI response successfully produced:
- exactly three specialized agents,
- a shared workflow state,
- conditional routing,
- a human approval gate before production database migration,
- post-deployment monitoring,
- rollback concepts,
- and terminal workflow states.
The generated architecture also correctly treated the workflow orchestrator as a deterministic state-management component rather than as a fourth autonomous agent.
However, the first architecture contained a structural weakness in its recovery logic.
3.3 Identified Structural Issue
During review of the first AI-generated architecture, a real routing problem was identified.
Both migration failure and deployment failure could route to:
RECOVERY_EVALUATION

However, the first version did not completely define all outgoing transitions from this intermediate state.
The architecture stated that RECOVERY_EVALUATION had to be resolved, but it did not fully specify:
- when recovery was considered safe,
- when rollback should actually begin,
- when the workflow should terminate as failed,
- when human intervention was required,
- how database compatibility should affect rollback,
- what should happen if rollback safety could not be established,
- and how recovery would be prevented from looping indefinitely.
This created an ambiguous state-machine branch.
A deterministic orchestration system should not enter an intermediate state without explicit rules for leaving that state.
The issue was therefore treated as a structural logic problem rather than a syntax problem.
3.4 Correction Prompt
The exact correction prompt used was:
ROLE

Continue acting as the Lead DevOps Engineer and Agentic Systems Architect.

OBSERVED STRUCTURAL ISSUE

In the first architecture iteration, both migration failure and deployment failure can route into the intermediate state:

RECOVERY_EVALUATION

However, RECOVERY_EVALUATION does not yet have a complete deterministic set of outgoing transitions.

The architecture states that this condition must be explicitly resolved, but it does not fully define:

- when recovery is considered safe,
- when rollback should begin,
- when the workflow should terminate as failed,
- when escalation to human intervention is required,
- and what happens if recovery cannot be verified.

This creates an ambiguous state-machine branch that could stall or produce undefined behavior.

TASK

Refactor the architecture so that RECOVERY_EVALUATION has explicit and deterministic routing.

Define:

1. the exact conditions evaluated inside RECOVERY_EVALUATION,
2. the possible outgoing states,
3. the condition required to enter ROLLBACK_EXECUTING,
4. the condition that produces terminal FAILED,
5. the condition that produces ROLLBACK_FAILED or escalation,
6. how database migration failures differ from application/container deployment failures,
7. how the previously healthy deployment version and database compatibility are validated before rollback,
8. how the workflow prevents recovery from looping back indefinitely.

Also update the routing table and final state flow so that every path from RECOVERY_EVALUATION resolves to a defined next state.

CONSTRAINTS

- Keep exactly the same three agents: Guard-Agent, Infra-Agent, and Watchman-Agent.
- Do not introduce a Recovery-Agent or any additional autonomous agent.
- The workflow orchestrator may evaluate recovery conditions.
- No terminal state may automatically restart the pipeline.
- No unlimited retry loops.
- Maximum one automatic rollback attempt.
- Do not assume database rollback is always safe.
- Do not treat Docker/application rollback as equivalent to database rollback.
- Require explicit human intervention when recovery cannot be safely determined.
- Preserve the mandatory human approval gate before production database migration.
- Do not fabricate successful recovery results.
- Do not write implementation code yet.

OUTPUT FORMAT

Return only the revised sections affected by this correction:

1. Revised RECOVERY_EVALUATION Logic
2. Revised Conditional Routing Table
3. Revised Rollback Logic
4. Revised Final Text-Based State Flow
5. Brief Explanation of What Was Corrected

3.5 Corrected Architecture
The correction prompt successfully converted RECOVERY_EVALUATION into a deterministic decision state.
The corrected architecture defined three explicit outgoing states:
FAILED
ROLLBACK_EXECUTING
MANUAL_INTERVENTION_REQUIRED

The corrected decision logic became:
RECOVERY_EVALUATION
        |
        v
Was production definitely unchanged?
        |
   +----+----+
   |         |
  YES     NO / UNKNOWN
   |         |
   v         v
FAILED   Is recovery evidence complete?
              |
         +----+----+
         |         |
        NO        YES
         |         |
         v         v
MANUAL_       Are previous version,
INTERVENTION  DB compatibility,
REQUIRED      recovery plan and
              authorization verified?
                   |
              +----+----+
              |         |
             NO        YES
              |         |
              v         v
          MANUAL_    Rollback count = 0?
          INTERVENTION    |
          REQUIRED    +---+---+
                      |       |
                     NO      YES
                      |       |
                      v       v
                  MANUAL_  ROLLBACK_EXECUTING
                  INTERVENTION     |
                  REQUIRED         v
                             Rollback succeeds?
                                  |
                             +----+----+
                             |         |
                            NO        YES
                             |         |
                             v         v
                     ROLLBACK_FAILED
                                       |
                                       v
                              ROLLBACK_VERIFYING
                                       |
                                  +----+----+
                                  |         |
                                FAIL     VERIFIED
                                  |         |
                                  v         v
                           ROLLBACK_FAILED
                                         ROLLED_BACK

The corrected architecture also explicitly distinguished:
- application or container rollback,
- database recovery,
- migration failure,
- deployment failure,
- uncertain production state,
- and failed rollback verification.
A previous application image could only be restored automatically when:
- a previously healthy version existed,
- the exact previous image artifact was available,
- that version was verified,
- the current database remained compatible,
- the recovery action was considered safe,
- recovery was authorized,
- and no automatic rollback had already been attempted.
The correction also introduced:
rollback_attempt_count

with a maximum automatic value of:
1

No recovery state automatically loops back to Guard-Agent, Infra-Agent, or Watchman-Agent.
A corrected release requires a new workflow execution.
3.6 Code-Generation Prompt
After the architecture was corrected, a third prompt was used to synthesize the LangGraph implementation.
The exact prompt used was:
ROLE

Act as a Python DevOps Engineer and LangGraph developer.

CONTEXT

We already designed and corrected an Event-Driven Agentic Deployment Pipeline for a Week 10 individual activity.

The system must use exactly three specialized agents:

1. Guard-Agent
2. Infra-Agent
3. Watchman-Agent

The corrected architecture requires:

- explicit shared workflow state
- deterministic routing
- no infinite loops
- Guard-Agent must block Infra-Agent when tests fail
- Docker build failure must stop progression
- a mandatory human-in-the-loop approval gate before production database migration
- migration failure must route into RECOVERY_EVALUATION
- deployment failure must route into RECOVERY_EVALUATION
- monitoring threshold breaches must route into RECOVERY_EVALUATION
- RECOVERY_EVALUATION must route deterministically to:
  - FAILED
  - ROLLBACK_EXECUTING
  - MANUAL_INTERVENTION_REQUIRED
- maximum one automatic rollback attempt
- rollback verification before ROLLED_BACK
- no automatic restart from terminal states

TASK

Generate a complete Python prototype using LangGraph StateGraph.

The prototype must model the Week 10 architecture and must be executable in GitHub Codespaces.

IMPLEMENTATION REQUIREMENTS

1. Use Python.
2. Use LangGraph StateGraph.
3. Define a TypedDict or equivalent shared workflow state.
4. Represent these required agents as graph nodes:
   - Guard-Agent
   - Infra-Agent
   - Watchman-Agent
5. Define callable tool functions used by the agents for:
   - running unit tests
   - building dependencies
   - building a Docker image
   - assessing a database migration
   - applying a database migration
   - deploying a container
   - reading runtime monitoring data
   - performing rollback
6. For this student prototype, the tool functions may safely simulate external production operations instead of modifying a real production system.
7. Make the simulation deterministic and controllable through input state so that different scenarios can be tested.
8. Include conditional edges for:
   - test pass/fail
   - Docker build success/failure
   - migration approval/rejection
   - migration success/failure
   - deployment success/failure
   - healthy monitoring / threshold breach
   - recovery evaluation
   - rollback success/failure
9. Include a human-in-the-loop approval node before production database migration.
10. For the local educational prototype, the human gate may use console input such as approve/reject, provided the workflow actually pauses for the decision.
11. RECOVERY_EVALUATION must explicitly evaluate:
   - whether production changed
   - whether a previous healthy version exists
   - database compatibility
   - recovery safety
   - recovery authorization
   - rollback attempt count
12. Maximum automatic rollback attempts: 1.
13. After rollback execution, route through rollback verification before allowing ROLLED_BACK.
14. All workflow paths must terminate.
15. Terminal states must include at least:
   - SUCCESS
   - FAILED
   - ROLLED_BACK
   - ROLLBACK_FAILED
   - MANUAL_INTERVENTION_REQUIRED

STUDENT-SCOPE CONSTRAINTS

- Do not connect to real production infrastructure.
- Do not require Docker daemon access for the prototype.
- Do not modify a real database.
- Do not call cloud deployment APIs.
- Use deterministic simulation functions for external operations.
- Keep the code understandable to a 4th-year IT student.
- Do not introduce additional autonomous agents.
- Supporting graph nodes such as human approval, recovery evaluation, and rollback verification are allowed but are not additional agents.
- Do not use unlimited retries.
- Do not fabricate execution output in the explanation.

OUTPUT FORMAT

Return exactly:

1. requirements.txt contents
2. one complete Python file named agentic_pipeline.py
3. concise explanation of each graph node
4. exact terminal commands to install dependencies and run the prototype
5. example scenario inputs that can be used to test:
   - successful deployment
   - failed unit test
   - rejected migration approval
   - Docker build failure
   - post-deployment rollback

3.7 AI-Generated LangGraph Implementation
The third AI iteration generated:
requirements.txt
agentic_pipeline.py

The dependency file contained:
langgraph>=1.0,<2.0

The generated Python implementation included:
- a shared WorkflowState,
- Guard-Agent,
- Infra-Agent,
- Watchman-Agent,
- deterministic simulation tools,
- LangGraph StateGraph,
- conditional routing,
- a real LangGraph interrupt() human approval gate,
- recovery evaluation,
- one-attempt rollback control,
- rollback verification,
- terminal states,
- scenario-based test inputs.
The generated implementation was preserved without manually rewriting its core logic before first execution.
The AI originally stated that full LangGraph execution could not be tested in its own generation environment.
For this activity, that claim was not treated as proof of correctness.
The generated files were instead downloaded and executed separately in GitHub Codespaces.
3.8 Validation Summary
The generated implementation was tested directly in GitHub Codespaces.
The following results were actually observed.
Test 1 — Successful Deployment
Command:
python agentic_pipeline.py --scenario success

Human input:
approve

Observed final result:
FINAL STATE: SUCCESS
Rollback attempts: 0

This verified:
- successful Guard-Agent routing,
- successful infrastructure preparation,
- human approval pause,
- migration execution,
- deployment,
- post-deployment monitoring,
- and successful termination.
Test 2 — Failed Unit Test
Command:
python agentic_pipeline.py --scenario test_fail

Observed path:
EVENT_RECEIVED
TEST_FAILED
FAILED

Observed final result:
FINAL STATE: FAILED

This verified that Infra-Agent did not run when Guard-Agent validation failed.
Test 3 — Rejected Migration Approval
Command:
python agentic_pipeline.py --scenario approval_reject

Human input:
reject

Observed path:
MIGRATION_ASSESSED
APPROVAL_REJECTED
FAILED

Observed final result:
FINAL STATE: FAILED

This verified that the production migration could not continue after human rejection.
Test 4 — Docker Build Failure
Command:
python agentic_pipeline.py --scenario docker_fail

Observed path:
TEST_PASSED
INFRA_PENDING
DEPENDENCIES_READY
BUILD_FAILED
FAILED

Observed final result:
FINAL STATE: FAILED

This verified that migration and deployment were not reached after a failed Docker build.
Test 5 — Post-Deployment Rollback
Command:
python agentic_pipeline.py --scenario rollback

Human input:
approve

The Watchman-Agent received a simulated HTTP 5xx error rate of:
8.0%

Observed recovery path:
ROLLBACK_REQUIRED
RECOVERY_EVALUATION
ROLLBACK_EXECUTED
ROLLED_BACK

Observed result:
FINAL STATE: ROLLED_BACK
Rollback attempts: 1
HTTP 5xx error rate: 8.0

This verified the corrected recovery routing and bounded rollback behavior.
Test 6 — Migration Failure with Manual Intervention
Command:
python agentic_pipeline.py --scenario migration_fail

Human input:
approve

Observed path:
MIGRATION_FAILED
RECOVERY_EVALUATION
MANUAL_INTERVENTION_REQUIRED

Observed final result:
FINAL STATE: MANUAL_INTERVENTION_REQUIRED
Rollback attempts: 0

This verified that an unsafe or incompatible database recovery was not automatically attempted.
3.9 Prompt Correction Result
The prompt correction process improved the architecture in a measurable way.
The first AI iteration successfully created the major deployment structure but left the RECOVERY_EVALUATION branch partially undefined.
The correction prompt forced the AI to:
- define deterministic recovery conditions,
- distinguish application rollback from database recovery,
- validate database compatibility,
- verify the previous healthy release,
- introduce manual escalation for uncertain conditions,
- limit automatic rollback to one attempt,
- add rollback verification,
- and guarantee terminal workflow outcomes.
The corrected architecture was then used as the basis for the executable LangGraph implementation.
The implementation tests confirmed that the corrected recovery behavior was represented in the actual running prototype.
This demonstrates the correction-loop process:
INITIAL PROMPT
      |
      v
INITIAL AI ARCHITECTURE
      |
      v
STRUCTURAL REVIEW
      |
      v
RECOVERY ROUTING ISSUE IDENTIFIED
      |
      v
CORRECTION PROMPT
      |
      v
CORRECTED ARCHITECTURE
      |
      v
CODE-GENERATION PROMPT
      |
      v
LANGGRAPH IMPLEMENTATION
      |
      v
ACTUAL EXECUTION TESTING
      |
      v
VERIFIED / OBSERVED RESULTS

The AI output was therefore not accepted automatically.
It was reviewed, corrected, implemented, and validated through actual execution before being treated as the final solution.

---

# Conclusion

The Week 10 activity demonstrated how a fragile manual deployment workflow can be transformed into a controlled Event-Driven Agentic Pipeline.

The original process depended on engineers to manually execute and verify unit testing, Docker image creation, database migration, deployment, and post-deployment monitoring.

The redesigned solution introduced exactly three specialized agents:

- Guard-Agent for test validation,
- Infra-Agent for build, migration, and deployment operations,
- Watchman-Agent for runtime monitoring and rollback initiation.

LangGraph `StateGraph` was used to coordinate these agents through a shared workflow state and explicit conditional transitions.

A mandatory human-in-the-loop gate was implemented before production database migration so that high-risk database changes could not proceed automatically.

The first AI-generated architecture was not accepted without review. A structural weakness was identified in the `RECOVERY_EVALUATION` state because its outgoing recovery routes were not fully deterministic.

A correction prompt was then used to define:

- explicit recovery conditions,
- database compatibility checks,
- previous-version verification,
- bounded rollback behavior,
- rollback verification,
- manual escalation for unsafe or uncertain recovery,
- and terminal recovery states.

The corrected architecture was then used to generate an executable LangGraph prototype.

The prototype was tested in GitHub Codespaces using multiple scenarios.

Actual execution verified:

- successful deployment,
- failed unit-test blocking,
- rejected human approval,
- Docker build failure handling,
- post-deployment rollback,
- and migration failure requiring manual intervention.

The final implementation therefore demonstrates the key objectives of the activity:

1. decomposition of a manual deployment process into discrete operational states,
2. orchestration of an event-driven multi-agent workflow,
3. explicit state and data handoffs between deployment stages,
4. deterministic failure routing,
5. human-in-the-loop control for database migration,
6. guarded rollback behavior,
7. and correction of AI-generated structural logic through prompt refinement and validation.

The solution remains a simulation-only educational prototype and does not modify real Docker infrastructure, production databases, or cloud environments.