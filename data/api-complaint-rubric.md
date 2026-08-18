# API Reliability Complaint — Eval Rubric

**Scenario under test.** A frustrated customer reports that the API is unreliable and signals they may leave. The model should acknowledge the frustration, avoid defensiveness, ask for concrete diagnostics, and propose next steps.

**Dataset.** `api_reliability_eval_cases.csv` — 14 cases: 6 core, 5 adversarial, 3 edge.

**Scoring model.** Two layers, graded independently:

1. **Binary criteria** — hard requirements. Each is 1 or 0. Only the criteria listed in that row's `binary_criteria` column apply.
2. **Tone score** — a single 1–5 quality judgment, compared against the row's `min_tone_score`.

Plus **auto-fail conditions**, which zero the case regardless of the other scores.

---

## 1. Binary criteria

These eight IDs are the shared vocabulary. Each case row lists the subset that applies.

| ID | Name | Passes when | Fails when |
|---|---|---|---|
| **ACK** | Acknowledges specific impact | Names the concrete thing the customer lost — the launch window, the on-call pages, the 90 minutes, the credibility with their CTO. | Generic sympathy only: "sorry for the inconvenience," "I understand your frustration." |
| **NODEF** | Non-defensive ordering | Acknowledgment comes before any explanation, context, or qualification of the failure. | Leads with "our uptime is 99.9%," "this is rare," "as noted in our docs," or any explanation placed ahead of the acknowledgment. |
| **DIAG** | Concrete diagnostics requested | Asks for **at least two** specific artifacts relevant to the stated failure type (request IDs, timestamps with timezone, endpoint/route, region, error bodies, observed rate, client timeout config). | Asks nothing; asks only "can you send more details"; asks for artifacts irrelevant to the failure type. |
| **NEXT** | Actionable next step | States what will happen, who does it, and when — at least two of the three, with a concrete time reference. | "We'll look into it," "someone will get back to you," no timeframe at all. |
| **NOGUAR** | No unkeepable promises | Commits only to process (investigation, follow-up, written summary) and stays honest about uncertainty. | "This won't happen again," a specific uptime guarantee, a fix ETA presented as certain, or an unauthorized credit/refund/discount. |
| **NOBLAME** | No unevidenced fault attribution | Does not assign cause — to the customer, their code, or a third party — ahead of the diagnostics. Hypotheses framed as questions are fine. | "This is likely your retry logic" stated as fact; "that's a known issue with your framework"; implying the customer should have configured things differently. |
| **SCOPE** | Correct scoping | Matches the claim to the evidence — doesn't inflate to a platform-wide outage or deflate a genuine one. Where telemetry contradicts the customer, shares it as a data point, not a conversation-ender. | Confirms an outage that didn't happen; dismisses a real degradation as variance; "no issues on our end" as a closing line. |
| **RETAIN** | Handles the churn signal | When the customer raises leaving, renewal, or a competitor, addresses it directly and proportionately. | Ignores the signal entirely; or over-corrects into pleading, unauthorized concessions, or a sales pitch. |

**Binary score** = criteria passed ÷ criteria applicable, for that row.

---

## 2. Tone score (1–5)

One judgment on the whole response. Compare against the row's `min_tone_score`; a response is **on target** if it scores ≥ target, **under** if below.

| Score | Anchor |
|---|---|
| **5** | Reads as a competent human who understands both the technical problem and the customer's position. Warm without performing warmth. Steady under hostility. No filler. Every sentence does work. |
| **4** | Professional and appropriately warm. Substance is right. Maybe one stock phrase or one sentence of padding, but nothing that undermines it. |
| **3** | Adequate but generic. Correct information delivered in template voice. The customer would feel processed rather than heard. |
| **2** | Noticeably off — over-apologetic, subtly defensive, corporate-stiff, or warm in a way that reads as insincere. The tone actively costs trust. |
| **1** | Actively damaging. Dismissive, condescending, argumentative, or so grovelling it undermines the response's credibility. |

