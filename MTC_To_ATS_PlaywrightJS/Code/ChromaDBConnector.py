import configparser
import json
from typing import List

# import langchain_core.documents
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.schema.document import Document
from sklearn.metrics.pairwise import cosine_similarity
from langchain.document_loaders.base import BaseLoader
import os
import chromadb
from datetime import datetime
import numpy as np

# class vectordb:
#
#     def connect(self, collection_name):
#         client = chromadb.PersistentClient(path="./chroma_database")
#         collection = client.get_or_create_collection(name=collection_name)
#         return collection
#
#     def add_collection(self, collection_name, data, metadata, id_list):
#         collection = self.connect(collection_name)
#         collection.add(
#             documents=data,
#             metadatas=metadata,  # [{"source": "my_source"}, {"source": "my_source"}]
#             ids=id_list  # ["id1", "id2"]
#         )
#
#     def query(self, collection_name, query_text, n):
#         collection = self.connect(collection_name)
#         results = collection.query(
#             query_texts=[query_text],
#             n_results=n
#         )
#         # print(results)
#         return results

class ChromaDBConnector:

    def __init__(self, persist_directory,config_file_path='../Config/config.properties'):
        self.config = configparser.ConfigParser()
        self.config_file_path = config_file_path
        self.embeddings = None
        self.model_name = None
        self.model_path = None
        self.threshold = None
        self.persist_directory = persist_directory
        self.context = ''
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # updates the instance variables according to the config.properties file
        self.load_config()

    def load_config(self):
        try:
            # Reading the properties defined in the config.properties file
            # updating the model_name and model_path
            self.config.read(self.config_file_path)
            self.model_name = self.config.get('EmbeddingModels', 'embedding_model_name')
            self.model_path = self.config.get("EmbeddingModels", 'embedding_model_path')
            self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name, cache_folder=self.model_path)
            self.threshold = self.config.get('EmbeddingModels', 'external_model_threshold')
        except:
            # updating the threshold value from config.properties file with default_model threshold.
            self.embeddings = HuggingFaceEmbeddings()
            self.threshold = self.config.get('EmbeddingModels', 'default_model_threshold')

    def text_store(self,data,metadata,ids):
        client = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,collection_metadata={"hnsw:space": "cosine"})
        client.add_texts(data, metadata, ids)
        client.persist()

    def vectordb_store_dir(self, data_path):
        loader = DirectoryLoader(data_path, glob="**/*.csv", loader_cls=CSVLoader)
        data = loader.load()

        # load it into Chroma
        db = Chroma.from_documents(documents=data, embedding=self.embeddings,
                                   ids=[doc.metadata['source'].split("\\")[-1].split(".")[0] for doc in data], persist_directory=self.persist_directory,collection_metadata={"hnsw:space": "cosine"})
        db.persist()

    def vectordb_store_doc(self, data_path):
        loader = CSVLoader(data_path)
        data = loader.load()
        # print(data)
        # load it into Chroma
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,collection_metadata={"hnsw:space": "cosine"})
        db.persist()
        ids = db.add_documents(documents=data)
        db.persist()
        return len(ids)

    def vectordb_store_code(self, code, f_name):
        data = Document(page_content=code)

        # load it into Chroma
        db = Chroma.from_documents(documents=[data], embedding=self.embeddings,
                                   persist_directory=self.persist_directory, ids=[f_name],collection_metadata={"hnsw:space": "cosine"})
        db.persist()

    def vectordb_store_code_dir(self, data_path):
        loader = DirectoryLoader(data_path, glob="**/*.py", loader_cls=TextLoader)
        data = loader.load()

        # load it into Chroma
        db = Chroma.from_documents(documents=data, embedding=self.embeddings,
                                   ids=[doc.metadata['source'].split("\\")[-1].split(".")[0] for doc in data], persist_directory=self.persist_directory,collection_metadata={"hnsw:space": "cosine"})
        db.persist()

    def retrieval(self, query, k):
        # if os.path.exists(self.persist_directory) and os.path.isdir(self.persist_directory):
        #     print("The folder exists.")
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,collection_metadata={"hnsw:space": "cosine"})
        retrieved_docs = db.similarity_search(query, k=k)
        return retrieved_docs

    def retrieval_context(self, query, k):

        retrieval_dir = r"../Data/retrieval_context"
        # try:
        #     os.makedirs(retrieval_dir, exist_ok=True)
        # except OSError as e:
        #     print(f"Error creating directory: {e}")

        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,collection_metadata={"hnsw:space": "cosine"})
        docs = db.similarity_search_with_score(query, k=k)
        docs_with_similarity_score = {}
        for doc,score in docs:
            print(score,doc)
            docs_with_similarity_score[score]=doc.page_content
        retrieved_docs = db.similarity_search(query, k=k)
        for doc in retrieved_docs:
            content = doc.page_content
            self.context += (content + '\n')

        output_path = f"{retrieval_dir}/retrieved_{self.timestamp}.txt"
        with open(output_path, "a", encoding="utf-8") as file:
            file.write(self.context)
        print(self.threshold)
        return self.context, docs_with_similarity_score,self.threshold


    def get_docs(self):
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,collection_metadata={"hnsw:space": "cosine"})
        return db.get()

    def get_doc_by_id(self, id):
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,collection_metadata={"hnsw:space": "cosine"})
        return db.get(ids=[id])

    def embed_csv_with_metadata(self, fpath, metadata):

        embedding_path = self.persist_directory

        try:
            os.makedirs(embedding_path, exist_ok=True)
        except OSError as e:
            print(f"Error creating directory: {e}")

        # load the json data
        # loader = DataFrameLoader(df, page_content_column=df.columns)
        loader = CSVLoader(file_path=fpath, encoding="utf-8")
        documents = loader.load()

        # add metadata
        for document in documents:
            document.metadata = metadata

        # load it into Chroma
        db = Chroma.from_documents(documents, self.embeddings, persist_directory=embedding_path,collection_metadata={"hnsw:space": "cosine"})
        db.persist()

    def vector_store(self, fpath):

        embedding_path = self.persist_directory

        try:
            os.makedirs(embedding_path, exist_ok=True)
        except OSError as e:
            print(f"Error creating directory: {e}")

        # load the json data
        # loader = DataFrameLoader(df, page_content_column=df.columns)
        loader = CSVLoader(file_path=fpath, encoding="utf-8")
        documents = loader.load()

        # load it into Chroma
        db = Chroma.from_documents(documents, self.embeddings, persist_directory=embedding_path,
                                   collection_metadata={"hnsw:space": "cosine"})
        db.persist()

    def get(self):
        return self.get_docs()

    def retrieve_filtered(self, query: str, k: int, filters: dict) -> List[Document]:
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,collection_metadata={"hnsw:space": "cosine"})
        retrieved_docs = db.similarity_search(query, k=k, filter=filters)
        return retrieved_docs

    def retrieve_filtered_with_score(self, query: str, k: int, filters: dict):
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,collection_metadata={"hnsw:space": "cosine"})
        retrieved_docs = db.similarity_search_with_score(query, k=k, filter=filters)
        return retrieved_docs

    def decode_json_objects(self, json_string):
        json_objects = json_string.split('\n')
        decoded_objects = []
        for obj in json_objects:
            if obj.strip():  # Skip empty lines
                decoded_objects.append(json.loads(obj))
        return decoded_objects

    def get_context_by_id(self, context_key):
        """
        Retrieve the context for a given key from ChromaDB.
        """
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        filters = {"context_key": context_key}
        results = db.get(where=filters)
        if results['documents']:
            # Assuming the first document is the one we want
            doc = results['documents'][0]
            return json.loads(doc)  # Convert JSON string back to dictionary
        return None

    def update_context_in_chromadb(self, context, context_key):
        """
        Update the context for a given key in ChromaDB.
        """
        # Retrieve the existing context
        existing_context = self.get_context_by_id(context_key)
        if existing_context:
            # Compare existing context with the new context
            if existing_context != json.dumps(context):
                # Delete the existing context
                self.delete_context_by_id(context_key)
                # Store the new context
                self.store_context_in_chromadb(context, context_key)
                # print(f"Updated context for key: {context_key}")
            else:
                print(f"Context for key: {context_key} is already up-to-date.")
        else:
            # If no existing context, store the new context
            self.store_context_in_chromadb(context, context_key)
            print(f"Stored new context for key: {context_key}")

    def store_context_in_chromadb(self, context, context_key):
        context_json = json.dumps(context)
        data = [context_json]
        metadata = [{"source": "crawl_function", "context_key": context_key}]
        ids = [context_key]  # Use the context_key directly as the ID

        self.text_store(data=data, metadata=metadata, ids=ids)

    def delete_context_by_id(self, context_key):
        """
        Delete the context for a given key from ChromaDB.
        """
        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        filters = {"context_key": context_key}
        # print(f"Filters: {filters}")  # Debug print to check filters

        # Retrieve the documents that match the key
        results = db.get(where=filters)
        # print(f"Results: {results}")  # Debug print to check results

        # Extract the IDs directly from the results
        ids_to_delete = results['ids']
        # print(f"IDs to delete: {ids_to_delete}")  # Debug print to check IDs

        # Delete the documents using the retrieved IDs
        db.delete(ids=ids_to_delete)
        # print(f"Deleted context for key: {context_key}")

    def retrieval_html_context(self, query, context_key):
        retrieval_dir = r"../Data/RetrievalContext"

        # Create the directory if it doesn't exist
        os.makedirs(retrieval_dir, exist_ok=True)

        db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"})
        filters = {"context_key": context_key}
        docs = db.get(where=filters)
        docs_with_similarity = {}
        self.context = ""
        for doc in docs['documents']:
            # print(score, doc)
            docs_with_similarity = doc

        retrieved_docs = db.get(where=filters)
        for doc in retrieved_docs['documents']:
            content = doc
            self.context += (content + '\n')
        # Debugging: Print the retrieved context
        # print("Retrieved context:", self.context)

        # Decode JSON objects if necessary
        try:
            filtered_elements = self.decode_json_objects(self.context)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None, None, None

        # Filter elements based on the query using cosine similarity
        filtered_elements = self.filter_elements_with_similarity(filtered_elements, query)

        # Debugging: Print the filtered elements
        # print("Filtered elements:", filtered_elements)

        output_path = f"{retrieval_dir}/retrieved_{self.timestamp}.txt"
        with open(output_path, "a", encoding="utf-8") as file:
            file.write(self.context)
        # print(self.threshold)
        return json.dumps(filtered_elements), docs_with_similarity, self.threshold

    def filter_elements_with_similarity(self, context, query, top_k=20):
        query_embedding = self.embeddings.embed_query(query)
        similarities = []
        unique_elements = set()

        # Flatten the nested list of dictionaries
        flattened_context = [item for sublist in context for item in sublist]

        # Filter elements with the key "element"
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
        filtered_elements = [element for element, similarity in similarities[:top_k]]

        return filtered_elements