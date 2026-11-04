from datetime import date, datetime
from pathlib import Path

import polars as pl
import pytest

from polars_hprimxml import pmsi_to_hprimxml

EXPECTED = Path(__file__).parent / "expected"


@pytest.mark.parametrize("content", ["dp_dr", "das", "actes"])
def test_each_row_injects_only_its_content_into_one_rum(content):
    # La ligne porte les trois contenus : seul celui demandé est écrit.
    df = pl.DataFrame(
        {
            "identifiant_message": ["00001_pmsi"],
            "ipp": ["123456789"],
            "anonyme": ["non"],
            "confidentiel": ["non"],
            "sexe": ["M"],
            "nom_usuel": ["SANDWICK"],
            "nom_naissance": ["SANDWICK"],
            "prenom": ["JOHN"],
            "date_naissance": [date(1970, 1, 1)],
            "nda": ["987654321"],
            "prive": ["non"],
            "date_entree": [datetime(2024, 1, 1, 8, 0)],
            "mode_entree": ["8"],
            "uf_responsable": ["4321"],
            "id_rss": ["0"],
            "action": ["creation"],
            "classant": ["non"],
            "prestation_inter_etablissement_a": ["non"],
            "date_action": [datetime(2024, 1, 1, 8, 10)],
            "id_rum": ["pmsi_00001"],
            "medecin_responsable": ["01234567"],
            "um": ["4321"],
            "date_entree_um": [datetime(2024, 1, 1, 8, 0)],
            "mode_entree_um": ["8"],
            "dp": ["Z511"],
            "dr": ["C10"],
            "das": ["E119"],
            "externe": ["non"],
            "remboursement_exceptionnel": ["non"],
            "code_acte": ["EBLA003"],
            "code_phase": ["0"],
            "code_activite": ["1"],
            "quantite": [1],
            "date_realisation": [datetime(2024, 1, 1, 8, 10)],
        }
    )

    messages = pmsi_to_hprimxml(
        df,
        sender="TEST",
        content=content,
        receiver="PMSI",
        expect_ack=True,
        produced_at=datetime(2024, 1, 1, 1, 1, 1),
    )

    expected = (EXPECTED / f"pmsi_{content}.xml").read_text(encoding="utf-8")
    assert messages == [expected]
