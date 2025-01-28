import os

import nltk
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_ollama import OllamaLLM

# Set custom NLTK data path
nltk_data_dir = os.path.join(os.path.dirname(__file__), "nltk_data")
os.environ["NLTK_DATA"] = nltk_data_dir
os.makedirs(nltk_data_dir, exist_ok=True)

# Download to custom directory
nltk.download("punkt_tab", download_dir=nltk_data_dir)
nltk.download("averaged_perceptron_tagger_eng", download_dir=nltk_data_dir)


# Document loading
def load_documents(directory):
    documents = []
    for file in os.listdir(directory):
        print(f"Loading file: {file}..")
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(directory, file))
            documents.extend(loader.load())
        elif file.endswith(".docx"):
            loader = UnstructuredWordDocumentLoader(os.path.join(directory, file))
            documents.extend(loader.load())
        elif file.endswith(".pptx"):
            loader = UnstructuredPowerPointLoader(os.path.join(directory, file))
            documents.extend(loader.load())
    return documents


# Text splitting
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
    model_kwargs={"device": "cpu"},
)

# OpenSearch connection and index settings
opensearch_url = "http://localhost:9200"
index_name = "sox_plus_knn"

# Vector index mapping
index_mapping = {
    "mappings": {
        "properties": {
            "text": {"type": "text"},
            "vector": {
                "type": "knn_vector",
                "dimension": 384,  # MiniLM-L6 dimension
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "nmslib",
                    "parameters": {"ef_construction": 128, "m": 16},
                },
            },
        }
    }
}

# Create vector store
vector_store = OpenSearchVectorSearch(
    index_name=index_name,
    embedding_function=embeddings,
    opensearch_url=opensearch_url,
    index_body=index_mapping,
    bulk_size=2048,
)

# Main execution
docs = load_documents("Documents")
splits = text_splitter.split_documents(docs)


# if not vector_store.index_exists():
# vector_store.delete_index()
print("Storing embedding of documents..")
vector_store.add_documents(splits)
print("Done loading documents successfully.")
# else:
#     print(f"Using existing vector index {index_name}..")

# print("\n\n\n")

# # Setup QA chain
# llm = OllamaLLM(model="mistral")
# qa_chain = RetrievalQA.from_chain_type(
#     llm=llm, retriever=vector_store.as_retriever(search_kwargs={"k": 3})
# )

# # query = "List all the relevant policies impacting the process area"
# # print("---- querying model without RAG context ----")
# # print(query)
# # response = llm.invoke(query)
# # print(response)

# # Example query
# query = """
# Create a comprehensive, optimal questionnaire that will be given to a Corporate Procurement Specialist as part of assessing SOX Readiness of the employee's company, Asian Infrastructure Investment Bank. The end goal is to construct a SOX Narrative for each Process Cycle in the company based on answers to questionnaires from all relevant employees at the company. Only 1 questionnaire will be administered to the employee, so make sure the questionnaire covers all information needed to eventually make an optimal SOX narrative for the company, and all questions should be fun, engaging, and gamified where appropriate. Fully read the attached documents before you prepare the questionnaire.
# """
# print("---- querying model with RAG context ----")
# response = qa_chain.invoke({"query": query})
# print(query)
# print(response["result"])
