import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader

def load_servicos():
    
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    servicos_path = os.path.join(root_dir, "data", "servicos")


    if not os.path.exists(servicos_path):
        raise FileNotFoundError(f"Pasta 'servicos' não encontrada em: {servicos_path}")

    loader = DirectoryLoader(
        servicos_path,
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )

    return loader.load()
