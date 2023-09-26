"""
This module script file contains functionality to load relevant emails in html format and
preprocess them using langchain to later feed into our future overlord ChatGPT.

LIMITATIONS: Currently, no account is taken of global context and local context in metadata during text splitting.
                This has to be implemented in the future for quality response when prompting model.
                Also time dimension must be implemented.
"""

import sys
from langchain import PromptTemplate, LLMChain
from langchain.document_loaders import UnstructuredHTMLLoader, DirectoryLoader
from langchain.document_transformers import Html2TextTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from dotenv import load_dotenv

load_dotenv()

# Step 1: Load html files
def load_transform_data():
    # loader = UnstructuredHTMLLoader("email_data_html/Thu 14 Sep 2023 031819 0700 PDT  Astroturfed.html")
    # html_document = loader.load() # This document is now already formatted (html tags, css etc. removed)
    loader = DirectoryLoader("email_data_html/")
    html_docs = loader.load()

    # Step 2: Transform html to text
    html2Text = Html2TextTransformer()
    text_docs = html2Text.transform_documents(html_docs) # Adds additional formating (handels special characters etc.) to make it as readable as possible
    return text_docs

# Step 3: Split documents into chunks
def split_document():
    text_docs = load_transform_data()
    chunks = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=32)
    for chunk in splitter.split_documents(text_docs): # If not working -> use split_text
        chunks.append(chunk)
    return chunks

# Step 4: Create or load a vectorstore of embeddings.
embeddings = OpenAIEmbeddings()

# Should only be run once when new data is processed (once a day when scheduled)
def create_vectorstore_index():
    chunks = split_document()
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    search_index = Chroma.from_texts(texts, embeddings, metadatas=metadatas, persist_directory="stored_index")
    return search_index

# Should be run whenever a query is submitted
def get_vectorstore_index():
    vectorstore = Chroma(persist_directory="stored_index", embedding_function=embeddings)
    index = VectorStoreIndexWrapper(vectorstore=vectorstore)
    return vectorstore, index # First var needed for manual retrieval, second var for retrieval chain

# Step 5: Similarity search of vectorstore database
def retrieve_info(query, vectorstore):
    matched_docs = vectorstore.similarity_search(query, k=4)
    # Code below not really usefull as matched_docs contains the page_content and metadata
    sources = []
    for doc in matched_docs:
        sources.append(
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata,
            }
        )
    return matched_docs

# Step 6: Interface LLM
def interface_llm(question):
    """This function is meant for 1 time prompting and includes prompt templates"""

    # Always retrieve from vector database when interfacing LLM
    vectorstore, _ = get_vectorstore_index()
    llm = ChatOpenAI(temperature=0.5, model="gpt-3.5-turbo")
    matched_docs = retrieve_info(question, vectorstore)

    template = """
    Please use the following context to answer questions.
    Context: {context}
    ---
    Question: {question}
    Answer: Let's think step by step."""

    context = "\n".join([doc.page_content for doc in matched_docs])
    prompt = PromptTemplate(input_variables=["context", "question"], template=template).partial(context=context)
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    response = llm_chain.run(question)
    return response

def interface_llm_chain():
    """This function enables a terminal conversation and includes conversation history"""
    _, index = get_vectorstore_index()
    llm = ChatOpenAI(temperature=0.5, model="gpt-3.5-turbo")

    custom_template = """
    Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question. Answer the question by thinking step by step.
    Chat History:
    {chat_history}
    Follow Up Input: {question}
    Standalone question:"""

    CUSTOM_QUESTION_PROMPT = PromptTemplate.from_template(custom_template)

    # The similarity search in this approach is done by the retriever
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=index.vectorstore.as_retriever(search_kwargs={"k":2}),
        return_source_documents=True,
        condense_question_prompt=CUSTOM_QUESTION_PROMPT
    )
    return chain


# TODO: iterate over all html files in the map, transform, save as txt in new map, read again, embed, store embedding, delete text
# TODO: add separate metadata for time
