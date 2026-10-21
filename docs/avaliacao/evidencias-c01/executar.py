"""Executar da raiz: python docs/avaliacao/evidencias-c01/executar.py baseline|A|B."""
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
variant = sys.argv[1]
command = [sys.executable, "-m", "pytest", "tests/", "-q"]
start = time.perf_counter()
result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
(OUT / f"testes-{variant}.txt").write_text("Comando: python -m pytest tests/ -q\n" + result.stdout + result.stderr + f"\nExit code: {result.returncode}\nDuracao: {time.perf_counter()-start:.3f}s\n", encoding="utf-8")
print(result.stdout, result.stderr)
if result.returncode:
    sys.exit(result.returncode)
if variant == "baseline":
    sys.exit(0)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.models.models import Base, User
from api.services.chat_service import ChatService
from api.services.menu_handlers import TEXTS

class NLPFake:
    def __init__(self):
        self.calls = []
    def process(self, text, user_name=None):
        self.calls.append({"query": text, "user_name": user_name})
        return "RESPOSTA CONTROLADA C01 - nao comprova recuperacao ou geracao."

engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
traces = []
with sessionmaker(bind=engine)() as db:
    user = User(id_wpp="5500000000000", name="Teste C01", state="WAITING_MAIN_MENU")
    db.add(user)
    db.commit()
    nlp = NLPFake()
    def send(text, state, fragment):
        response = asyncio.run(ChatService(db, nlp).process_message(user.id_wpp, text))
        db.refresh(user)
        traces.append({"entrada": text, "estado": user.state, "saida": response.text})
        assert user.state == state, traces[-1]
        assert fragment in response.text, traces[-1]
    main = "WAITING_MAIN_MENU"
    services = "WAITING_4_SERVICOS"
    new = "WAITING_4_17_C01"
    send("/menu", main, "MENU PRINCIPAL")
    send("4", services, "17")
    send("17", new, "SERVI\u00c7O EXPERIMENTAL C01")
    send("0", services, TEXTS[services]["text"])
    send("0", main, "MENU PRINCIPAL")
    send("4", services, "17")
    send("17", new, "SERVI\u00c7O EXPERIMENTAL C01")
    send("99", new, "Op\u00e7\u00e3o inv\u00e1lida")
    send("/menu", main, "MENU PRINCIPAL")
    send("4", services, "17")
    existing = TEXTS[services]["options"]["2"]["next_state"]
    send("2", existing, "CEMERF")
    send("0", services, TEXTS[services]["text"])
    send("0", main, "MENU PRINCIPAL")
    assert not nlp.calls
    if variant == "B":
        send("4", services, "17")
        send("17", new, "SERVI\u00c7O EXPERIMENTAL C01")
        send("1", new, "RESPOSTA CONTROLADA C01")
        assert nlp.calls == [{"query": "Qual \u00e9 a finalidade do Servi\u00e7o Experimental C01?", "user_name": "Teste C01"}]
        send("0", services, TEXTS[services]["text"])
        send("0", main, "MENU PRINCIPAL")
(OUT / f"percursos-{variant}.json").write_text(json.dumps({"nivel": "ChatService real, SQLite em memoria, NLP substituto", "percursos": traces, "chamadas_nlp": nlp.calls}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"C01-{variant}: {len(traces)} etapas aprovadas; {len(nlp.calls)} chamadas NLP.")
