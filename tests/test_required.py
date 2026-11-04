from functools import partial

import polars as pl
import pytest

from polars_hprimxml import (
    actes_to_hprimxml,
    etats_patient_to_hprimxml,
    pmsi_to_hprimxml,
)


@pytest.mark.parametrize(
    "to_hprimxml",
    [
        actes_to_hprimxml,
        etats_patient_to_hprimxml,
        partial(pmsi_to_hprimxml, content="dp_dr"),
        partial(pmsi_to_hprimxml, content="das"),
        partial(pmsi_to_hprimxml, content="actes"),
    ],
    ids=["actes", "etats_patient", "pmsi_dp_dr", "pmsi_das", "pmsi_actes"],
)
@pytest.mark.parametrize(
    "df",
    [
        pl.DataFrame({"ipp": ["123456789"]}),
        pl.DataFrame({"ipp": ["123456789"], "nda": [None]}),
    ],
    ids=["absente", "nulle"],
)
def test_missing_or_null_required_column_raises(to_hprimxml, df):
    with pytest.raises(ValueError, match="nda"):
        to_hprimxml(df, sender="TEST")


def test_unknown_pmsi_content_raises():
    with pytest.raises(ValueError, match="content"):
        pmsi_to_hprimxml(
            pl.DataFrame({"ipp": ["123456789"]}), sender="TEST", content="dad"
        )
