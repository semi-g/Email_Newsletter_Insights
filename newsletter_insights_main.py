"""
This is the main project file.
Project description: 
    1. Make API call to gmail to retrieve relevant newsletter emails and store as html files
    2. Load the files, transform and chunk them into equal length chunks
    3. Embed to create a knowledge base (ensure a time dimension is present -> either in documents or as metadata)
    4. Create an advanced prompt template incorporating useful prompt engineering techniques (role, one-shot, chain of tought etc.)
        and specify the importance of time dimension
    5. Create pipeline for querying the knowledge base and process the outputs in gpt-3.5-turbo
    6. Schedule to run daily (try Task Scheduler) and create a summary file with all important (relevant) information
    7. Try to add explainability functionality -> using metadata, AI must be able to tell where it got the answer from
        (document title, page) when asked.
"""

import langchain_processing
import streamlit as st
import sys


# TODO: later build with streamlit
def main():
    chain = langchain_processing.interface_llm_chain()

    prompt = None
    chat_history = []
    while True:
        if not prompt:
            prompt = input("Prompt: ")
        if prompt in ["exit"]:
            sys.exit()
        result = chain({"question": prompt, "chat_history": chat_history})
        print(result["answer"])
        print(result['source_documents'][0].metadata)
        
        chat_history.append((prompt, result["answer"]))
        prompt = None

if __name__ == "__main__":
    main()
   


