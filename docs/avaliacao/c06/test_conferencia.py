"""Contraprovas da conferência posterior, sempre em cópias temporárias."""
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("c06_conferencia", Path(__file__).with_name("conferir_evidencias.py"))
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def test_lote_original():
    report = CHECKER.verify(CHECKER.DEFAULT_BATCH)
    assert report["valido"]
    assert report["resumo"]["observacoes_com_relato_em_logs"] == ["D04-R1", "D06-R1", "D04-R2", "D06-R2"]
    assert report["resumo"]["http"] == 12


@pytest.mark.parametrize("mutation,expected_check", [
    ("fonte", "sha256:copia:app/adapters/prompts.py"),
    ("pedido", "D05-R1:corpo integral reconstruido"),
    ("diagnostico", "D06-R1:localizacoes recalculadas"),
])
def test_rejeita_evidencia_adulterada(tmp_path, mutation, expected_check):
    batch = tmp_path / "lote"
    shutil.copytree(CHECKER.DEFAULT_BATCH, batch)
    if mutation == "fonte":
        with (batch / "fontes/app/adapters/prompts.py").open("ab") as handle:
            handle.write(b"\n# alteracao posterior\n")
    else:
        path = batch / ("D05-R1.json" if mutation == "pedido" else "D06-R1.json")
        row = json.loads(path.read_text(encoding="utf-8"))
        if mutation == "pedido":
            row["http"][0]["corpo"]["messages"][0]["content"] += " CAMPO_EXTRA"
        else:
            row["localizacoes"]["logs"]["relato"] = []
        path.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
    report = CHECKER.verify(batch)
    assert not report["valido"]
    assert {"verificacao": expected_check, "aprovada": False} in report["verificacoes"]
