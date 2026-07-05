"""Mock data connectors for all alternative data sources."""

from src.connectors.base import BaseConnector
from src.connectors.live.loan_tape import LoanTapeConnector
from src.utils.constants import MACRO_INDICATORS, SECTOR_GROWTH


class GSTConnector(BaseConnector):
    source_name = "gst"

    def fetch(self, profile: dict) -> dict:
        return profile["gst"]


class UPIConnector(BaseConnector):
    source_name = "upi"

    def fetch(self, profile: dict) -> dict:
        return profile["upi"]


class AAConnector(BaseConnector):
    source_name = "aa"

    def fetch(self, profile: dict) -> dict:
        return profile["aa"]


class EPFOConnector(BaseConnector):
    source_name = "epfo"

    def fetch(self, profile: dict) -> dict:
        return profile["epfo"]


class GoogleConnector(BaseConnector):
    source_name = "google"

    def fetch(self, profile: dict) -> dict:
        return profile["google"]


class BureauConnector(BaseConnector):
    source_name = "bureau"

    def fetch(self, profile: dict) -> dict:
        return profile["bureau"]


class CourtsConnector(BaseConnector):
    source_name = "courts"

    def fetch(self, profile: dict) -> dict:
        return profile["courts"]


class ElectricityConnector(BaseConnector):
    source_name = "electricity"

    def fetch(self, profile: dict) -> dict:
        return profile["electricity"]


class MacroConnector(BaseConnector):
    source_name = "macro"

    def fetch(self, profile: dict) -> dict:
        sector = profile["sector"]
        data = dict(MACRO_INDICATORS)
        data["sector_growth_pct"] = SECTOR_GROWTH.get(sector, 5.0)
        data.update(profile["macro"])
        data["sector"] = sector
        return data


class InvestmentConnector(BaseConnector):
    source_name = "investment"

    def fetch(self, profile: dict) -> dict:
        return profile["investment"]


ALL_CONNECTORS = {
    "loan_tape": LoanTapeConnector(),
    "gst": GSTConnector(),
    "upi": UPIConnector(),
    "aa": AAConnector(),
    "epfo": EPFOConnector(),
    "google": GoogleConnector(),
    "bureau": BureauConnector(),
    "courts": CourtsConnector(),
    "electricity": ElectricityConnector(),
    "macro": MacroConnector(),
    "investment": InvestmentConnector(),
}


def fetch_all_sources(msme_id: str, sources: list[str] | None = None) -> dict:
    sources = sources or list(ALL_CONNECTORS.keys())
    results = {}
    for name in sources:
        if name in ALL_CONNECTORS:
            results[name] = ALL_CONNECTORS[name].connect(msme_id)
    return results
