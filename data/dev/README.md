# Development dataset

The five authored scenarios and 25 questions are defined in `src/devdata.py` so
the same validated objects feed fixture tests, the development runner and the
worksheet export without a second generated source of truth. They are D01–D05,
one Q1, one Q2, one Q3 and two Q4 questions per scenario. No test/held-out records
are present in this repository.

`data/dev/fixtures/` and `data/dev/questions/` are reserved for materialized JSON
exports when the pinned environment is available; the canonical in-process dataset
is already executable through `evaluation.gold_validate` and the development tests.

