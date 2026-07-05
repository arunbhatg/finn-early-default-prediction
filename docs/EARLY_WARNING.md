# Early Warning — Business Case

## The gap

| Approach | Accuracy (typical) | What it uses |
|----------|-------------------|--------------|
| Structured-only (legacy) | 16–22% | Bureau snapshot, loan master, static GST |
| **FINN. full model** | **≥90%** (PoC) | + collections timing + bureau other-loans + NLP text conversion |

## Stress definition

A loan is labelled **stressed within 12 months** if any of:

- DPD ≥ 30 for 2+ consecutive months on the facility under review
- NPA / restructuring event
- Simulated default in synthetic demo data

## Feature pillars

### 1. Collection payment timing (structured)

- EMI on-time rate (6m), max/avg DPD, payment lead days
- Bounce count, partial payments, broken promise-to-pay
- Follow-up call volume from collections CRM

### 2. Bureau — other loan payments

For non-NTC promoters, bureau enriches with **how they pay other lenders**:

- Per-loan EMI on-time rate, DPD history (12m), bounce rate
- Aggregated: `bureau_other_emi_on_time_rate`, `bureau_other_max_dpd_12m`

### 3. NTC alt-data (when bureau is thin)

When `is_ntc=true`, model switches to:

- GST filing compliance proxy
- UPI volume stability
- EPFO / AA bounce proxies
- No CIBIL score required

### 4. Unstructured → structured conversion

Raw text is converted to numeric stress features:

| Source | Converted feature |
|--------|-------------------|
| Google reviews | `review_stress_score` |
| News headlines/snippets | `news_stress_score` |
| RM call notes | `rm_note_stress_score` |
| GST notices/remarks | `gst_remark_stress_score` |
| Collection field notes | `collection_note_stress_score` |
| All combined | `composite_text_stress_score` |

Keyword-weighted density scoring (no heavy NLP deps) — production path: fine-tuned classifier or LLM extraction.

## RM / collections workflow

1. **Portfolio scan** — rank loans by 12m stress probability
2. **Assessment** — review payment timing charts + bureau other-loan table
3. **Intervene** — Critical/High bands trigger field visit or restructuring
4. **Signals tab** — read unstructured evidence behind the score

## Production path

- Replace synthetic `loan_book` / `collections` JSON with **CBS loan tape** connector
- Refresh bureau other-loan tradelines nightly
- Pipe collections CRM notes into unstructured corpus
- Retrain on 3+ years of labelled portfolio outcomes with out-of-time validation
