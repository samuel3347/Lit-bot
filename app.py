# importing all the important libraries
import streamlit as st
from dotenv import load_dotenv,find_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from openai import Client, completions, OpenAI
import os 


st.set_page_config(page_title="Multiple-PDF-Bot", page_icon=":books:")

st.header("Let's Study!!!:books:")

#reading the document
def get_pdf_text(pdf_docs):
    text = "" 
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

#converting the text read into chunks
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    #splitting the text 
    chunks = text_splitter.split_text(text)
    return chunks

#chunks of data into vectorDB
def get_vectorstore(text_chunks, api_key1):
    #embeddings = HuggingFaceInstructEmbeddings(model_name='hkunlp/instructor-xl')
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=os.environ.get('OPENAI_API_KEY'))
    vector_store = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

    load_dotenv(find_dotenv())

def get_conversational_chain(context, user_question):
    client = Client(api_key=os.environ.get('OPENAI_API_KEY'))
    prompt_template = "Please answer the question with reference to the document provided."

    prompt = f"Document: {context}\nQuestion: {user_question}\n{prompt_template}"

    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        temperature=0.5,
        max_tokens=550  
    )
    return response.choices[0].text

def user_input(user_question, document_text):
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002",api_key=os.environ.get('OPENAI_API_KEY'))
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)

    response_text = get_conversational_chain(document_text, user_question)

    st.write("Reply: ", response_text) 


api_key = os.environ.get('OPENAI_API_KEY')


def main():
    user_question = st.text_input("Ask a Question related to the PDF Files that you uploaded", key="user_question")
    document_text=""

    if user_question and api_key: 
        user_input(user_question, document_text)
    

    with st.sidebar:
        st.subheader("Documents")
        pdf_docs = st.file_uploader("Upload your PDFs",accept_multiple_files=True)
        if st.button("Process"):
            with st.spinner("Processing"):
                # get the pdf text 
                raw_text = get_pdf_text(pdf_docs)

                # get the text chunks
                text_chunks = get_text_chunks(raw_text)
                
                #create vectorstore
                get_vectorstore(text_chunks, api_key)

                st.success("Done")
                

if __name__ == '__main__':
    main() 
