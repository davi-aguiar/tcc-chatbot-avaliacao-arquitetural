"""Carga HTTP C03-B em processo separado do Uvicorn; não altera a aplicação."""
import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import time
import uuid

import httpx

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TOKEN = "c03b-token-sintetico"
sys.path.insert(0, str(ROOT))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now():
    return datetime.now(timezone.utc).isoformat()


def read_events(out):
    path = out / "eventos.jsonl"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass  # Última linha pode estar sendo escrita pelo subprocesso.
    return events


def cases(mode):
    if mode == "real":
        return [("evolution", "rag_real", n) for n in (1, 10)]
    return ([(route, profile, n) for route in ("rest", "evolution")
             for profile in ("estatico", "rag_lento") for n in (1, 2, 5, 10)]
            + [("evolution", profile, n) for profile in ("envio_lento", "limite_429") for n in (1, 10)]
            + [("evolution", "timeout_cliente", 10)])


def body(route, identity, text):
    if route == "rest":
        return "/messages/receive", {"id_wpp": identity, "text": text}
    return "/evolution_webhook", {"event": "messages.upsert", "data": {
        "key": {"remoteJid": identity + "@s.whatsapp.net"}, "message": {"conversation": text}}}


async def request(client, rid, path, payload=None, timeout=90):
    record = {"rid": rid, "path": path, "despacho_t": time.perf_counter(), "erro_cliente": None}
    try:
        response = await client.request("GET" if payload is None else "POST", path,
                                        json=payload, headers={"X-C03-ID": rid, "X-Webhook-Token": TOKEN},
                                        timeout=httpx.Timeout(timeout, connect=5, pool=5))
        record.update(status=response.status_code, resposta=response.json())
    except Exception as exc:
        record.update(status=None, erro_cliente=type(exc).__name__)
    record.update(fim_t=time.perf_counter())
    record["duracao_s"] = record["fim_t"] - record["despacho_t"]
    return record


def analyse(row, events):
    prefix = row["id"] + "-"
    selected = [e for e in events if e["rid"].startswith(prefix)]
    nlp_intervals = {}
    current = maximum = 0
    for event in selected:
        if event["evento"] == "nlp_inicio":
            current += 1
            maximum = max(maximum, current)
            nlp_intervals.setdefault(event["rid"], {})["inicio"] = event["t"]
        elif event["evento"] == "nlp_fim":
            current -= 1
            nlp_intervals.setdefault(event["rid"], {})["fim"] = event["t"]
    probe = row["sondas_durante"][0]
    health_start = next((e["t"] for e in selected
                         if e["rid"] == probe["rid"] and e["evento"] == "http_inicio"), None)
    waits = [(v["inicio"], v["fim"]) for v in nlp_intervals.values() if "inicio" in v and "fim" in v]
    gateway = {}
    if row["perfil"] == "envio_lento":
        for e in selected:
            if e["evento"] in ("envio_inicio", "envio_fim"):
                gateway.setdefault(e["rid"], {})[e["evento"]] = e["t"]
        waits = [(v["envio_inicio"], v["envio_fim"]) for v in gateway.values()
                 if "envio_inicio" in v and "envio_fim" in v]
    waited = [(start, end) for start, end in waits if start < probe["despacho_t"] < end]
    durations = [r["duracao_s"] for r in row["requisicoes"]]
    times = [r["despacho_t"] for r in row["requisicoes"]]
    lag = [e["lag_s"] for e in events if e["evento"] == "loop_atrasado"
           and row["inicio_t"] <= e["t"] <= row["fim_t"]]
    audits = Counter(e["tipo"] for e in row["snapshot"].get("auditoria", []))
    provider = Counter(e["status"] for e in selected if e["evento"] == "provedor_resposta")
    actual_outputs = {e["rid"]: e["texto"] for e in selected if e["evento"] == "envio_fim"}
    expected = ("WAITING_4_SERVICOS" if row["perfil"] in ("estatico", "envio_lento") else "WAITING_1_1_INFO")
    states = {u["id_wpp"]: u["estado"] for u in row["snapshot"].get("usuarios", [])}
    return {
        "mediana_s": statistics.median(durations), "min_s": min(durations), "max_s": max(durations),
        "amplitude_despacho_s": max(times) - min(times),
        "http_200": sum(r.get("status") == 200 for r in row["requisicoes"]),
        "erros_cliente": dict(Counter(r["erro_cliente"] for r in row["requisicoes"] if r["erro_cliente"])),
        "inferencias_max_simultaneas": maximum, "inferencias_observadas": len(nlp_intervals),
        "status_provedor": dict(provider), "auditoria": dict(audits),
        "lag_loop_max_s": max(lag, default=0), "saude_durante_s": probe["duracao_s"],
        "menu_durante_s": row["sondas_durante"][1]["duracao_s"],
        "saude_enviada_durante_espera": bool(waited),
        "saude_executada_apos_espera": bool(waited) and health_start is not None and health_start >= waited[0][1],
        "processo_vivo_apos": row["processo_vivo_apos"], "drenagem_completa": row["drenagem_completa"],
        "estado_usuarios_esperado": all(states.get(identity) == expected for identity in row["usuarios_carga"]),
        "respostas_saida": actual_outputs,
        "saude_apos_ok": row["saude_apos"].get("status") == 200,
        "menu_apos_ok": row["menu_apos"].get("status") == 200 and (
            row["menu_apos"].get("resposta", {}).get("status") == "success" if row["rota"] == "evolution"
            else "MENU PRINCIPAL" in row["menu_apos"].get("resposta", {}).get("response", "")),
    }


