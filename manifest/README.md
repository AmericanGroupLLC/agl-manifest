# Manifest (Desired State)

This directory is the desired-state layer for the control plane.

- Human-maintained or generated from a controlled source
- Defines what the fleet *should* look like
- Input to orchestration and policy checks

Primary file:

- `apps.yaml`: canonical app registry for release orchestration

Compatibility note:

- Existing automation still consumes `apps.json` today.
- During migration, `apps.yaml` is generated from `apps.json` and reviewed.
