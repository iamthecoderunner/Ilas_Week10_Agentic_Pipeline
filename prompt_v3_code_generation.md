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