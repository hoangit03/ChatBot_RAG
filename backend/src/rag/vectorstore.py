from typing import List, Optional, Type, Dict, Any, ClassVar
import logging
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.vectorstores import VectorStore
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
import os

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VectorDB:
    """
    Lớp để xây dựng và quản lý cơ sở dữ liệu vector cho truy vấn ngữ nghĩa.
    Hỗ trợ nhiều loại vector stores khác nhau như Chroma và FAISS.
    """

    # Embedding đa ngôn ngữ
    DEFAULT_EMBEDDING_MODEL: ClassVar[str] = "paraphrase-multilingual-mpnet-base-v2"

    def __init__(
        self,
        documents: Optional[List[Document]] = None,
        vector_db_cls: Type[VectorStore] = FAISS,
        embedding: Optional[Embeddings] = None,
        persist_directory: Optional[str] = None,
        vector_db_kwargs: Optional[Dict[str, Any]] = None,
        index_name: Optional[str] = "vectordb"
        ) -> None:
        """
        Khởi tạo VectorDB.
        
        Args:
            documents: Danh sách các document cần lưu trữ
            vector_db_cls: Lớp vector store (Chroma, FAISS, ...)
            embedding: Mô hình embedding để chuyển đổi văn bản thành vector
            persist_directory: Thư mục để lưu vector database (cho Chroma)
            vector_db_kwargs: Các tham số bổ sung cho vector database
            index_name: Tên của index (cho FAISS)
        """
        self.vector_db_cls = vector_db_cls
        self.persist_directory = persist_directory
        self.index_name = index_name

        self.embedding = embedding or HuggingFaceEmbeddings(
            model_name=self.DEFAULT_EMBEDDING_MODEL
        )
        
        self.vector_db_kwargs = vector_db_kwargs or {}
        

        self.db = None
        if documents:
            self.db = self._build_db(documents)
        elif persist_directory:
            self.db = self._load_db()
        
    def _build_db(self, documents: List[Document]) -> VectorStore:
        """
        Xây dựng cơ sở dữ liệu vector từ documents.
        
        Args:
            documents: Danh sách các document cần lưu trữ
            
        Returns:
            VectorStore: Cơ sở dữ liệu vector đã được xây dựng
        """
        if not documents:
            logger.warning("Không có document nào để xây dựng vector database")
            return None
        
        try:

            logger.info(f"Đang xây dựng {self.vector_db_cls.__name__} với {len(documents)} document")
            db = self.vector_db_cls.from_documents(
                documents=documents,
                embedding=self.embedding,
                **self.vector_db_kwargs
            )

            # Lưu database nếu có persist_directory
            if self.persist_directory:
                self._save_db(db)

            logger.info(f"Xây dựng thành công {self.vector_db_cls.__name__}")
            return db
        except Exception as e:
            logger.error(f"Lỗi khi xây dựng vector database: {str(e)}")
            raise

    def _load_db(self) -> Optional[VectorStore]:
        """
        Load vector database từ đĩa.
        
        Returns:
            VectorStore: Vector database đã được load từ đĩa
        """
        if not self.persist_directory:
            logger.warning("Không có persist_directory để load database")
            return None
        
        try:
            faiss_path = self.persist_directory
            index_path = os.path.join(faiss_path, f"{self.index_name}.faiss")
            index_pkl_path = os.path.join(faiss_path, f"{self.index_name}.pkl")
            
            if os.path.exists(index_path) and os.path.exists(index_pkl_path):
                logger.info(f"Đang load FAISS database từ {faiss_path}")
                db = FAISS.load_local(
                    folder_path=faiss_path,
                    embeddings=self.embedding,
                    index_name=self.index_name,
                    allow_dangerous_deserialization=True
                )
                logger.info("Đã load FAISS database thành công")
                return db
            else:
                logger.warning(f"Không tìm thấy file FAISS index tại {faiss_path}")
                return None
        except Exception as e:
            logger.error(f"Lỗi khi load vector database: {str(e)}")
            return None

    def get_retriever(
            self,
            search_type: str = 'similarity',
            search_kwargs: Optional[Dict[str, Any]] = None
        ):
        """
        Tạo retriever từ vector database.
        
        Args:
            search_type: Loại tìm kiếm ('similarity', 'mmr', ...)
            search_kwargs: Các tham số cho tìm kiếm (k, ...)
            
        Returns:
            Retriever từ vector database
        """
        if not self.db:
            raise ValueError("Vector database chưa được xây dựng")
        
        search_kwargs = search_kwargs or {"k": 10}
            
        retriever = self.db.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
        return retriever

    def add_documents(self, documents: List[Document]) -> None:
        """
        Thêm documents vào vector database đã tồn tại.
        
        Args:
            documents: Danh sách các document cần thêm
        """
        if not documents:
            logger.warning("Không có documents nào để thêm vào vector database")
            return
            
        if not self.db:
            self.db = self._build_db(documents)
        else:
            try:
                logger.info(f"Đang thêm {len(documents)} documents vào vector database")
                self.db.add_documents(documents)
                
                if self.persist_directory:
                    self._save_db(self.db)
            except Exception as e:
                logger.error(f"Lỗi khi thêm documents vào vector database: {str(e)}")
                raise
       
    def _save_db(self, db: VectorStore):
        """
        Lưu vector database vào đĩa.
        
        Args:
            db: Vector database cần lưu
        """
        try:
            if isinstance(db, FAISS):
                # Đảm bảo thư mục tồn tại
                os.makedirs(self.persist_directory, exist_ok=True)
                
                # Lưu FAISS với index_name
                db.save_local(
                    folder_path=self.persist_directory,
                    index_name=self.index_name
                )
                logger.info(f"Đã lưu FAISS vector database vào {self.persist_directory}")
            
            else:
                logger.warning(f"Chưa hỗ trợ lưu cho loại database {type(db).__name__}")
        
        except Exception as e:
            logger.error(f"Lỗi khi lưu vector database: {str(e)}")
            raise
    
    def save(self, save_path: str) -> None:
        """
        Lưu vector database hiện tại.
        """
        if not self.db:
            raise ValueError("Vector database chưa được xây dựng")
        
        if not self.persist_directory:
            raise ValueError("Không có persist_directory để lưu database")
            
        self._save_db(self.db)
