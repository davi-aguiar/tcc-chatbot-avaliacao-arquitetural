from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_docs(docs):
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", " ", ""],
        
        chunk_size=1000,  
        chunk_overlap=200, 
        
        length_function=len,
        is_separator_regex=False
    )
    return splitter.split_documents(docs)