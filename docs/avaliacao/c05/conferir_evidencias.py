"""Conferência posterior da coleta C05, sem inferência ou julgamento semântico."""
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def verify(batch):
    from dotenv import dotenv_values
    from langchain_core.documents import Document

    from app.adapters.prompts import rag_prompt
    from app.adapters.respostas import RESPOSTA_SEM_CONTEXTO, sem_contexto

    checks = {}
    environment = load(batch / "ambiente.json")
    checks["copias_e_fontes_conferem_sha256"] = all(
        digest(batch / "fontes" / name) == expected == digest(ROOT / name)
        for name, expected in environment["sha256"].items())
    snapshot = Path(environment["embeddings_snapshot"])
    checks["pesos_locais_conferem_sha256"] = all(
        digest(snapshot / name) == expected
        for name, expected in environment["embeddings_sha256"].items())
    checks["manifesto_integridade"] = load(batch / "integridade-fontes.json") == {
        "fontes_inalteradas": True, "alteradas": []}
    spec = load(batch / "fontes/docs/avaliacao/c05/casos.json")
    config = load(batch / "configuracao.json")
    listing = load(batch / "modelos-disponiveis.json")
    checks["modelo_configurado_listado"] = listing["status"] == 200 and config["modelo"] in listing["modelos"]
    checks["configuracao_prevista"] = all(config[k] == v for k, v in {
        "temperature": 0.1, "max_tokens": 500, "timeout_s": 60, "max_retries": 2,
        "retriever_k": 10}.items())
    schedule = [(r, c) for r in range(1, spec["repeticoes"] + 1) for c in spec["casos"]]
    expected_ids = [f"{case['id']}-R{r}" for r, case in schedule]
    checks["doze_registros_sem_extras"] = sorted(p.stem for p in batch.glob("P*-R*.json")) == sorted(expected_ids)
    checks["dezessete_documentos_preservados"] = len(list((batch / "fontes/data/servicos").glob("*.txt"))) == 17
    rows = [load(batch / f"{row_id}.json") for row_id in expected_ids]
    details = []
    for (round_number, case), row in zip(schedule, rows):
        # FAISS atribui IDs aos Documents. O serializer do coletor guarda conteúdo
        # e metadados; os IDs permanecem na representação exata do prompt.
        ids = re.findall(r"Document\(id='([0-9a-f-]{36})', metadata=", row["prompt"])
        docs = [Document(id=doc_id, page_content=d["conteudo"], metadata=d["metadados"])
                for doc_id, d in zip(ids, row["contexto"])]
        facts = row["diagnostico_recuperacao"]["trechos_literais"]
        valid = {
            "identidade": row["caso"] == case["id"] and row["rodada"] == round_number
                and row["pergunta"] == case["pergunta"],
            "uma_recuperacao_uma_geracao": row["chamadas_recuperador"] == row["chamadas_gerador"] == 1,
            "dez_chunks_ordenados": [d["indice"] for d in row["contexto"]] == list(range(1, 11)),
            "dez_ids_preservados_no_prompt": len(ids) == len(set(ids)) == len(row["contexto"]) == 10,
            "chunks_constam_nas_fontes": all(d["conteudo"] in (
                batch / "fontes/data/servicos" / Path(d["metadados"]["source"]).name
                ).read_text(encoding="utf-8") for d in row["contexto"]),
            "prompt_reproduzido": row["prompt"] == rag_prompt.invoke({"context": docs, "question": case["pergunta"]}).to_string(),
            "resposta_obtida_sem_erro": row["erro_tipo"] is None and isinstance(row["resposta_original"], str)
                and bool(row["resposta_original"].strip()),
            "adaptacao_nlp": row["saida_nlp"] == (None if sem_contexto(row["resposta_original"]) else row["resposta_original"]),
            "frase_ausencia_conferida": row["frase_ausencia_exata"] == (row["resposta_original"].strip() == RESPOSTA_SEM_CONTEXTO),
            "reconhecimento_ausencia_conferido": row["ausencia_reconhecida"] == sem_contexto(row["resposta_original"]),
            "http_final_200": bool(row["tentativas_http"]) and row["tentativas_http"][-1]["status"] == 200,
            "modelo_retornado": row["metadados_geracao"]["model_name"] == config["modelo"],
            "diagnostico_literal": facts == [{"fato": f["id"], "chunks": [d["indice"]
                for d in row["contexto"] if Path(d["metadados"]["source"]).name == f["fonte"]
                and f["trecho"] in d["conteudo"]]} for f in case["fatos_esperados"]],
        }
        checks.update({f"{row['id']}/{name}": bool(value) for name, value in valid.items()})
        details.append({"id": row["id"], "trechos_esperados": len(facts),
                        "trechos_localizados": sum(bool(f["chunks"]) for f in facts),
                        "finish_reason": row["metadados_geracao"]["finish_reason"],
                        "tentativas_http": len(row["tentativas_http"])})
    checks["ordem_temporal"] = all(a["fim_utc"] <= b["inicio_utc"] for a, b in pairwise(rows))
    execution = load(batch / "execucao.json")
    checks["execucao_completa_e_instrumentada"] = execution["coleta_completa"] and execution["instrumentacao_valida"] and execution["respostas_obtidas"] == 12
    reviews = load(batch / "revisao.json")
    checks["fichas_humanas_continuam_pendentes"] = [r["id"] for r in reviews] == expected_ids and all(
        r["estado"] == "pendente" and r["revisor"] is None for r in reviews)
    key = os.environ.get("GROQ_API_KEY") or dotenv_values(ROOT / ".env").get("GROQ_API_KEY")
    if key:
        checks["valor_credencial_ausente_dos_artefatos"] = all(
            key.encode() not in p.read_bytes() for p in batch.rglob("*") if p.is_file())
    return {"data_utc": datetime.now(UTC).isoformat(), "lote": batch.name,
            "conferencia_estrutural_aprovada": all(checks.values()),
            "verificacoes": checks, "respostas": details,
            "credencial_disponivel_para_conferencia_local": bool(key),
            "julgamento_semantico": "Não realizado por este conferidor; revisão humana permanece pendente."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lote", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.lote)
    args.saida.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"conferencia_estrutural_aprovada": result["conferencia_estrutural_aprovada"],
                      "verificacoes": len(result["verificacoes"]),
                      "falhas": [k for k, v in result["verificacoes"].items() if not v]}, ensure_ascii=False))
    return 0 if result["conferencia_estrutural_aprovada"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
