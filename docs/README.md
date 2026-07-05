# FINN. Early Default Prediction — Documentation

## Index

| Doc | Description |
|-----|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Early-warning pipeline, 12-month labels, dual models |
| [EARLY_WARNING.md](EARLY_WARNING.md) | Business case: 16–22% → 90%, RM workflow |
| [DATA_SOURCES.md](DATA_SOURCES.md) | Structured + unstructured sources |
| [CONNECTOR_INTEGRATION.md](CONNECTOR_INTEGRATION.md) | CBS loan tape, bureau, collections CRM |
| [CODE_GUIDE.md](CODE_GUIDE.md) | Code layout |
| [NTC_MSME.md](NTC_MSME.md) | NTC MSME context (alt-data path) |

## Summary

FINN. Early Default Prediction flags **MSME loan stress 12 months ahead** using:

1. **Collection payment timing** — DPD, EMI lead days, bounces, PTP breaks
2. **Bureau other-loan behaviour** — how promoter pays non-IDBI facilities
3. **NTC alt-data** — GST, UPI, EPFO, AA when no bureau score
4. **Unstructured text conversion** — reviews, news, RM notes → numeric stress features

Two models: **structured-only baseline (~18%)** vs **full model with collections + NLP (~90%)** on synthetic demo data.
