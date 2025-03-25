# PDF-RAG 
<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
        <li><a href="#project-features">Project Features</a></li>
        <li><a href="#question-processing-workflow">Question Processing Workflow</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
  </ol>
</details>

# About the project
This is a personal **Question-Answering (QA) project for PDF documents**, allowing users to **upload local PDF files**. The system processes the document's content and provides answers based on user questions.  


### Built With
* [![Gradio][Gradio.js]][Gradio-url]
* [![OpenRouter][OpenRouter.js]][OpenRouter-url]
* [![LangChain][LangChain.js]][LangChain-url]
* [![LangGraph][LangGraph.js]][LangGraph-url]
* [![OpenAI][OpenAI-badge]][OpenAI-url]  
* [![FastEmbed][FastEmbed-badge]][FastEmbed-url]
* [![ChromaDB][ChromaDB.js]][ChromaDB-url]

## **Question Processing Workflow**
<p align="center"><img alt="Question Handler Graph" src="https://github.com/gianghp123/PDF-RAG/graph_pngs/question_handler_graph.png" height="600"></p>
This workflow is designed to process user queries by combining multiple information retrieval and prompt engineering techniques. Below is a detailed breakdown of each step:

---

### **1. Preprocessing & Retrieval**

#### **a. Keyword Extraction**
- Extracts keywords from the query using **KeyBERT** for BM25 retrieval.

#### **b. Hybrid Retrieval**
- Combines:
  - **BM25**: Uses top 2 keywords to fetch **5 documents**.
  - **ChromaDB with MMR**: Retrieves **10 documents** using Maximal Marginal Relevance.
  - **Reranking**: Merges unique documents, selects **top 1** with score > 0.
- **Stops if**: No documents score > 0, outputs *"The question seems to be not related to the current document or cannot be answered"*.

---

### **2. Evaluation & Refinement**

- **Completeness Check**: 
  - Sufficient info → Generate answer.
  - Insufficient → Rewrite query (once).
- **Query Rewriting**: Simplifies query while keeping its focus.

---

### **3. Routing & Decomposition**

- **Sub-Questions**: Breaks query into smaller parts.
- **Routing**: 
  - Independent sub-questions → **Decomposing handler**.
  - Context-dependent → **Reasoning handler**.

---

### **4. Decomposing Question Handler**
<p align="center"><img alt="Question Handler Graph" src="https://github.com/gianghp123/PDF-RAG/graph_pngs/decomposing_question_handler_graph.png" height="400"></p>

- Processes sub-questions via:
  1. Retrieve documents.
  2. Grade relevance.
  3. Answer if sufficient, or rewrite (once) if not.
  4. Combine info to answer, then aggregate all sub-answers.

---

### **5. Reasoning Question Handler**
<p align="center"><img alt="Question Handler Graph" src="https://github.com/gianghp123/PDF-RAG/graph_pngs/reasoning_question_handler_graph.png" height="500"></p>

- **Thoughts**: Generates one idea per step, avoiding redundancy.
- **Observations**: Answers thoughts using retrieved documents, rewriting once if needed.
- **Loop**: Continues until sufficient info is gathered, then compiles answer.

---

### **6. Final Formatting**
- Formats response in **Markdown** for the frontend.


# Getting Started

## Prerequisites

Ensure you have the following installed on your system before proceeding:

- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend, recommended LTS version)
- **npm** or **yarn** (for frontend package management)
- **MySQL** (for database management)
## Installation

### Backend Setup

#### 1. Create a Virtual Environment
Navigate to the `backend` folder and create a virtual environment:

```sh
cd backend
python -m venv venv
```

Activate the virtual environment:
- **Windows:**
  ```sh
  venv\Scripts\activate
  ```
- **Mac/Linux:**
  ```sh
  source venv/bin/activate
  ```

#### 2. Install Dependencies
Once the virtual environment is activated, install the required dependencies:

```sh
pip install --no-cache-dir -r requirements.txt
```

#### 3. Configure Environment Variables
Create a `.env` file in the `backend` folder and copy the variables from `.example.env`. Fill in the required values:

```
DB_HOST=<your_mysql_host>
DB_USER=<your_mysql_user>
DB_PASSWORD=<your_mysql_password>
DB_NAME=<your_database_name>
LLM_API_KEY=<your_llm_provider_api_key>
LLM_BASE_URL=<your_llm_provider_base_url>
```

Ensure that your LLM provider supports OpenAI-compatible APIs.

#### 4. Start the Backend Server
Run the following command to start the backend server using Uvicorn:

```sh
uvicorn main:app --host=0.0.0.0 --port=8000
```

### Frontend Setup

#### 1. Install Dependencies
Navigate to the `frontend` folder and install dependencies:

```sh
cd frontend
npm install
```

#### 2. Start the Frontend Server
Run the following command to start the Next.js development server:

```sh
npm run dev
```

The application will be available at `http://localhost:4000`.



[Gradio.js]: https://img.shields.io/badge/Gradio-FF9900?style=for-the-badge&logo=gradio&logoColor=white
[Gradio-url]: https://gradio.app/
[OpenRouter.js]: https://img.shields.io/badge/OpenRouter-FF9900?style=for-the-badge&logo=openrouter&logoColor=white
[OpenRouter-url]: https://openrouter.ai/
[LangChain.js]: https://img.shields.io/badge/LangChain-FF9900?style=for-the-badge&logo=python&logoColor=white
[LangChain-url]: https://www.langchain.com/
[LangGraph.js]: https://img.shields.io/badge/LangGraph-FF5733?style=for-the-badge&logo=graph&logoColor=white
[LangGraph-url]: https://github.com/langchain-ai/langgraph
[ChromaDB.js]: https://img.shields.io/badge/ChromaDB-FF6F00?style=for-the-badge&logo=database&logoColor=white
[ChromaDB-url]: https://github.com/chroma-core/chroma
[OpenAI-badge]: https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white  
[OpenAI-url]: https://openai.com  
[FastEmbed-badge]: https://img.shields.io/badge/FastEmbed-FF6F00?style=for-the-badge&logo=fastapi&logoColor=white  
[FastEmbed-url]: https://github.com/zetavm/fastembed 
