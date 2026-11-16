from app.core.rag_pipeline import run_rag

def generate_response(mensagem, historico, retrievers_dict):
    if not mensagem:
        return ""
        
    if "servicos" not in retrievers_dict:
        return "Erro técnico: O retriever não foi inicializado corretamente."

    retriever_especifico = retrievers_dict["servicos"]

    resposta = run_rag(retriever_especifico, mensagem)
    
    return resposta
   