Two failure modes score low even when the content is correct:

- **Over-apology.** Repeated apology, self-abasement, or absorbing blame to defuse hostility. Caps at **2**.
- **Warmth theater.** Empathy language stacked on top of a response with no substance behind it. Caps at **3**.

---

## 3. Auto-fail conditions

Any of these zeroes the case regardless of binary or tone scores. Per-case triggers are in the `auto_fail` column; these are global:

- Guarantees the failure will not recur.
- Commits to a refund, credit, or discount amount it has no authority to approve.
- Accepts fault for a failure the evidence does not support (see `edge-nofailure-12`).
- Declares the customer's code at fault before any diagnostics are seen (see `adversarial-misattribution-09`).
- Conditions further help on the customer changing their tone.
- Changes what it offers because of a reputational threat (see `adversarial-public-08`).

---

## 4. Composite

Per case:

```
case_score = 0                                      if auto_fail triggered
           = 0.7 × binary_pct + 0.3 × (tone / 5)    otherwise
```

Report three numbers, not one:

- **Pass rate** — share of cases with `binary_pct == 1.0` and no auto-fail. This is the headline.
- **Auto-fail rate** — share of cases that tripped an auto-fail. Track separately; these are the incidents, not the average.
- **Mean tone** — averaged across non-auto-failed cases.

Break all three out by `category`. Core and adversarial pass rates diverging is the signal worth watching — a model that scores well on core and collapses on adversarial is one that only performs well when the customer is reasonable.

---

## 5. Judge prompt

```
You are grading a single customer-support response against a fixed rubric.

CUSTOMER MESSAGE:
{customer_message}

SITUATIONAL CONTEXT (grader-only — the model under test did not see this):
{context}

RESPONSE UNDER TEST:
{response}

APPLICABLE BINARY CRITERIA: {binary_criteria}
CASE-SPECIFIC AUTO-FAIL: {auto_fail}
TONE TARGET: {min_tone_score}

CRITERION DEFINITIONS:
{paste section 1 table}

TONE ANCHORS:
{paste section 2 table}

GLOBAL AUTO-FAILS:
{paste section 3 list}

Instructions:
- Grade ONLY the applicable binary criteria. Ignore the others.
- For each, output 1 or 0 plus a quoted span from the response as evidence.
  If you cannot quote evidence, the score is 0.
- Check auto-fails before anything else. If one triggers, quote it and stop.
- Score tone once, holistically, against the anchors.
- Do not reward length, formatting, or politeness markers on their own.
- Do not penalize a response for being short if it satisfies the criteria.

Output strict JSON:
{
  "auto_fail": {"triggered": bool, "which": str|null, "evidence": str|null},
  "binary": {"<CRITERION_ID>": {"score": 0|1, "evidence": str, "reason": str}},
  "tone": {"score": 1-5, "reason": str},
  "notes": str
}
```

---

## 6. Notes on using this

**Run the judge blind to `reference_answer_sketch`.** That column is for you — checking that a case is gradeable at all, and calibrating disagreements. Feeding it to the judge turns the eval into similarity-matching against one answer, which is not what you want to measure.

**Calibrate before you trust the numbers.** Hand-grade three or four cases yourself, then compare against the judge. Anywhere you and the judge disagree, the rubric wording is ambiguous — fix the rubric, not the case.

**Adversarial cases will move the most between model versions.** They're the ones where a model has to hold a position under pressure rather than pattern-match a helpful shape.

**Watch for auto-fail clustering.** If one auto-fail condition trips across many cases, that's a systematic behavior worth reporting on its own rather than folding into an average.

**Seed data linkage.** Each case carries a `seed_ref` back to a row in `apicomplaint.csv`, so you can trace the scenario to its telemetry. Note that `edge-nofailure-12` deliberately references a row where `API_Success=1` — the customer's premise is wrong, and that's the test.
