import dotenv
from typing import List
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.retrievers import BM25Retriever
import re

dotenv.load_dotenv()


def delete_collection(file_path: str, persist_directory: str = "./chromadb") -> None:
    """Delete the Chroma collection associated with the file path."""
    collection_name = reformat_collection_name(file_path)
    vector_store = Chroma(
        collection_name=collection_name, persist_directory=persist_directory
    )
    vector_store.delete_collection()


def reformat_collection_name(name: str) -> str:
    """Reformat a filename to a valid Chroma collection name."""
    name = re.sub(r"\.\w+$", "", name)
    name = re.sub(r"[()\s]+", "_", name)
    name = re.sub(r"[^a-zA-Z0-9_-]", "", name)
    name = name.strip("_-")
    return name.ljust(3, "x")[:63] if len(name) < 3 or len(name) > 63 else name


class CustomDocumentLoader:
    def __init__(self, file_path: str):
        self.loader = PyMuPDFLoader(file_path)

    def split_and_create_documents(
        self, chunk_size: int = 2000, chunk_overlap: int = 150
    ) -> List[Document]:
        """Split document into chunks and return Document objects."""
        docs = self.loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        return splitter.split_documents(docs)


class RetrieveWithReranker:
    def __init__(
        self, file_path: str, reranker, embedding, persist_directory: str = "./chromadb"
    ):
        """
        Initialize a RetrieveWithReranker instance.

        Args:
            file_path (str): The path to the PDF file.
            reranker: The reranker model to use.
            embedding: The embedding model to use.
            persist_directory (str, optional): The directory to store the Chroma collection. Defaults to "./chromadb".
        """
        self.reranker = reranker
        loader = CustomDocumentLoader(file_path)
        self.collection_name = reformat_collection_name(file_path)
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            persist_directory=persist_directory,
            embedding_function=embedding,
        )
        documents = loader.split_and_create_documents()
        if not self.vector_store.get()["ids"]:
            self.vector_store.add_documents(documents)
        self.chroma_retriever = self.vector_store.as_retriever(
            search_type="mmr", search_kwargs={"k": 10, "fetch_k": 50}
        )
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = 5 

    def _rerank(self, query: str, documents: List, top_k: int = 1) -> List:
        """Rerank documents or strings based on relevance to the query."""
        contents = []
        if not documents:
            return []
        if isinstance(documents[0], Document):
            contents = [doc.page_content for doc in documents]
        else:
            contents = documents
            
        scores = self.reranker.rerank(query, contents)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

        return [documents[i] for i, score in ranked[:top_k] if score > 0]

    def search(
        self, query: str, keywords: List[str] = None, top_k: int = 1
    ) -> List[Document]:
        """
        Retrieve documents from the PDF file based on the query.

        If the query includes keywords, it will first use BM25 to retrieve documents
        that contain the keywords. Then it will use Chroma to retrieve documents that
        are relevant to the query. The retrieved documents will then be reranked based
        on their relevance to the query.

        Args:
            query (str): The query string.
            keywords (List[str], optional): The keywords to search for. Defaults to None.
            top_k (int, optional): The number of documents to return. Defaults to 1.

        Returns:
            List[Document]: The retrieved documents.
        """
        bm25_docs = []
        if keywords:
            keyword_query = (
                " ".join(self._rerank(query, keywords, top_k=2))
                if len(keywords) > 1
                else keywords[0]
            )
            bm25_docs = self.bm25_retriever.invoke(keyword_query)

        # Lấy tài liệu từ Chroma
        chroma_docs = self.chroma_retriever.invoke(query)

        # Gộp và loại trùng lặp
        all_docs = list(
            {doc.page_content: doc for doc in bm25_docs + chroma_docs}.values()
        )

        # Rerank toàn bộ và trả về top_k
        return self._rerank(query, all_docs, top_k=top_k)
