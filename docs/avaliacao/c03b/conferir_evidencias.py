"""Conferência posterior, sem repetir carga HTTP ou chamar o provedor."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "docs/avaliacao/evidencias-c03-b"


def verify(batch):
    manifest = json.loads((batch / "ambiente.json").read_text(encoding="utf-8"))
    execution = json.loads((batch / "execucao.json").read_text(encoding="utf-8"))
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(batch.glob("B[0-9][0-9]-*.json"))]
    events = [json.loads(line) for line in (batch / "eventos.jsonl").read_text(encoding="utf-8").splitlines()]
    indices = {(e["rid"], e["evento"]) for e in events}
    started = Counter(e["rid"] for e in events if e["evento"] == "http_inicio")
    ended = Counter(e["rid"] for e in events if e["evento"] == "http_fim")
    config = json.loads((batch / "config.json").read_text(encoding="utf-8"))
    menu_text = json.loads((ROOT / "api/services/menu_texts.json").read_text(encoding="utf-8"))["WAITING_MAIN_MENU"]["text"]
    outputs = {e["rid"]: e["texto"] for e in events if e["evento"] == "envio_fim"}
    menus_ok = True
    persistence_ok = True
    for row in rows:
        for menu in [row["sondas_durante"][1], row["menu_apos"]]:
            answer = (outputs.get(menu["rid"], "") if row["rota"] == "evolution"
                      else menu.get("resposta", {}).get("response", ""))
            menus_ok = menus_ok and menu_text in answer
        audits = Counter(e["tipo"] for e in row["snapshot"]["auditoria"])
        persistence_ok = persistence_ok and (audits["MESSAGE_RECEIVED"] == row["usuarios"] + 2
            and audits["MESSAGE_SENT"] + audits["MESSAGE_FAILED"] == row["usuarios"] + 2
            and len(row["snapshot"]["mensagens"]) == 2 * audits["MESSAGE_SENT"])
    checks = {
        "hashes_fontes_conferem": all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                                      for name, digest in manifest["sha256"].items()),
        "copias_conferem": all(hashlib.sha256((batch / name).read_bytes()).hexdigest() == manifest["sha256"][source]
                                for name, source in {
                                    "executar.py": "docs/avaliacao/c03b/executar.py",
                                    "servidor.py": "docs/avaliacao/c03b/servidor.py",
                                    "C03-B-protocolo.md": "docs/avaliacao/C03-B-protocolo.md"}.items()),
        "rajadas_completas": len(rows) == execution["rajadas_previstas"] == execution.get("rajadas_executadas"),
        "requisicoes_finalizadas_no_servidor": started == ended,
        "saude_menu_e_drenagem": all(r["resumo"]["saude_apos_ok"] and r["resumo"]["menu_apos_ok"]
                                     and r["drenagem_completa"] and r["processo_vivo_apos"] for r in rows),
        "todas_cargas_observadas": all((q["rid"], "http_inicio") in indices and (q["rid"], "http_fim") in indices
                                       for r in rows for q in r["requisicoes"]),
        "estados_conferem": all(r["resumo"]["estado_usuarios_esperado"] for r in rows),
        "menus_sondas_tem_texto_esperado": menus_ok,
        "persistencia_e_auditoria_conferem": persistence_ok,
        "encerramento_voluntario": execution["servidor_exit_code"] == 0 and not execution["encerramento_forcado"],
        "sem_saida_externa_controlada": not any(e["evento"] == "rede_externa_bloqueada" for e in events),
    }
    requests = [q for r in rows for q in r["requisicoes"]]
    return {"lote": batch.name, "modo": config["modo"], "checks": checks, "valido": all(checks.values()),
            "rajadas": len(rows), "mensagens_carga": len(requests),
            "http_200_carga": sum(q.get("status") == 200 for q in requests),
            "erros_cliente": dict(Counter(q["erro_cliente"] for q in requests if q["erro_cliente"])),
            "respostas_provedor": dict(Counter(e["status"] for e in events if e["evento"] == "provedor_resposta")),
            "erros_nlp": dict(Counter(e["tipo"] for e in events if e["evento"] == "nlp_erro")),
            "saude_lancada_em_espera": sum(r["resumo"]["saude_enviada_durante_espera"] for r in rows),
            "saude_so_executada_apos_espera": sum(r["resumo"]["saude_executada_apos_espera"] for r in rows)}


def main():
    batches = [p for p in EVIDENCE.iterdir() if p.is_dir() and (p / "execucao.json").exists()]
    results = [verify(p) for p in sorted(batches)]
    # C03-A tem protocolo/instrumentos próprios: conferir seus hashes preservados.
    original = ROOT / "docs/avaliacao/evidencias-c03/20261108-212956-falhas-4781d2"
    old_manifest = json.loads((original / "ambiente.json").read_text(encoding="utf-8"))
    original_unchanged = all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                             for name, digest in old_manifest["sha256"].items())
    functional_unchanged = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "api", "app", "data", "tests"],
                                         cwd=ROOT, check=False).returncode == 0
    result = {"conferencia_utc": datetime.now(timezone.utc).isoformat(), "lotes": results,
              "fontes_c03_a_preservadas": original_unchanged, "aplicacao_preservada": functional_unchanged,
              "valido": bool(results) and all(r["valido"] for r in results) and original_unchanged and functional_unchanged}
    (EVIDENCE / "validacao-evidencias.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valido"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