async def run_burst(client, out, process, number, route, profile, size, mode):
    label = f"B{number:02d}-{route}-{profile}-{size}"
    users = [f"550003{number:03d}{i:04d}" for i in range(size + 2)]
    rag = profile not in ("estatico", "envio_lento")
    prepare = await request(client, label + "-prepare", "/__c03/prepare", {
        "perfil": profile, "estado": "WAITING_1_1_INFO" if rag else "WAITING_MAIN_MENU", "usuarios": users})
    if prepare.get("status") != 200:
        raise RuntimeError("Preparacao da rajada falhou")
    text = "1" if rag else "4"
    start = time.perf_counter()
    barrier = asyncio.Event()

    async def send(index):
        await barrier.wait()
        path, payload = body(route, users[index], text)
        return await request(client, label + f"-carga-{index:02d}", path, payload,
                             timeout=1 if profile == "timeout_cliente" else (180 if mode == "real" else 90))

    tasks = [asyncio.create_task(send(i)) for i in range(size)]
    barrier.set()
    if profile != "estatico":
        deadline = time.perf_counter() + 30
        target = "envio_inicio" if profile == "envio_lento" else "provedor_inicio"
        while time.perf_counter() < deadline:
            if any(e["evento"] == target and e["rid"].startswith(label + "-carga") for e in read_events(out)):
                break
            if all(t.done() for t in tasks):
                break
            await asyncio.sleep(0.01)
    menu_path, menu_body = body(route, users[-2], "/menu")
    probes = await asyncio.gather(request(client, label + "-saude-durante", "/__c03/health", timeout=360),
                                  request(client, label + "-menu-durante", menu_path, menu_body, timeout=360))
    results = await asyncio.gather(*tasks)
    limit = time.perf_counter() + (360 if mode == "real" else 90)
    expected_rids = {r["rid"] for r in results}
    drained = False
    while time.perf_counter() < limit and process.poll() is None:
        ended = {e["rid"] for e in read_events(out) if e["evento"] == "http_fim"}
        if expected_rids <= ended:
            drained = True
            break
        await asyncio.sleep(0.05)
    health = await request(client, label + "-saude-apos", "/__c03/health", timeout=10)
    path, payload = body(route, users[-1], "/menu")
    menu = await request(client, label + "-menu-apos", path, payload, timeout=15)
    snapshot = await request(client, label + "-snapshot", "/__c03/snapshot", timeout=15)
    row = {"id": label, "rota": route, "perfil": profile, "usuarios": size, "inicio_t": start,
           "fim_t": time.perf_counter(), "usuarios_carga": users[:size], "requisicoes": results,
           "sondas_durante": probes, "saude_apos": health, "menu_apos": menu,
           "snapshot": snapshot.get("resposta", {}), "processo_vivo_apos": process.poll() is None,
           "drenagem_completa": drained}
    row["resumo"] = analyse(row, read_events(out))
    save(out / f"{label}.json", row)
    print(json.dumps({"rajada": label, **{k: v for k, v in row["resumo"].items()
                                          if k not in ("respostas_saida", "auditoria")}}, ensure_ascii=False), flush=True)
    return row


