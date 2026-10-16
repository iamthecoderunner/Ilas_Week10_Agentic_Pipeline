"""Week 10: deterministic, simulation-only LangGraph deployment pipeline.

Exactly three agent nodes: Guard-Agent, Infra-Agent and Watchman-Agent.
Other nodes are deterministic infrastructure/orchestration states, not agents.
No Docker, database, cloud API, or LLM calls are performed.
"""

import argparse
import json
import uuid
from typing import Any, Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class WorkflowState(TypedDict):
    workflow_id: str
    scenario: str
    current_state: str
    commit_sha: str
    test_status: str
    dependency_status: str
    docker_status: str
    image_digest: str | None
    migration_risk: str
    migration_status: str
    approval_status: str
    deployment_status: str
    monitoring_status: str
    http_error_rate: float | None
    production_changed: bool | None
    previous_version: str | None
    previous_image_digest: str | None
    previous_version_verified: bool
    database_compatible: bool | None
    recovery_safe: bool
    recovery_authorized: bool
    rollback_attempt_count: int
    rollback_status: str
    recovery_reason: str
    recovery_target: str
    events: list[str]


# ---- Deterministic tools: nothing is executed against real infrastructure. ----
def run_unit_tests(state: WorkflowState) -> bool:
    return state["scenario"] != "test_fail"


def build_dependencies(state: WorkflowState) -> bool:
    return state["scenario"] != "dependency_fail"


def build_docker_image(state: WorkflowState) -> tuple[bool, str | None]:
    if state["scenario"] == "docker_fail":
        return False, None
    return True, "sha256:simulated-fixed-image-digest"


def assess_database_migration(state: WorkflowState) -> tuple[bool, str]:
    if state["scenario"] == "unsafe_migration":
        return False, "HIGH_BLOCKED"
    return True, "LOW_REQUIRES_APPROVAL"


def apply_database_migration(state: WorkflowState) -> tuple[bool, bool | None]:
    if state["scenario"] == "migration_fail":
        return False, True  # Simulated partial production change.
    if state["scenario"] == "migration_unknown":
        return False, None  # Unknown production state => no automatic rollback.
    return True, True  # Simulated schema change.


def deploy_container(state: WorkflowState) -> tuple[bool, bool | None]:
    if state["scenario"] == "deployment_fail":
        return False, True
    return True, True


def read_runtime_monitoring_data(state: WorkflowState) -> tuple[float | None, bool]:
    if state["scenario"] == "monitoring_unknown":
        return None, False
    if state["scenario"] in {"rollback", "rollback_fail", "rollback_unverified"}:
        return 8.0, True
    return 0.5, True


def perform_rollback(state: WorkflowState) -> bool:
    return state["scenario"] != "rollback_fail"


def verify_rollback(state: WorkflowState) -> bool:
    return state["scenario"] != "rollback_unverified"


# ---- State helpers. Each node returns a partial TypedDict update. ----
def update(state: WorkflowState, name: str, **changes: Any) -> dict[str, Any]:
    return {"current_state": name,
            "events": state["events"] + [name], **changes}


def guard_agent(state: WorkflowState) -> dict[str, Any]:
    passed = run_unit_tests(state)
    return update(state, "TEST_PASSED" if passed else "TEST_FAILED",
                  test_status="PASSED" if passed else "FAILED")


def infra_agent(state: WorkflowState) -> dict[str, Any]:
    # The only entry to Infra-Agent is the test-passed conditional edge.
    if state["test_status"] != "PASSED":
        return update(state, "FAILED", recovery_reason="Guard clearance absent")
    return update(state, "INFRA_PENDING")


def dependencies_node(state: WorkflowState) -> dict[str, Any]:
    ok = build_dependencies(state)
    return update(state, "DEPENDENCIES_READY" if ok else "BUILD_FAILED",
                  dependency_status="SUCCESS" if ok else "FAILED")


def docker_node(state: WorkflowState) -> dict[str, Any]:
    ok, digest = build_docker_image(state)
    return update(state, "IMAGE_BUILT" if ok else "BUILD_FAILED",
                  docker_status="SUCCESS" if ok else "FAILED", image_digest=digest)


def migration_assessment(state: WorkflowState) -> dict[str, Any]:
    ok, risk = assess_database_migration(state)
    return update(state, "MIGRATION_ASSESSED" if ok else "MIGRATION_BLOCKED",
                  migration_risk=risk)


def human_approval(state: WorkflowState) -> dict[str, Any]:
    # This is a real LangGraph pause. The console driver resumes with Command.
    answer = interrupt({"question": "Approve simulated production DB migration?",
                        "choices": ["approve", "reject"],
                        "risk": state["migration_risk"],
                        "image_digest": state["image_digest"]})
    approved = answer == "approve"
    return update(state, "APPROVED" if approved else "APPROVAL_REJECTED",
                  approval_status="APPROVED" if approved else "REJECTED")


