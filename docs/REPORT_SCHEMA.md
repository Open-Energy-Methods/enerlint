# Machine-readable verification reports (schema v0.1.0)

**Status:** alpha reporting contract · 27 October 2026. This is software interoperability documentation, not a certification, external peer review, or validation of the reported physical model.

The published machine-readable contract is [`report-v0.1.0.schema.json`](../src/enerlint/schemas/report-v0.1.0.schema.json), validated with JSON Schema Draft 2020-12. It is included in installed EnerLint wheel and source distributions and can be accessed with Python's `importlib.resources`.

## Versioning and compatibility

- `schema_version = "0.1.0"` identifies the report's data contract. The alpha retains the **same field and version** used in the current API. For the current alpha, the input JSON contract and report output contract both use the literal `0.1.0`. They are **not automatically interchangeable formats**.
- `enerlint_version = "0.1.0a0"` identifies the software version that generated the report; it is a separate identifier.
- The existing check's `name` is the stable **check ID within this schema version**. For example: `(schema_version="0.1.0", name="steady_first_law")`. We have **not** introduced a competing `check_id` field or silently renamed existing checks.
- A future breaking change to a check's meaning, required fields, or ID requires a **new report schema version, a new schema file and explicit migration notes**. Existing `v0.1.0` records remain readable under the `v0.1.0` schema. Do not relabel old output as new-format data.

These check IDs are currently frozen:

| Case kind | Mandatory check | Optional check |
|---|---|---|
| `steady_control_volume` | `steady_mass_closure`; `steady_first_law` | None |
| `storage_interval` | `storage_energy_closure` | `storage_capacity` |

All four check IDs occur as report entries in their case type; `storage_capacity` can be marked `NOT_CHECKED` if capacity is absent. The schema rejects duplicates, missing mandatory checks and mismatched check kinds for a successfully parsed case.

## Meaning of statuses

| Status | Scope | Required interpretation |
|---|---|---|
| `PASS_IN_SCOPE` | Whole report | At least one check was evaluated and passed, no evaluated check failed; **some optional checks may be `NOT_CHECKED`** |
| `FAIL` | Whole report | At least one evaluated check violates its stated threshold |
| `INVALID_INPUT` | Whole report | The input could not be read, parsed or evaluated under the contract; **no physical checks were performed** |
| `PASS` | Individual check | This one measured residual satisfies its threshold |
| `FAIL` | Individual check | This one measured residual violates its threshold |
| `NOT_CHECKED` | Individual check | No calculation performed (currently only optional storage capacity); `residual`, `scale`, `threshold` and `unit` are `null` |

**`NOT_CHECKED` is neither PASS nor FAIL.** A report with `PASS_IN_SCOPE` and a `NOT_CHECKED` capacity must not be described as storage-capacity verified.

A `PASS_IN_SCOPE` report must contain at least one evaluated `PASS` and zero `FAIL` checks. A `FAIL` report must contain at least one failing check. The schema disallows re-labeling a skipped check as an evaluated success while keeping null numerical fields.

## Report fields

All report variants have these keys (no undocumented extra keys in schema v0.1.0):

| Field | Physical report (`PASS_IN_SCOPE`/`FAIL`) | Rejected input (`INVALID_INPUT`) |
|---|---|---|
| `schema_version` | `"0.1.0"` | `"0.1.0"` |
| `enerlint_version` | Software release string | Software release string |
| `case_id`, `kind` | Nonempty declared case metadata; supported kind | `null` (untrusted) |
| `source_fingerprint_sha256` | SHA-256 of canonical JSON object, not an authenticity guarantee | `null` |
| `evidence_class`, `declared_source` | **Author-declared**, not independently authenticated | `null` |
| `checks` | Ordered check objects, with stable IDs and numeric residual/threshold for evaluated checks | Empty array |
| `assumptions`, `limitations` | Explicit lists of scope and exclusions | Empty assumptions; limitation stating no physical check |
| `errors` | Empty array | At least one human-readable reason for rejection |

The record's numerical `scale` and `threshold` document the actual decision rule applied to the declared inputs, not the model's uncertainty budget. See [verification contract](VERIFICATION_CONTRACT.md) and [numeric tolerance review](NUMERICAL_TOLERANCE_POLICY.md).

## Using the CLI

From a clean checkout with EnerLint installed:

```bash
# Output file contains a complete versioned PASS_IN_SCOPE or FAIL report.
enerlint check examples/steady_compressor.json --output reports/compressor.json

# If the input is malformed/invalid, use --output to keep the rejection
# as structured JSON with status INVALID_INPUT and no fabricated provenance.
enerlint check broken-input.json --output reports/broken.json
```

CLI exit codes are unchanged: **0** for scoped success, **1** for failed physical checks, **2** for invalid input or report writing errors. On invalid input, the CLI still writes `INVALID_INPUT: ...` to stderr. A valid `INVALID_INPUT` JSON artifact is created **only when `--output` is specified and writing succeeds**; without it, the CLI retains its prior stderr-only behavior. A failed output write is an I/O failure and cannot be treated as a scientific report.

In the Python API, `VerificationReport.as_dict()` and `InvalidInputReport.as_dict()` return JSON-native list/dict values (not Python tuples for arrays), and `serialize_report(report)` emits deterministic UTF-8 JSON text with sorted keys, a two-space indent and a trailing newline. No timestamps, random identifiers or machine paths are added to **successful** verification reports. This gives the same serialized result for unchanged report objects; it does **not** make the external source or physical model trustworthy.

## Validating outside the package

In a development environment (`pip install -e ".[dev]"`), JSON Schema validation is provided by the optional `jsonschema` development dependency:

```python
import json
from importlib.resources import files
from jsonschema import Draft202012Validator

schema = json.loads(
    files("enerlint").joinpath("schemas", "report-v0.1.0.schema.json")
    .read_text(encoding="utf-8")
)
Draft202012Validator.check_schema(schema)
with open("reports/compressor.json", encoding="utf-8") as stream:
    Draft202012Validator(schema).validate(json.load(stream))
```

The **EnerLint core runtime does not depend on `jsonschema`**. Reports can be validated by other JSON Schema Draft 2020-12 implementations. No custom trust or approval mechanism is implied.

## Migration and reproducibility checks

- `tests/test_report_schema.py` validates all four original example reports, an intentional physical failure, an optional omitted capacity, rejected inputs, unknown fields and check IDs, and status/check contradictions.
- `scripts/verify_distributions.py` confirms the schema is **included** in installed wheels and sdists and that the installed CLI can produce a structured rejected-input report outside the source checkout.
- The repository's [Scientific core CI](../.github/workflows/ci.yml) runs these checks on supported Python/OS combinations.
- Changes to report semantics require new focused tests, a change record, and a schema migration plan. Do not silently mutate the existing v0.1.0 JSON Schema.

**Known limitations:** external data provenance is declared, not authenticated; input hashes are not electronic signatures; a conservation pass is not physical validation; changes in interpreter float formatting or I/O errors may change text/error messages across environments. `INVALID_INPUT` is not a numerical failure of the source engineering model.
