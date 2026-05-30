from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


def extract_text_from_pdf(pdf_file):
    pdf_file.seek(0)
    reader = PdfReader(pdf_file)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


def create_chunks(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_text(text)
    return chunks


def get_embedding_model():
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    return embedding_model


def store_chunks_in_chroma(chunks):
    embedding_model = get_embedding_model()

    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embedding_model
    )

    return vectorstore




def process_resume(uploaded_file):
    resume_text = extract_text_from_pdf(uploaded_file)
    resume_chunks = create_chunks(resume_text)
    vectorstore = store_chunks_in_chroma(resume_chunks)

    return resume_text, resume_chunks, vectorstore

