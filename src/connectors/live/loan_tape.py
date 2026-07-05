"""Loan tape connector — CBS/core banking loan + collections data."""

from __future__ import annotations

from src.connectors.base import BaseConnector


class LoanTapeConnector(BaseConnector):
    """Production: CBS loan tape API. PoC: reads loan_book + collections from profile JSON."""

    source_name = "loan_tape"

    def fetch(self, profile: dict) -> dict:
        return {
            "loan_book": profile.get("loan_book", {}),
            "collections": profile.get("collections", {}),
            "observation_labels": profile.get("observation_labels", []),
        }
