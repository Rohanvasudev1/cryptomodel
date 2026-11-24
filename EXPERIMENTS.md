# Experiment log

Add one entry per run, newest first. Record failed runs too. The ablation tables in the paper come from this file.

**Rule.** Every session that runs anything (a trial, labeling, training or evaluation) adds an entry here in the same PR; the manager rejects a PR that runs something without one. Write the hypothesis and pass threshold before looking at the results, copying them from the phase gate where one applies. The full rules are in "How we run experiments" in `PLAN.md`.

## Template

```text
Run ID:
Date:
Phase:
Question this run answers:
Hypothesis (pre-registered, written before the results):
Pass threshold (from the PLAN.md gate, or set here before the run):

Data snapshot date:
Pretraining cutoff date:
Train, validation and test periods:
Split (time split by default; say if not):
Label and label version:
Base rate (per label and horizon):
Code commit:
Config file:
Seeds:
Machine:

Model size:
Objectives:
Wall-clock time:

Results:
  Metric, value (mean and 95% interval over seeds), base rate, compared with which baseline

What changed from the previous run:
Outcome (pass, fail or inconclusive, against the threshold above):
Conclusion:
Decision taken (and the decision-log entry, if any):
Next step:
```

## Runs

None yet.
