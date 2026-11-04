from datetime import date, datetime
from pathlib import Path

import polars as pl

from polars_hprimxml import actes_to_hprimxml

EXPECTED = Path(__file__).parent / "expected" / "actes.xml"


def test_each_row_becomes_one_evenements_serveur_actes_message():
    df = pl.DataFrame(
        {
            "identifiant_message": ["00001_acte"],
            "ipp": ["123456789"],
            "sexe": ["M"],
            "nom_usuel": ["SANDWICK"],
            "prenom": ["JOHN"],
            "date_naissance": [date(1970, 1, 1)],
            "nda": ["987654321"],
            "prive": ["non"],
            "date_entree": [datetime(2024, 1, 1, 8, 0)],
            "uf_responsable": ["4321"],
            "id_intervention": ["000000000001"],
            "debut_intervention": [datetime(2024, 1, 1, 8, 10)],
            "fin_intervention": [datetime(2024, 1, 1, 9, 0)],
            "uf_intervention": ["4321"],
            "date_prescription": [datetime(2023, 12, 25, 2, 30)],
            "uf_demande": ["4321"],
            "action": ["creation"],
            "facturable": ["oui"],
            "valide": ["oui"],
            "id_acte": ["121212"],
            "code_acte": ["EBLA003"],
            "code_activite": ["1"],
            "code_phase": ["0"],
            "date_execution": [datetime(2024, 1, 1, 8, 10)],
            "medecin_executant": ["01234567"],
            "uf_executant": ["4321"],
            "quantite": [1],
        }
    )

    messages = actes_to_hprimxml(
        df, sender="TEST", expect_ack=True, produced_at=datetime(2024, 1, 1, 1, 1, 1)
    )

    assert messages == [EXPECTED.read_text(encoding="utf-8")]
