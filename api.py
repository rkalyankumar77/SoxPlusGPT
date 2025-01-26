from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Query(BaseModel):
    text: str
    use_rag: bool = True


class Message(BaseModel):
    text: str
    is_bot: bool


# Initialize components
llm = OllamaLLM(model="mistral")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={"device": "cpu"}
)
vector_store = OpenSearchVectorSearch(
    index_name="sox_plus_knn",
    embedding_function=embeddings,
    opensearch_url="http://localhost:9200",
)


@app.post("/chat", response_model=Message)
async def chat(query: Query):
    try:
        if query.use_rag:
            results = vector_store.similarity_search_with_score(query.text, k=3)
            context = "\n".join([doc.page_content for doc, _ in results])
            prompt = f"Context: {context}\nQuestion: {query.text}"
            response = llm.invoke(prompt)
        else:
            response = llm.invoke(query.text)

        return Message(text=response, is_bot=True)
    except Exception as e:
        print(f"Error details: {str(e)}")  # Add this line for detailed logging
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
