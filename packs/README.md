# Decision packs

A pack is everything Fork needs for one kind of decision. Owner: Person B (Engine).

| File | Used by | What it is |
|---|---|---|
| `defaults.json` | template model, A4 spec builder | Fallback values for anything the documents and interview don't give, each with `source_ref` ("illustrative default" when unsourced) |
| `questions.json` | A4 interview | At most 5 questions; code picks the next one, Super only rewords it |
| `template_model.py` | fallback + example in Ultra's prompt | Hand-written `simulate()` |
| `golden/checks.py` | tests here and in the sandbox | Golden values from the hand-worked oracles + invariant checks |
| `golden/test_golden.py` | sandbox | Copied next to Ultra's `model.py`; never written by Ultra |
| `widgets.json` | Face (C) | Which metrics and cards the results screens show |

## Model interface (template and agent-written models are identical)

```python
def simulate(option_id: str, spec: dict, rng: np.random.Generator, n: int) -> dict:
    return {
        "cash_in_hand": ...,  # (n, quarters) cumulative money at each quarter end
        "metrics": {...},  # name -> (n,) array; must include spec["metrics"]["primary"]
        "story": {...},  # name -> (n,) array of raw facts for hover stories
    }
```

- `spec` is the Decision Spec as a dict (`DecisionSpec.model_dump()`).
- Month 1 is April (start of the financial year). Quarters line up with `Results.x_points`.
- Vectorised NumPy only: loops over months or years are fine, loops over futures are not.
- Common random numbers: draw every uncertain input through `packs.common.SpecView`
  (`s.draw(name)` / `s.rng(name)`). The runner seeds A and B identically per shard, so a
  shared variable has the same value in future #i for both options.
- No network, no file writes. 10,000 futures in under 5 seconds (template: ~0.15 s).

## Running the golden checks

```bash
pytest -q tests/test_offer_xray_pack.py     # template model, in the repo
pytest -q test_golden.py                     # in the sandbox, against model.py
```