def manifest(mode):
    files = [p for folder in ("api", "app", "data/servicos") for p in (ROOT / folder).rglob("*")
             if p.suffix in (".py", ".json", ".txt")]
    files += list(HERE.glob("*.py")) + [HERE.parent / "C03-B-protocolo.md"]
    return {"inicio_utc": now(), "modo": mode, "python": sys.version, "plataforma": platform.platform(),
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).strip(),
            "dependencias": sorted({f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()}),
            "sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}


async def collect(out, process, mode):
    deadline = time.perf_counter() + 180
    async with httpx.AsyncClient(trust_env=False, limits=httpx.Limits(max_connections=40)) as client:
        while time.perf_counter() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Servidor encerrou na preparacao")
            ready = out / "servidor.json"
            if ready.exists():
                server = json.loads(ready.read_text(encoding="utf-8"))
                client.base_url = f"http://127.0.0.1:{server['porta']}"
                probe = await request(client, "preparacao", "/__c03/health", timeout=2)
                if probe.get("status") == 200:
                    break
            await asyncio.sleep(0.1)
        else:
            raise TimeoutError("Servidor nao ficou pronto")
        rows = []
        try:
            for number, (route, profile, size) in enumerate(cases(mode), 1):
                rows.append(await run_burst(client, out, process, number, route, profile, size, mode))
                save(out / "resumo.json", [{"id": r["id"], **r["resumo"]} for r in rows])
        finally:
            await request(client, "encerramento", "/__c03/stop", {}, timeout=10)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modo", choices=("controlado", "real"))
    parser.add_argument("--saida", type=Path, default=HERE.parent / "evidencias-c03-b")
    args = parser.parse_args()
    out = args.saida / f"{datetime.now():%Y%m%d-%H%M%S}-{args.modo}-{uuid.uuid4().hex[:6]}"
    out.mkdir(parents=True, exist_ok=False)
    save(out / "ambiente.json", manifest(args.modo))
    config = {"modo": args.modo, "atraso_s": 0.5, "modelo": "openai/gpt-oss-120b" if args.modo == "real" else "llama-3.3-70b-versatile"}
    if args.modo == "real":
        config["embeddings_snapshot"] = str(Path.home() / ".cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots/e8f8c211226b894fcb81acc59f3b34ba3efd5f42")
    save(out / "config.json", config)
    for source in [HERE / "executar.py", HERE / "servidor.py", HERE.parent / "C03-B-protocolo.md"]:
        shutil.copyfile(source, out / source.name)
    execution = {"inicio_utc": now(), "modo": args.modo, "rajadas_previstas": len(cases(args.modo))}
    print(json.dumps({"lote": str(out), **execution}, ensure_ascii=False), flush=True)
    with (out / "servidor.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, str(HERE / "servidor.py"), str(out)], cwd=ROOT,
                                   stdout=log, stderr=log,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        execution["servidor_pid"] = process.pid
        try:
            rows = asyncio.run(collect(out, process, args.modo))
            execution.update(rajadas_executadas=len(rows), coleta_completa=len(rows) == len(cases(args.modo)))
        except Exception as exc:
            execution.update(coleta_completa=False, erro_tipo=type(exc).__name__)
        finally:
            try:
                process.wait(timeout=10)
                execution["encerramento_forcado"] = False
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=10)
                execution["encerramento_forcado"] = True
            execution.update(servidor_exit_code=process.returncode, fim_utc=now())
    save(out / "execucao.json", execution)
    print(json.dumps({"lote": str(out), **execution}, ensure_ascii=False), flush=True)
    return 0 if execution["coleta_completa"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
