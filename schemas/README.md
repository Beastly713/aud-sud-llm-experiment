# Exported JSON schemas

Run `python3 -m src.schema_export` in the pinned environment to materialize the
versioned Pydantic JSON schemas for `Scenario`, `Question`, `CommonAnswer`,
`GoldRecord`, `InvestigationPlan` and `EvidenceBundle`. The command is deterministic;
the current workspace does not include generated schemas because the pinned
Pydantic dependency is not installed.