def migration_node(state: WorkflowState) -> dict[str, Any]:
    if state["approval_status"] != "APPROVED" or state["docker_status"] != "SUCCESS":
        return update(state, "MIGRATION_FAILED", migration_status="BLOCKED",
                      recovery_reason="Missing approval or image")
    ok, changed = apply_database_migration(state)
    return update(state, "MIGRATED" if ok else "MIGRATION_FAILED",
                  migration_status="SUCCESS" if ok else "FAILED",
                  production_changed=changed,
                  recovery_reason="migration failure" if not ok else "")


def deployment_node(state: WorkflowState) -> dict[str, Any]:
    ok, changed = deploy_container(state)
    return update(state, "DEPLOYED" if ok else "DEPLOYMENT_FAILED",
                  deployment_status="SUCCESS" if ok else "FAILED",
                  production_changed=changed,
                  recovery_reason="deployment failure" if not ok else "")


def watchman_agent(state: WorkflowState) -> dict[str, Any]:
    rate, valid = read_runtime_monitoring_data(state)
    if not valid or rate is None:
        return update(state, "MONITORING_ERROR", monitoring_status="UNKNOWN",
                      http_error_rate=None, production_changed=True,
                      recovery_reason="monitoring evidence missing")
    breached = rate > 5.0
    return update(state, "ROLLBACK_REQUIRED" if breached else "MONITORING_PASSED",
                  monitoring_status="BREACHED" if breached else "HEALTHY",
                  http_error_rate=rate, production_changed=True,
                  recovery_reason="HTTP 5xx threshold exceeded" if breached else "")


def recovery_evaluation(state: WorkflowState) -> dict[str, Any]:
    # Complete, ordered, fail-closed decisions.
    if state["production_changed"] is False:
        target = "FAILED"
    elif state["production_changed"] is None:
        target = "MANUAL_INTERVENTION_REQUIRED"
    elif state["rollback_attempt_count"] >= 1:
        target = "MANUAL_INTERVENTION_REQUIRED"
    elif not (state["previous_version"] and state["previous_image_digest"]
              and state["previous_version_verified"]
              and state["database_compatible"] is True
              and state["recovery_safe"] and state["recovery_authorized"]):
        target = "MANUAL_INTERVENTION_REQUIRED"
    else:
        target = "ROLLBACK_EXECUTING"
    return update(state, "RECOVERY_EVALUATION", recovery_target=target)


def rollback_execution(state: WorkflowState) -> dict[str, Any]:
    if state["rollback_attempt_count"] != 0:
        return update(state, "ROLLBACK_FAILED", rollback_status="FAILED")
    # Reserve the attempt before executing the simulated operation.
    attempt = state["rollback_attempt_count"] + 1
    ok = perform_rollback(state)
    return update(state, "ROLLBACK_EXECUTED" if ok else "ROLLBACK_FAILED",
                  rollback_attempt_count=attempt,
                  rollback_status="EXECUTED" if ok else "FAILED")


def rollback_verification(state: WorkflowState) -> dict[str, Any]:
    ok = verify_rollback(state)
    return update(state, "ROLLED_BACK" if ok else "ROLLBACK_FAILED",
                  rollback_status="VERIFIED" if ok else "UNVERIFIED")


def terminal_node(name: str):
    def node(state: WorkflowState) -> dict[str, Any]:
        return update(state, name)
    return node


def choose(field: str, mapping: dict[str, str]):
    def route(state: WorkflowState) -> str:
        return mapping[state[field]]
    return route


