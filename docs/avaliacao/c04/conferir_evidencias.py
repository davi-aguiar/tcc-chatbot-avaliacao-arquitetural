"""Conferência posterior de C04, por leitura; não repete casos nem acessa rede."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "docs/avaliacao/evidencias-c04"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(batch):
    manifest = load(batch / "ambiente.json")
    spec = load(batch / "casos.json")
    rows = load(batch / "casos-executados.json")
    result = load(batch / "resumo.json")
    execution = load(batch / "execucao.json")
    isolation = load(batch / "isolamento.json")
    coverage = load(batch / "cobertura.json")
    packages = load(batch / "cobertura-por-pacote.json")
    observations = {r["id"]: r["observacoes"] for r in rows}
    expected_ids = [c["id"] for c in spec["casos"]]
    sources = manifest["sha256"]
    copies = [name for name in sources if name.startswith("docs/avaliacao/c04/")]
    copies += ["docs/avaliacao/C04-protocolo.md"]
    check = {
        "hashes_fontes_conferem": all((ROOT / name).is_file() and sha(ROOT / name) == value
                                      for name, value in sources.items()),
        "copias_conferem": all(sha(batch / Path(name).name) == sources[name] for name in copies),
        "matriz_completa_em_ordem": [r["id"] for r in rows] == expected_ids and len(expected_ids) == 16,
        "pytest_completo_aprovado": all([(p["fase"], p["resultado"]) for p in r["pytest"]]
                                        == [(phase, "passed") for phase in ("setup", "call", "teardown")]
                                        for r in rows),
        "credenciais_ausentes": isolation["ambiente_por_lista_permitida"]
                                and isolation["credenciais_presentes"] == [],
        "dotenv_neutralizado": isolation["dotenv_neutralizado"] and isolation["chamadas_dotenv_suprimidas"] >= 1,
        "zero_tentativas_externas": isolation["bloqueio_ativo"] and isolation["tentativas"] == [],
        "caches_sem_arquivos": set(isolation["cache_antes"]) == set(isolation["cache_depois"])
                               and len(isolation["cache_antes"]) == 5
                               and not any(isolation["cache_antes"].values())
                               and not any(isolation["cache_depois"].values())
                               and not any(p.is_file() for p in (batch / "cache-vazio").rglob("*")),
    }
    docs = observations["I01"]["documentos"]
    check["ingestao_conteudo_e_origem"] = (len(docs) == 2 and
        {Path(d["metadata"]["source"]).name for d in docs} == {"aurora.txt", "horizonte.txt"} and
        all(d["texto"] == Path(d["metadata"]["source"]).read_text(encoding="utf-8") for d in docs))
    chunking = observations["D01"]
    check["chunking_real"] = (chunking["documentos"] == 2 and chunking["chunks"] == 10
                              and len(chunking["tamanhos"]) == 10
                              and all(0 < n <= 1000 for n in chunking["tamanhos"])
                              and any(chunking["sobreposicoes"]))
    check["faiss_discrimina_documentos"] = all(
        observations[case]["indice_tipo"] == "FAISS" and observations[case]["vetores"] == 10
        and len(observations[case]["resultados"]) == 1
        and marker in observations[case]["resultados"][0]["texto"]
        for case, marker in (("R01", "C04-AURORA-2026"), ("R02", "C04-HORIZONTE-2026")))
    boot = observations["B01"]
    check["montagem_real"] = (boot["chaves"] == ["servicos"] and boot["metricas"]["n_documentos"] == 2
                              and boot["metricas"]["n_chunks"] == 10
                              and boot["construtores"] == [{"model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"}])
    context = observations["P01"]
    check["prompt_e_resposta"] = (len(context["prompts"]) == 1 and context["pergunta"] in context["prompts"][0]
                                  and "C04-AURORA-2026" in context["prompts"][0]
                                  and "C04-HORIZONTE-2026" not in context["prompts"][0]
                                  and context["resposta"] == "Resposta fixa para Aurora, somente para teste.")
    empty = observations["P02"]
    check["ausencia_e_resposta_vazia"] = (empty["resposta_nlp"] is None
        and len(empty["prompts"]) == 1 and "CONTEXTO:\n[]" in empty["prompts"][0]
        and observations["P03"]["resposta_nlp"] is None)
    check["excecoes_identicas"] = (observations["E01"]["mesma_excecao"] is True
        and len(observations["E01"]["prompts"]) == 1
        and observations["E02"]["mesma_excecao"] is True and observations["E02"]["prompts"] == [])
    check["entradas_locais_e_personalizacao"] = (
        observations["L01"]["erro_tipo"] == "ValueError" and observations["L01"]["cache_vazio"]
        and observations["L02"]["chamadas_embeddings_adicionais"] == 0
        and observations["L02"]["prompts"] == []
        and observations["N01"]["resposta"] == "Oi, Ana C04! 😊\nComo posso te ajudar?"
        and observations["N02"]["resposta"] == "Oi, Ana C04! 😊 Desculpe a demora. Resposta sintética sobre Aurora.")
    coverage_ok = True
    for package in ("app", "api"):
        files = [v for name, v in coverage["files"].items() if name.replace("\\", "/").startswith(package + "/")]
        totals = packages[package]["totais"]
        coverage_ok = coverage_ok and all(totals[key] == sum(f["summary"][key] for f in files)
            for key in ("num_statements", "covered_lines", "num_branches", "covered_branches"))
        coverage_ok = coverage_ok and all(len(f["executed_lines"]) == f["summary"]["covered_lines"] for f in files)
    check["cobertura_recalculada_por_pacote"] = coverage_ok
    check["resumos_coerentes"] = (result["casos_previstos"] == result["casos_executados"]
        == result["casos_aprovados"] == 16 and result["coleta_valida"] and result["julgamento"] == "atendido"
        and result["pytest_exit_code"] == 0 and all(execution[k] == v for k, v in result.items()))
    return {"lote": batch.name, "checks": check, "valido": all(check.values()),
            "arquivos_fontes_conferidos": len(sources), "casos": len(rows),
            "cobertura": {k: v["totais"] for k, v in packages.items()},
            "artefatos_sha256": {p.relative_to(batch).as_posix(): sha(p) for p in sorted(batch.rglob("*"))
                                 if p.is_file() and "__pycache__" not in p.parts and p.name != ".coverage"}}


def main():
    results = [verify(p) for p in sorted(EVIDENCE.iterdir())
               if p.is_dir() and (p / "execucao.json").exists()]
    functional = subprocess.run(["git", "diff", "--quiet", "77348fb", "--", "api", "app", "data", "tests"],
                                cwd=ROOT, check=False).returncode == 0
    missing = []
    docs = [ROOT / "docs/avaliacao/C04-protocolo.md", ROOT / "docs/avaliacao/C04-relatorio-execucao.md",
            EVIDENCE / "README.md"]
    for doc in docs:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
            target = target.split("#")[0]
            resolved = (doc.parent / target).resolve()
            own_output = (EVIDENCE / "validacao-evidencias.json").resolve()
            if target and not re.match(r"[a-zA-Z]+://", target) and resolved != own_output and not resolved.exists():
                missing.append({"documento": doc.relative_to(ROOT).as_posix(), "destino": target})
    result = {"conferencia_utc": datetime.now(timezone.utc).isoformat(), "lotes": results,
              "funcional_preservado": functional, "links_ausentes": missing,
              "metodo": "Leitura independente de registros, contagens, cobertura, hashes e diff; sem repetir coleta.",
              "valido": bool(results) and all(r["valido"] for r in results) and functional and not missing}
    (EVIDENCE / "validacao-evidencias.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valido": result["valido"], "lotes": len(results), "links_ausentes": missing,
                      "funcional_preservado": functional}, ensure_ascii=False))
    return 0 if result["valido"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
