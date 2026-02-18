# /validate-outputs

Check the quality of existing outputs without re-running any workflow. Runs structural verification and quote validation against files in `05-outputs/`.

## Usage

```
/validate-outputs                                  # validate all outputs in 05-outputs/
/validate-outputs <filename>                       # validate one specific output file
```

Examples:
- `/validate-outputs`
- `/validate-outputs participant-archetypes.md`

Read-only — does not regenerate or modify any output file.

## Output-to-verify script mapping

| Output file | Verify script |
|---|---|
| `research-question-analysis.md` | `02-workflows/analyze-by-research-question/verify.py` |
| `participant-archetypes.md` | `02-workflows/analyze-and-create-archetypes/verify.py` |
| `vc-pitch.md` | `02-workflows/analyze-by-vc-pitch/verify.py` |
| `recruitment-screener.md` | `02-workflows/build-screener-for-recruitment/verify.py` |
| `assess-vc-pitch-by-three-amigos.md` | `02-workflows/assess-vc-pitch-by-three-amigos/verify.py` |
| `personas-from-archetypes/` (folder) | `02-workflows/create-personas-from-archetypes/verify.py` |

## Procedure

### Step 1: Identify targets

If a filename argument was provided, confirm it exists in `05-outputs/` before proceeding.

If no argument was provided, list all files in `05-outputs/` (including any subfolders). Exclude any files not matching a known output (see mapping table above).

### Step 2: Run structural verification

For each target output that has a corresponding `verify.py`:

```
python3 02-workflows/<workflow>/verify.py 05-outputs/<output-file> [extra args if needed]
```

Capture the exit code and output. Record `PASS` or `FAIL` per file.

If no `verify.py` exists for a given output, note it as "no verifier — skipped".

### Step 3: Run quote validation

For each output that contains quoted participant text (archetypes, research-question-analysis, personas, vc-pitch), run the `quote-validation-reviewer` agent:

- `output_file`: the output file path
- `transcripts_folder`: `04-process/translated`

This checks that quotes in the output match source transcripts verbatim.

### Step 4: Report results

For each output validated, show:

| Output file | Structural verify | Quote validation |
|---|---|---|
| `participant-archetypes.md` | PASS | WARN (2 items) |
| `research-question-analysis.md` | PASS | PASS |
| `vc-pitch.md` | FAIL | — |

For any WARN or FAIL result, list the issues returned by the verifier or quote reviewer.

End with a one-line summary: how many outputs were checked, how many passed, how many need attention.
