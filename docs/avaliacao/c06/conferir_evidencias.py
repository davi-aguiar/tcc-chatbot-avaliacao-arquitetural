"""Conferência posterior do lote C06; não executa a aplicação nem a coleta."""
import argparse
import hashlib
import json
import runpy
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from langchain_core.documents import Document

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
DEFAULT_BATCH = ROOT / "docs/avaliacao/evidencias-c06/20261114-231108-coletar-7b9bcf"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locate(value, marker, path="$"):
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in locate(v, marker, f"{path}.{k}")]
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in locate(v, marker, f"{path}[{i}]")]
    return [path] if isinstance(value, str) and marker in value else []


def verify(batch, workspace=ROOT):
    checks = []

    def check(label, condition):
        checks.append({"verificacao": label, "aprovada": bool(condition)})

    env, execution = read(batch / "ambiente.json"), read(batch / "execucao.json")
    frozen = batch / "fontes"
    check("manifesto: 68 fontes", len(env["sha256"]) == 68)
    check("manifesto: corte e ambiente limpo", env["commit"] == "d5aa47767cd950cb13b63fdd2acc45353f969f2f"
          and env["git_status"] == "" and not env["credencial_real_lida"] and not env["dotenv_lido"])
    for name, sha in env["sha256"].items():
        for root, label in ((frozen, "copia"), (workspace, "atual")):
            path = root / name
            check(f"sha256:{label}:{name}", path.is_file() and digest(path) == sha)
    # Não interpretar código do prompt caso suas fontes tenham sido alteradas.
    if not all(c["aprovada"] for c in checks):
        return result(checks, batch, {})
    spec = read(frozen / "docs/avaliacao/c06/casos.json")
    fixture = spec["fixture"]
    check("matriz: sete perfis, duas rodadas", spec["repeticoes"] == 2
          and [c["id"] for c in spec["casos"]] == [f"D{i:02}" for i in range(1, 8)]
          and [c["http_status"] for c in spec["casos"]] == [200, 400, 200, 400, 200, 400, None])
    expected_ids = {f"D{i:02}-R{r}" for r in (1, 2) for i in range(1, 8)}
    check("amostra: arquivos exatos", {p.stem for p in batch.glob("D*.json")} == expected_ids)
    check("execucao: completa sem erro", execution["modo"] == "coletar"
          and execution["observacoes_previstas"] == execution["observacoes_executadas"] == 14
          and execution["coleta_completa"] and execution["fontes_inalteradas"]
          and execution["erro_tipo"] is None and execution["julgamento"] == "pendente_analise")
    prompt = runpy.run_path(str(frozen / "app/adapters/prompts.py"))["rag_prompt"]
    menu = read(frozen / "api/services/menu_texts.json")
    rows = []
    previous_end = datetime.fromisoformat(execution["inicio_utc"])
    for repetition in (1, 2):
        for case in spec["casos"]:
            identifier = f"{case['id']}-R{repetition}"
            row = read(batch / f"{identifier}.json")

            def ck(label, condition, identifier=identifier):
                check(f"{identifier}:{label}", condition)

            ck("identidade e fixture", row["id"] == identifier and row["caso"] == case["id"]
               and row["rodada"] == repetition and row["entrada"] == case["entrada"]
               and row["fixture"] == fixture)
            start, end = (datetime.fromisoformat(row[k]) for k in ("inicio_utc", "fim_utc"))
            ck("ordem e intervalo", previous_end <= start <= end <= datetime.fromisoformat(execution["fim_utc"]))
            previous_end = end
            ck("validade e isolamento", row["observacao_valida"] and row["erro_instrumento"] is None
               and row["tentativas_externas"] == [])
            ck("diagnostico de segredo bruto", row["credencial_em_dados_brutos"] == [])
            # O segredo foi descartado: não se pode recalcular a procura anterior à omissão.
            # A ausência do marcador de omissão serve apenas como conferência adicional.
            ck("sem marcador de omissao", not locate(row, "[CREDENCIAL_SINTETICA_OMITIDA]"))
            query = case.get("consulta_esperada", case["entrada"])
            if case["percurso"] == "menu":
                ck("query de menu", menu[case["estado"]]["options"][case["entrada"]]["query"] == query)
            count = case["chamadas_previstas"]
            ck("contagens de fronteiras", len(row["http"]) == len(row["nlp"]) == len(row["recuperacoes"]) == count)
            ck("recuperacoes", row["recuperacoes"] == [query] * count)
            for nlp in row["nlp"]:
                ck("entrada NLP", nlp["consulta"] == query and nlp["user_name_recebido"] == fixture["nome_cadastrado"])
                ck("retorno NLP", nlp["erro_tipo"] == ("BadRequestError" if case["http_status"] == 400 else None))
                if case["http_status"] == 200:
                    ck("personalizacao posterior", nlp["resposta"] == fixture["resposta_sintetica"].replace(
                        "Olá!", f"Oi, {fixture['nome_cadastrado']}! 😊"))
            for http in row["http"]:
                ck("HTTP local serializado", http["metodo"] == "POST"
                   and http["url"] == "https://api.groq.com/openai/v1/chat/completions"
                   and http["autenticacao_presente"] is True and http["status_sintetico"] == case["http_status"]
                   and set(http) == {"metodo", "url", "autenticacao_presente", "corpo", "status_sintetico"})
                doc = Document(page_content=fixture["contexto"], metadata={"source": "c06-documento-sintetico.txt"})
                expected = {"messages": [{"role": "user", "content": prompt.format(context=[doc], question=query)}],
                            "model": "llama-3.3-70b-versatile", "max_tokens": 500, "n": 1,
                            "reasoning_effort": None, "reasoning_format": None, "service_tier": "on_demand",
                            "stop": None, "stream": False, "temperature": 0.1}
                ck("corpo integral reconstruido", http["corpo"] == expected)
            before, after = row["antes"], row["depois"]
            expected_user = {"id": 1, "id_wpp": fixture["id_cadastrado"], "name": fixture["nome_cadastrado"], "state": case["estado"]}
            ck("banco inicial", before == {"users": [expected_user], "chats": [{"id": 1, "user_id": 1}],
               "messages": [{"id": i, "chat_id": 1, "sender": sender, "text": fixture[key]}
                            for i, sender, key in ((1, "user", "historico_usuario"), (2, "bot", "historico_bot"))],
               "audit_logs": []})
            expected_user = dict(expected_user, state="WAITING_4_SERVICOS" if not count else case["estado"])
            ck("identidade e vinculo persistidos", after["users"] == [expected_user] and after["chats"] == before["chats"])
            failed_menu = case["id"] == "D02"
            expected_messages = list(before["messages"])
            if not failed_menu:
                expected_messages += [{"id": 3, "chat_id": 1, "sender": "user", "text": case["entrada"]},
                                      {"id": 4, "chat_id": 1, "sender": "bot", "text": row["resposta_chamador"]["text"]}]
            ck("mensagens e rollback", after["messages"] == expected_messages)
            audits = after["audit_logs"]
            ck("eventos de auditoria", len(audits) == 2 and [a["event_type"] for a in audits]
               == ["MESSAGE_RECEIVED", "MESSAGE_FAILED" if failed_menu else "MESSAGE_SENT"]
               and all(a["user_id"] == 1 for a in audits))
            ck("logs disponiveis", bool(row["logs"]) and all(set(log) == {"logger", "nivel", "mensagem", "formatado"}
                                                         for log in row["logs"]))
            markers = {k: fixture[k] for k in ("id_cadastrado", "nome_cadastrado", "id_declarado", "nome_declarado",
                                              "historico_usuario", "historico_bot", "contexto")}
            markers.update(consulta=query, relato="RELATO_C06_FICTICIO")
            regions = {"payload": [h["corpo"] for h in row["http"]], "logs": row["logs"], "persistencia": after}
            recomputed = {region: {k: locate(value, marker) for k, marker in markers.items()}
                          for region, value in regions.items()}
            ck("localizacoes recalculadas", row["localizacoes"] == recomputed)
            rows.append({"id": identifier, "http": count, "status": case["http_status"],
                         "logs": len(row["logs"]), "mensagens_depois": len(after["messages"]),
                         "eventos": [a["event_type"] for a in audits],
                         "localizacoes": recomputed,
                         "emissoes_com_relato": sum("RELATO_C06_FICTICIO" in log["mensagem"] for log in row["logs"])})
    summary = {"observacoes": len(rows), "fontes": len(env["sha256"]), "http": sum(r["http"] for r in rows),
               "status_http": dict(Counter(str(r["status"]) for r in rows if r["http"])),
               "logs": sum(r["logs"] for r in rows), "auditorias": sum(len(r["eventos"]) for r in rows),
               "mensagens_depois": sum(r["mensagens_depois"] for r in rows),
               "emissoes_com_relato": sum(r["emissoes_com_relato"] for r in rows),
               "observacoes_com_relato_em_logs": [r["id"] for r in rows if r["emissoes_com_relato"]],
               "por_observacao": rows}
    return result(checks, batch, summary)


def result(checks, batch, summary):
    return {"cenario": "C06", "lote": batch.name, "data_utc": datetime.now(UTC).isoformat(),
            "natureza": "conferencia_posterior_estrutural_sem_julgamento_humano",
            "verificador_sha256": digest(Path(__file__)), "total": len(checks),
            "aprovadas": sum(c["aprovada"] for c in checks), "valido": all(c["aprovada"] for c in checks),
            "verificacoes": checks, "resumo": summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lote", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    if args.saida.resolve().is_relative_to(args.lote.resolve()):
        parser.error("A saída deve ficar fora do lote original.")
    report = verify(args.lote)
    args.saida.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("lote", "total", "aprovadas", "valido")}, ensure_ascii=False))
    return 0 if report["valido"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
