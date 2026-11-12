from langchain_community.vectorstores import FAISS

def create_vector_store(docs, embeddings):
    return FAISS.from_documents(docs, embeddings)

def create_retriever(vector_store, k=10):
    return vector_store.as_retriever(search_kwargs={"k": k})
