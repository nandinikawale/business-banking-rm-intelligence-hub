import shutil

from streamlit_app.data import fingerprint, load_options


def test_changed_csv_invalidates_cached_options(ui_dataset, tmp_path):
    directory = tmp_path / "csv"
    shutil.copytree(ui_dataset[0], directory)
    before = fingerprint(directory)
    original = load_options(str(directory), before)
    customers = ui_dataset[1]["customers"].copy()
    customers.loc[0, "business_name"] = "Fictional refreshed fixture business"
    customers.to_csv(directory / "customers.csv", index=False)
    after = fingerprint(directory)
    assert before != after
    refreshed = load_options(str(directory), after)
    assert (
        refreshed["customers"].iloc[0].business_name
        == "Fictional refreshed fixture business"
    )
    assert (
        original["customers"].iloc[0].business_name
        != refreshed["customers"].iloc[0].business_name
    )
