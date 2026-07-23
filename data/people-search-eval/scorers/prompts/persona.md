# Braintrust UI scorer — persona-switched people-search judge

One judge for all 6 personas. It reads the persona from the row and applies the matching rubric.

| Setting | Value |
|---------|--------|
| Output type | **Score** |
| Messages | **One User message** (paste below) |
| Model | `claude-opus-4-6` |
| CoT | On |
| Slug | `people-judge-persona` |

## Choice scores

| Label | Score |
|-------|-------|
| High Value | 1.0 |
| Useful | 0.7 |
| Low Value | 0.3 |
| Failed | 0.0 |

---

You are evaluating people-search API results **on behalf of one specific buyer persona**.

First, read the persona for this query, then apply ONLY that persona's rubric below.

Persona (slug): {{output.judge_persona}}
Persona (label): {{metadata.persona}}
Provider: {{output.provider}} (informational only — score the normalized preview)

Query: {{input.query}}
Query type: {{metadata.query_type}}
Named target: {{output.named_target}}

Error: {{output.error}}
Person count: {{output.person_count}}

Results preview:
{{output.people_preview}}

## Pick the rubric that matches the persona slug

### recruiter — Recruiter / Talent Sourcer
Goal: can you pipeline these people? Assess role fit, seniority, skills, location, career history. NOT hire quality.
High-signal fields: current_title, current_company, location, skills, insights/match summaries.
Low priority: email/phone.

### sdr — SDR / BDR
Goal: can you reach and prospect this person or list? Work email, phone, correct title and company matter most.
High-signal fields: email, phone, displayname, current_title, current_company, profile_url.
Correct person + LinkedIn only (no email) = Useful, not High. Wrong person at right company = Low Value.

### compliance — Background Check / Compliance Analyst
Goal: verify identity and employment. Can you confirm this person works at the stated org with a plausible title?
High-signal fields: displayname, current_company, current_title, confidence/likelihood, profile_url.
Gate: if the returned person is clearly NOT the named target, cap at Low Value regardless of richness.

### journalist — Journalist / Investigative Researcher
Goal: enough background/context to research or write. Employment, affiliations, public footprint, narrative.
High-signal fields: highlight, insights, current_title, current_company, profile_url, summaries.
Low priority: email/phone.

### events — Event Organizer / Community Manager
Goal: can you contact and invite people (alumni, community, speakers)? Contact path + affiliation matter most.
High-signal fields: email, phone, displayname, current_company, location, profile_url.
LinkedIn-only for a named contact = Useful, not High.

### investor — VC / PE / Investor
Goal: assess deal relevance — founding teams, exec bios, prior ventures, authority, employer verification.
High-signal fields: current_title, current_company, highlight, insights, career summaries, profile_url.
Gate: named founder/exec lookups require correct person match before scoring high.

## Score labels (same for every persona)

**High Value (1.0)** — Persona can act immediately; correct, relevant, and rich enough for this use case.

**Useful (0.7)** — Partially actionable: thin fields, some noise, or incomplete — still worth opening.

**Low Value (0.3)** — Wrong people, wrong company, named-person miss, or empty on a query that should return data.

**Failed (0.0)** — Hard API `error`, OR zero results on a named-person `enrichment` query (person + company were specified).

## Decision order

1. Hard `error`? → **Failed**
2. `query_type=enrichment` with a named target and `person_count=0`? → **Failed**
3. Named target present but the returned person is the wrong individual? → **Low Value**
4. People present? → **High Value** vs **Useful** by persona-fit and preview richness
5. Open `search` with zero results? → **Low Value** (niche is still Low, not Failed)

Briefly explain your reasoning (name the persona rubric you applied), then select exactly ONE choice using the provided tool.
