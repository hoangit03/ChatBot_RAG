from pydantic import Field
from typing import Literal

from langchain_community.vectorstores import FAISS
from src.rag.file_loader import Loader
from src.rag.vectorstore import VectorDB
from src.rag.offline_rag import Offline_RAG
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()


def build_rag_chain(llm, data_dir, data_type: Literal['pdf'] = 'pdf'):
    """
    Xây dựng chuỗi RAG (Retrieval-Augmented Generation)
    
    Args:
        llm: Mô hình ngôn ngữ để sử dụng
        data_dir: Đường dẫn thư mục chứa dữ liệu
        data_type: Loại dữ liệu (hiện chỉ hỗ trợ 'pdf')
        
    Returns:
        Chuỗi RAG đã được xây dựng
    """

    try:
        DATA_PATH = os.environ.get("DATA_PATH")
        DATA_NAME = os.environ.get("DATA_NAME")
        faiss_files_exist = (
            Path(DATA_PATH).exists() and 
            (Path(DATA_PATH) / f"{DATA_NAME}.faiss").exists() and 
            (Path(DATA_PATH) / f"{DATA_NAME}.pkl").exists()
        )

        if faiss_files_exist:
            vectordb = VectorDB(
            vector_db_cls=FAISS,
            persist_directory=DATA_PATH,
            index_name=DATA_NAME
            )
        else:
            loader = Loader(data_type,split_kwargs={"chunk_size": 700, "chunk_overlap": 200})
            documents = loader.load_dir(data_dir, workers=8)    
            vectordb = VectorDB(
                documents=documents,
                vector_db_cls=FAISS,
                persist_directory=DATA_PATH,
                index_name=DATA_NAME
            )
        retriever = vectordb.get_retriever(search_kwargs={"k": 10}) 
        chain_rag = Offline_RAG(llm).get_chain(retriever=retriever)
        return chain_rag
        
    except Exception as e:
        print(f"Lỗi khi xây dựng chuỗi RAG: {str(e)}")
        raise