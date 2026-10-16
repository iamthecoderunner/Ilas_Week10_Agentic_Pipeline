# Week 10 Activity Working Notes

## Stage 1 — Manual Baseline

### Current Manual Production Deployment Process

The Week 10 activity provides the following manual deployment sequence:

```text
[Trigger: Code Push]
        |
        v
[Manual Step 1: Run Unit Tests]
        |
        v
[Manual Step 2: Build Docker Image]
        |
        v
[Manual Step 3: DB Migration]
        |
        v
[Manual Step 4: Monitor Logs]

### Stage 1 Verification

The manual baseline above was derived strictly from the Week 10 deployment scenario.

The state labels such as `CODE_PUSHED`, `TESTING`, `BUILDING_IMAGE`, and `MONITORING` are working implementation labels created for this activity. They are not prescribed names from the activity sheet.

Stage 1 satisfies the requirement to identify:

- the current manual workflow,
- human intervention points,
- data or variables passed between stages,
- likely failure points,
- and deterministic operational states for later orchestration.

