import csv
import io

import pandas as pd

from rm_hub.services.opportunities import filter_opportunities, opportunities
from streamlit_app.exports import opportunity_worklist, worklist_csv


def selected_worklist(repository):
    signals = filter_opportunities(
        opportunities(repository), "Cross-sell", "credit_card"
    )
    return signals.merge(
        repository.customers()[["customer_id", "industry", "region"]],
        on="customer_id",
        validate="many_to_one",
    )


def test_export_matches_filtered_worklist_and_context(repository):
    signals = selected_worklist(repository)
    display = opportunity_worklist(signals)
    payload = worklist_csv(display)
    assert payload.startswith(b"\xef\xbb\xbf")
    parsed = pd.read_csv(io.BytesIO(payload))
    assert len(parsed) == len(signals)
    assert parsed["Customer ID"].tolist() == signals.customer_id.tolist()
    assert parsed["Reporting month"].eq("December 2025").all()
    assert parsed["Potential product"].eq("Credit card").all()
    assert parsed["Signal type"].eq("Cross-sell").all()
    assert parsed["Industry"].notna().all()
    assert parsed["Region"].notna().all()
    assert parsed["Supporting observation"].tolist() == signals.reason.tolist()


def test_csv_quotes_unicode_newlines_and_neutralizes_formulas(repository):
    display = opportunity_worklist(selected_worklist(repository)).iloc[:1].copy()
    display.loc[display.index[0], "Fictional business"] = '=HYPERLINK("example")'
    display.loc[display.index[0], "Supporting observation"] = (
        "Fictional café, example\nSecond line"
    )
    display.loc[display.index[0], "Deposit change (%)"] = -25.5
    parsed = list(
        csv.DictReader(io.StringIO(worklist_csv(display).decode("utf-8-sig")))
    )
    assert parsed[0]["Fictional business"].startswith("'=")
    assert parsed[0]["Supporting observation"] == "Fictional café, example\nSecond line"
    assert parsed[0]["Deposit change (%)"] == "-25.50"
    assert display.iloc[0]["Fictional business"].startswith("=")


def test_empty_export_has_headers(repository):
    display = opportunity_worklist(selected_worklist(repository).iloc[:0])
    parsed = pd.read_csv(io.BytesIO(worklist_csv(display)))
    assert parsed.empty
    assert parsed.columns.tolist() == display.columns.tolist()
