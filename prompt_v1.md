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