def create_graph():
    graph = StateGraph(WorkflowState)
    nodes = {
        "Guard-Agent": guard_agent,
        "Infra-Agent": infra_agent,
        "DEPENDENCIES": dependencies_node,
        "DOCKER_BUILD": docker_node,
        "MIGRATION_ASSESSMENT": migration_assessment,
        "HUMAN_APPROVAL": human_approval,
        "MIGRATION_EXECUTING": migration_node,
        "DEPLOYING": deployment_node,
        "Watchman-Agent": watchman_agent,
        "RECOVERY_EVALUATION": recovery_evaluation,
        "ROLLBACK_EXECUTING": rollback_execution,
        "ROLLBACK_VERIFYING": rollback_verification,
    }
    terminal_states = ("SUCCESS", "FAILED", "ROLLED_BACK", "ROLLBACK_FAILED",
                       "MANUAL_INTERVENTION_REQUIRED")
    for name in terminal_states:
        nodes[name] = terminal_node(name)
    for name, function in nodes.items():
        graph.add_node(name, function)
    graph.add_edge(START, "Guard-Agent")
    graph.add_conditional_edges("Guard-Agent", choose("test_status", {
        "PASSED": "Infra-Agent", "FAILED": "FAILED"}))
    graph.add_edge("Infra-Agent", "DEPENDENCIES")
    graph.add_conditional_edges("DEPENDENCIES", choose("dependency_status", {
        "SUCCESS": "DOCKER_BUILD", "FAILED": "FAILED"}))
    graph.add_conditional_edges("DOCKER_BUILD", choose("docker_status", {
        "SUCCESS": "MIGRATION_ASSESSMENT", "FAILED": "FAILED"}))
    graph.add_conditional_edges("MIGRATION_ASSESSMENT", choose("current_state", {
        "MIGRATION_ASSESSED": "HUMAN_APPROVAL", "MIGRATION_BLOCKED": "FAILED"}))
    graph.add_conditional_edges("HUMAN_APPROVAL", choose("approval_status", {
        "APPROVED": "MIGRATION_EXECUTING", "REJECTED": "FAILED"}))
    graph.add_conditional_edges("MIGRATION_EXECUTING", choose("migration_status", {
        "SUCCESS": "DEPLOYING", "FAILED": "RECOVERY_EVALUATION",
        "BLOCKED": "RECOVERY_EVALUATION"}))
    graph.add_conditional_edges("DEPLOYING", choose("deployment_status", {
        "SUCCESS": "Watchman-Agent", "FAILED": "RECOVERY_EVALUATION"}))
    graph.add_conditional_edges("Watchman-Agent", choose("monitoring_status", {
        "HEALTHY": "SUCCESS", "BREACHED": "RECOVERY_EVALUATION",
        "UNKNOWN": "RECOVERY_EVALUATION"}))
    graph.add_conditional_edges("RECOVERY_EVALUATION", choose("recovery_target", {
        "FAILED": "FAILED", "ROLLBACK_EXECUTING": "ROLLBACK_EXECUTING",
        "MANUAL_INTERVENTION_REQUIRED": "MANUAL_INTERVENTION_REQUIRED"}))
    graph.add_conditional_edges("ROLLBACK_EXECUTING", choose("rollback_status", {
        "EXECUTED": "ROLLBACK_VERIFYING", "FAILED": "ROLLBACK_FAILED"}))
    graph.add_conditional_edges("ROLLBACK_VERIFYING", choose("rollback_status", {
        "VERIFIED": "ROLLED_BACK", "UNVERIFIED": "ROLLBACK_FAILED"}))
    for name in terminal_states:
        graph.add_edge(name, END)
    return graph.compile(checkpointer=InMemorySaver())


SCENARIOS = ["success", "test_fail", "approval_reject", "docker_fail",
             "rollback", "dependency_fail", "unsafe_migration", "migration_fail",
             "migration_unknown", "deployment_fail", "monitoring_unknown",
             "rollback_fail", "rollback_unverified", "incompatible_db"]


def initial_state(scenario: str) -> WorkflowState:
    compatible = scenario not in {"incompatible_db", "migration_fail"}
    return {
        "workflow_id": str(uuid.uuid4()), "scenario": scenario,
        "current_state": "EVENT_RECEIVED", "commit_sha": "demo-commit-001",
        "test_status": "PENDING", "dependency_status": "PENDING",
        "docker_status": "PENDING", "image_digest": None,
        "migration_risk": "UNKNOWN", "migration_status": "PENDING",
        "approval_status": "NOT_REQUESTED", "deployment_status": "PENDING",
        "monitoring_status": "PENDING", "http_error_rate": None,
        "production_changed": False, "previous_version": "v1.0.0",
        "previous_image_digest": "sha256:simulated-previous-image-digest",
        "previous_version_verified": True, "database_compatible": compatible,
        "recovery_safe": scenario != "migration_fail",
        "recovery_authorized": True, "rollback_attempt_count": 0,
        "rollback_status": "NOT_REQUIRED", "recovery_reason": "",
        "recovery_target": "NONE",
        "events": ["EVENT_RECEIVED"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulation-only deployment pipeline")
    parser.add_argument("--scenario", choices=SCENARIOS, default="success")
    args = parser.parse_args()
    graph = create_graph()
    state = initial_state(args.scenario)
    config = {"configurable": {"thread_id": state["workflow_id"]}}

    result = graph.invoke(state, config=config)
    if "__interrupt__" in result:
        question = result["__interrupt__"][0].value
        print("\nWORKFLOW PAUSED: HUMAN_APPROVAL")
        print(json.dumps(question, indent=2))
        try:
            answer = input("Type approve or reject: ").strip().lower()
        except EOFError:
            answer = "reject"  # Fail closed on noninteractive terminal.
        if answer not in {"approve", "reject"}:
            print("Invalid input: treating as reject (fail closed).")
            answer = "reject"
        result = graph.invoke(Command(resume=answer), config=config)

    print("\nSIMULATED TRANSITIONS:")
    for event in result["events"]:
        print(" -", event)
    print("\nFINAL STATE:", result["current_state"])
    print("Rollback attempts:", result["rollback_attempt_count"])
    print("HTTP 5xx error rate:", result["http_error_rate"])
    print("Note: these are simulated outcomes, not real infrastructure results.")


if __name__ == "__main__":
    main()
