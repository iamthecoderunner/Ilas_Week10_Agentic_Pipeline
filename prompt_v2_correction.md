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