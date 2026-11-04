from datetime import date, datetime
from pathlib import Path

import polars as pl

from polars_hprimxml import etats_patient_to_hprimxml

EXPECTED = Path(__file__).parent / "expected" / "etats_patient.xml"


def test_each_row_becomes_one_evenements_serveur_etats_patient_message():
    df = pl.DataFrame(
        {
            "identifiant_message": ["00001_esep"],
            "ipp": ["123456789"],
            "confidentiel": ["non"],
            "sexe": ["M"],
            "nom_usuel": ["SANDWICK"],
            "prenom": ["JOHN"],
            "date_naissance": [date(1970, 1, 1)],
            "nda": ["987654321"],
            "prive": ["non"],
            "date_entree": [datetime(2024, 1, 1, 8, 0)],
            "uf_responsable": ["4321"],
            "id_intervention": ["000000000001"],
            "uf_intervention": ["4321"],
            "action": ["creation"],
            "type_diagnostic": ["dp"],
            "code_cim10": ["Z511"],
            "date_action": [datetime(2024, 1, 1, 8, 10)],
        }
    )

    messages = etats_patient_to_hprimxml(
        df, sender="TEST", produced_at=datetime(2024, 1, 1, 1, 1, 1)
    )

    assert messages == [EXPECTED.read_text(encoding="utf-8")]
