import dotenv
from typing_extensions import List
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.retrievers import BM25Retriever
import re

dotenv.load_dotenv()


def reformat_collection_name(name):
    """
    Reformat a filename to a valid Chroma collection name.

    The rules are as follows:

    - Remove the file extension.
    - Replace spaces, parentheses, and other special characters with underscores.
    - Remove any other non-alphanumeric characters.
    - Replace any double periods with a single period.
    - Remove any leading or trailing underscores or hyphens.
    - If the result is less than 3 characters, pad with "x"s.
    - If the result is more than 63 characters, truncate.

    Args:
        name (str): The filename to reformat.

    Returns:
        str: The reformatted collection name.
    """

    name = re.sub(r"\.\w+$", "", name)
    name = re.sub(r"[()\s]+", "_", name)
    name = re.sub(r"[^a-zA-Z0-9_-]", "", name)
    name = re.sub(r"\.\.", ".", name)
    name = name.strip("_-")
    if len(name) < 3:
        name = name.ljust(3, "x")
    elif len(name) > 63:
        name = name[:63]
    return name


class CustomDocumentLoader:
    def __init__(self, file_path: str):
        """
        Initialize the PyMuPDFLoader with the specified file path.

        Args:
            file_path (str): The path to the file to be loaded by the document loader.
        """

        self.doc = PyMuPDFLoader(file_path)

    def split_and_create_documents(self, chunksize=2000, overlap=150) -> List[Document]:
        """
        Split the loaded document into smaller chunks and create Document objects.

        Args:
            chunksize (int, optional): The maximum size of each document chunk. Defaults to 2000.
            overlap (int, optional): The number of overlapping characters between chunks. Defaults to 150.

        Returns:
            List[Document]: A list of Document objects representing the split document.
        """

        documents = self.doc.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunksize, chunk_overlap=overlap
        )
        documents = text_splitter.split_documents(documents)
        return documents


def delete_collection(file_path: str) -> None:
    """
    Delete the Chroma collection associated with the specified file path.

    Args:
        file_path (str): The path to the file whose Chroma collection is to be deleted.

    Returns:
        None
    """
    loader = CustomDocumentLoader(file_path)
    vector_store = Chroma(
        collection_name=reformat_collection_name(loader.doc.source),
        persist_directory="./chromadb",
    )
    vector_store.delete_collection()


class RetrieveWithReranker:
    """A Hybrid Retriever with Reranker using Chroma, BM25 and FastEmbed TextCrossEncoder.

    Args:
        file_path (str): The path to the PDF file.
        reranker (TextCrossEncoder): The reranker model.
        embedding (FastEmbedEmbeddings): The embedding model.
        persist_directory (str): The directory to persist the Chroma vector store.
    """

    def __init__(
        self, file_path: str, reranker, embedding, persist_directory="./chromadb"
    ):
        """
        Initialize the RetrieveWithReranker instance with the given file path, reranker, embedding model, and persist directory.

        Args:
            file_path (str): The path to the PDF file.
            reranker (TextCrossEncoder): The reranker model.
            embedding (FastEmbedEmbeddings): The embedding model.
            persist_directory (str, optional): The directory to persist the Chroma vector store. Defaults to "./chromadb".

        Returns:
            None
        """
        self.reranker = reranker
        loader = CustomDocumentLoader(file_path)
        vector_store = Chroma(
            collection_name=reformat_collection_name(loader.doc.source),
            persist_directory=persist_directory,
            embedding_function=embedding,
        )
        documents = loader.split_and_create_documents()
        if len(vector_store.get()["ids"]) == 0:
            vector_store.add_documents(documents)
        self.chroma_retriever = vector_store.as_retriever(
            search_type="mmr", search_kwargs={"k": 10, "fetch_k": 50}
        )
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = 2

    def _rerank(self, query: str, documents: list, return_k: int = 2):
        """
        Rerank the given list of documents based on their relevance to the given query.

        This function takes a query string and a list of documents (either as strings or Document objects)
        and returns the top-k documents that are most relevant to the query.

        Args:
            query (str): The query string to rerank the documents against.
            documents (list): The list of documents to rerank.
            return_k (int, optional): The number of top documents to return. Defaults to 2.

        Returns:
            list: The top-k documents that are most relevant to the query.
        """
        scores = []
        if not isinstance(documents[0], str):
            scores = self.reranker.rerank(
                query, [doc.page_content for doc in documents]
            )
        else:
            scores = self.reranker.rerank(query, documents)
        scores_with_idx = [(index, score) for index, score in enumerate(scores)]
        scores_with_idx.sort(key=lambda x: x[1], reverse=True)
        result = []
        for i in scores_with_idx[:return_k]:
            if i[1] > 0:
                result.append(documents[i[0]])
        return result

    def search(self, query: str, keywords: List[str] = None) -> List[Document]:
        """
        Perform Hybrid search for documents relevant to the given query.
        This function uses a combination of reranking and retrieval techniques
        to find documents that best match the provided query and set of keywords.
        It first identifies the most relevant keywords using the reranker, then
        retrieves documents using both BM25 and Chroma retrievers. The results
        from both retrievers are combined and returned.

        Args:
            query (str): The query string to search documents against.
            keywords (List[str]): A list of keywords from the main question.

        Returns:
            List[Document]: A list of 5 Document objects that are most relevant to the query.
                - The 2 most relevant documents from the BM25 retriever.
                - The most relevant documents document from the Chroma retriever.
                - The 2 most relevant documents from the Chroma retriever after reranking.
        """
        bm25_docs = []
        if keywords:
            most_relevant_keywords = ''
            reranked_keywords = self._rerank(query, keywords)
            if len(reranked_keywords) == 0:
                most_relevant_keywords = keywords[0]
            else:
                most_relevant_keywords = reranked_keywords[0]
            bm25_docs = self.bm25_retriever.invoke(most_relevant_keywords)
        chroma_docs = self.chroma_retriever.invoke(query)
        chroma_docs_reranked = self._rerank(query, chroma_docs, return_k=2)
        if len(chroma_docs_reranked) == 0:
            return []
        return bm25_docs + chroma_docs_reranked + chroma_docs[:1]
