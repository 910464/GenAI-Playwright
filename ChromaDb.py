import configparser
import json
from typing import List
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.schema.document import Document
from sklearn.metrics.pairwise import cosine_similarity
import os
import numpy as np
from datetime import datetime


class ChromaDBConnector:

    def __init__(self, persist_directory, config_file_path='../Config/config.properties'):
        self.config = configparser.ConfigParser()
        self.config_file_path = config_file_path
        self.embeddings = None
        self.model_name = None
        self.model_path = None
        self.threshold = None
        self.persist_directory = persist_directory
        self.context = ''
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.load_config()

    def load_config(self):
        try:
            self.config.read(self.config_file_path)
            self.model_name = self.config.get('EmbeddingModels', 'embedding_model_name')
            self.model_path = self.config.get("EmbeddingModels", 'embedding_model_path')
            full_model_path = os.path.join(self.model_path, self.model_name)
            self.embeddings = HuggingFaceEmbeddings(model_name=full_model_path)
            self.threshold = self.config.get('EmbeddingModels', 'external_model_threshold')
        except Exception as e:
            print(f"Error loading local model: {e}")
            self.embeddings = HuggingFaceEmbeddings()
            self.threshold = self.config.get('EmbeddingModels', 'default_model_threshold')

    def text_store(self, data, metadata, ids):
        client = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                        collection_metadata={"hnsw:space": "cosine"})
        client.add_texts(data, metadata, ids)
        client.persist()

    def vectordb_store_dir(self, data_path):
        loader = DirectoryLoader(data_path, glob="**/*.csv", loader_cls=CSVLoader)
        data = loader.load()
        db = Chroma.from_documents(
            documents=data,
            embedding=self.embeddings,
            ids=[doc.metadata['source'].split("\\")[-1].split(".")[0] for doc in data],
            persist_directory=self.persist_directory,
            collection_metadata={"hnsw:space": "cosine"}
        )
        db.persist()

    def vectordb_store_doc(self, data_path):
        loader = CSVLoader(data_path)
        data = loader.load()
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        db.persist()
        ids = db.add_documents(documents=data)
        db.persist()
        return len(ids)

    def vectordb_store_code(self, code, f_name):
        data = Document(page_content=code)
        db = Chroma.from_documents(documents=[data], embedding=self.embeddings,
                                   persist_directory=self.persist_directory, ids=[f_name],
                                   collection_metadata={"hnsw:space": "cosine"})
        db.persist()

    def vectordb_store_code_dir(self, data_path):
        loader = DirectoryLoader(data_path, glob="**/*.py", loader_cls=TextLoader)
        data = loader.load()
        db = Chroma.from_documents(documents=data, embedding=self.embeddings,
                                   ids=[doc.metadata['source'].split("\\")[-1].split(".")[0] for doc in data],
                                   persist_directory=self.persist_directory,
                                   collection_metadata={"hnsw:space": "cosine"})
        db.persist()

    def retrieval(self, query, k):
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        return db.similarity_search(query, k=k)

    def retrieval_context(self, query, k):
        retrieval_dir = r"../Data/retrieval_context"
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        docs = db.similarity_search_with_score(query, k=k)
        docs_with_similarity_score = {score: doc.page_content for doc, score in docs}
        retrieved_docs = db.similarity_search(query, k=k)
        for doc in retrieved_docs:
            self.context += (doc.page_content + '\n')

        os.makedirs(retrieval_dir, exist_ok=True)
        output_path = f"{retrieval_dir}/retrieved_{self.timestamp}.txt"
        with open(output_path, "a", encoding="utf-8") as file:
            file.write(self.context)

        return self.context, docs_with_similarity_score, self.threshold

    def get_docs(self):
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        return db.get()

    def get_doc_by_id(self, id):
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        return db.get(ids=[id])

    def embed_csv_with_metadata(self, fpath, metadata):
        embedding_path = self.persist_directory
        os.makedirs(embedding_path, exist_ok=True)
        loader = CSVLoader(file_path=fpath, encoding="utf-8")
        documents = loader.load()
        for doc in documents:
            doc.metadata = metadata
        db = Chroma.from_documents(documents, self.embeddings, persist_directory=embedding_path,
                                   collection_metadata={"hnsw:space": "cosine"})
        db.persist()

    def vector_store(self, fpath):
        embedding_path = self.persist_directory
        os.makedirs(embedding_path, exist_ok=True)
        loader = CSVLoader(file_path=fpath, encoding="utf-8")
        documents = loader.load()
        db = Chroma.from_documents(documents, self.embeddings, persist_directory=embedding_path,
                                   collection_metadata={"hnsw:space": "cosine"})
        db.persist()

    def get(self):
        return self.get_docs()

    def retrieve_filtered(self, query: str, k: int, filters: dict) -> List[Document]:
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        return db.similarity_search(query, k=k, filter=filters)

    def retrieve_filtered_with_score(self, query: str, k: int, filters: dict):
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        return db.similarity_search_with_score(query, k=k, filter=filters)

    def decode_json_objects(self, json_string):
        return [json.loads(obj) for obj in json_string.split('\n') if obj.strip()]

    def get_context_by_id(self, context_key):
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        filters = {"context_key": context_key}
        results = db.get(where=filters)
        if results['documents']:
            return json.loads(results['documents'][0])
        return None

    def update_context_in_chromadb(self, context, context_key):
        existing_context = self.get_context_by_id(context_key)
        if existing_context != context:
            self.delete_context_by_id(context_key)
            self.store_context_in_chromadb(context, context_key)
        else:
            print(f"Context for key: {context_key} is already up-to-date.")

    def store_context_in_chromadb(self, context, context_key):
        context_json = json.dumps(context)
        data = [context_json]
        metadata = [{"source": "crawl_function", "context_key": context_key}]
        ids = [context_key]
        self.text_store(data=data, metadata=metadata, ids=ids)

    def delete_context_by_id(self, context_key):
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        filters = {"context_key": context_key}
        results = db.get(where=filters)
        db.delete(ids=results['ids'])

    def retrieval_html_context(self, query, context_key):
        retrieval_dir = r"../Data/RetrievalContext"
        os.makedirs(retrieval_dir, exist_ok=True)
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        filters = {"context_key": context_key}
        docs = db.get(where=filters)
        docs_with_similarity = {}
        self.context = ""

        for doc in docs['documents']:
            docs_with_similarity = doc
            self.context += (doc + '\n')

        try:
            filtered_elements = self.decode_json_objects(self.context)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None, None, None

        filtered_elements = self.filter_elements_with_similarity(filtered_elements, query)
        output_path = f"{retrieval_dir}/retrieved_{self.timestamp}.txt"
        with open(output_path, "a", encoding="utf-8") as file:
            file.write(self.context)

        return json.dumps(filtered_elements), docs_with_similarity, self.threshold

    def filter_elements_with_similarity(self, context, query, top_k=20):
        query_embedding = self.embeddings.embed_query(query)
        similarities = []
        unique_elements = set()
        flattened_context = [item for sublist in context for item in sublist]
        elements = [item for item in flattened_context if "element" in item and item["element"]]
        element_texts = [item["element"] for item in elements]
        element_embeddings = self.embeddings.embed_documents(element_texts)
        query_embedding = np.array(query_embedding).reshape(1, -1)
        element_embeddings = np.array(element_embeddings)
        cosine_similarities = cosine_similarity(query_embedding, element_embeddings)[0]

        for idx, item in enumerate(elements):
            unique_id = f"{item['xpath']}-{item['element']}"
            if unique_id not in unique_elements:
                similarities.append((item, cosine_similarities[idx]))
                unique_elements.add(unique_id)

        similarities.sort(key=lambda x: x[1], reverse=True)
        return [element for element, similarity in similarities[:top_k]]
