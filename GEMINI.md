# DocSentry Project Context

## Project Overview

DocSentry is a web application designed to detect sensitive data within PDF documents. It utilizes a Retrieval-Augmented Generation (RAG) approach, leveraging LangChain for orchestration, OpenAI for embeddings and Large Language Model (LLM) interactions, and FAISS for in-memory vector storage of document embeddings.

The application features a client-server architecture:
-   **Frontend:** A React application built with Vite, handling user interactions, file uploads, and displaying chat responses.
-   **Backend:** A FastAPI server, responsible for processing PDF documents, chunking text, generating and storing embeddings, and querying the LLM to identify sensitive information.

The primary goal is to provide a user-friendly interface to upload documents and query for specific types of confidential information using natural language prompts.

## Key Technologies

*   **Backend:** Python 3.8+, FastAPI, LangChain, OpenAI API, FAISS.
*   **Frontend:** Node.js 18+, React, Vite, npm, Axios.

## Building and Running

To set up and run the DocSentry application, you need to start both the backend and frontend servers.

### Prerequisites

*   Python 3.8 or higher.
*   Node.js 18 or higher (includes `npm`).
*   An OpenAI API Key.

### Backend Setup & Run

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  Create and activate a Python virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate # On macOS/Linux
    # OR
    .\venv\Scripts\activate # On Windows
    ```
3.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
4.  Create a `.env` file in the `backend` directory and add your OpenAI API key:
    ```
    OPENAI_API_KEY="your-openai-api-key-here"
    ```
5.  Start the FastAPI server:
    ```bash
    uvicorn main:app --reload
    ```
    The backend will typically run on `http://127.0.0.1:8000`.

### Frontend Setup & Run

1.  Navigate to the `frontend` directory (from the project root, or `cd ../frontend` if in `backend`):
    ```bash
    cd frontend
    ```
2.  Install the required Node.js packages:
    ```bash
    npm install
    ```
3.  Start the Vite development server:
    ```bash
    npm run dev
    ```
    The frontend will typically be available at `http://localhost:5173`.

## Development Conventions

*   **Dependency Management:** Python dependencies are managed via `requirements.txt`, and Node.js dependencies via `package.json`.
*   **Environment Variables:** Sensitive information like API keys are managed using `.env` files, specifically `OPENAI_API_KEY` for the backend. These files are typically excluded from version control.
*   **Code Structure:** The project is divided into `backend` (FastAPI) and `frontend` (React) directories, promoting a clear separation of concerns.
*   **RAG Implementation:** LangChain is used for orchestrating the RAG pipeline, demonstrating a modular approach to integrating LLMs and vector stores.
*   **Temporary Embeddings:** The current implementation uses in-memory FAISS for embeddings, indicating a convention of prioritizing quick setup over persistent storage, with a noted potential improvement for persistence.

## Potential Improvements (as identified in README.md)

*   Implement FAISS Persistence to avoid reprocessing PDFs.
*   Support more file types (e.g., `.docx`, `.txt`, `.csv`).
*   Allow alternative models/embeddings beyond OpenAI.
*   Enhance security with user authentication/authorization.
*   Improve scalability for larger documents or higher traffic.
