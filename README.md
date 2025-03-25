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
This is a personal **Question-Answering (QA) project for PDF documents**, allowing users to **upload local PDF files** or **download PDF files via a link**. The system processes the document's content and provides answers based on user queries.  


### Built With
* [![Gradio][Gradio.js]][Gradio-url]
* [![OpenRouter][OpenRouter.js]][OpenRouter-url]
* [![LangChain][LangChain.js]][LangChain-url]
* [![LangGraph][LangGraph.js]][LangGraph-url]
* [![OpenAI][OpenAI-badge]][OpenAI-url]  
* [![FastEmbed][FastEmbed-badge]][FastEmbed-url]
* [![ChromaDB][ChromaDB.js]][ChromaDB-url]

## Project Features

### File Management  
- Upload, download, and delete files  
- Each file can be associated with multiple sessions  
- Session-based file organization for better tracking   

### Question-Answer System  
- Ask questions about a specific file  
- Each session maintains a separate QA history for the file  
- Retrieve past Q&A interactions for reference

### Session Management  
- Multiple sessions per file, each with independent discussions  
- Track and manage QA history within each session  
- Restore previous sessions to continue discussions seamlessly  

## **Question Processing Workflow**
<p align="center"><img alt="Question Handler Graph" src="https://github.com/gianghp123/PDF-RAG/blob/main/backend/graph_pngs/question_handler_graph.png" height="600"></p>
This workflow is designed to process user queries by combining multiple information retrieval and prompt engineering techniques. Below is a detailed breakdown of each step:

---

### **1. Preprocessing & Information Retrieval**

#### **a. Keyword Extraction**
- Uses **KeyBERT** to extract keywords from the query for keyword-based retrieval (BM25).

#### **b. Hybrid Retrieval**
- Extracted keywords are reranked to determine the most relevant ones for the query.
- Combines three retrieval methods:
  - **BM25**: Returns the top 2 most relevant documents based on keyword matching.
  - **ChromaDB with MMR (Maximal Marginal Relevance)**:
    - Retrieves **10 most relevant documents** using the MMR algorithm.
    - Selects **the most relevant document** from this set that has not yet been reranked.
  - **Reranking**:
    - Applies reranking to the **10 retrieved documents** from ChromaDB.
    - Selects the **top 2 highest-scoring documents** after reranking.
- **Stopping condition**: If the reranking step returns empty results (score < 0), the system outputs *"The question is not related to the current documents"* and ends the workflow.

---

### **2. Evaluation & Query Refinement**

#### **a. Completeness Check**
- If the retrieved information is **sufficient** to answer the query → Generate the answer and exit.
- If **insufficient** → Proceed to **query rewriting** (step-back prompting).

#### **b. Query Rewriting**
- **Goal**: Reformulate the query into a clearer and more general version while maintaining its core focus.
- **Limit**: Rewrite **only once**. If the rewritten query still lacks sufficient information → Move to the next step.

---

### **3. Routing & Question Decomposition**

#### **a. Generating Sub-Questions**
- Decompose the original query into smaller, independent sub-questions.

#### **b. Routing Sub-Questions**
- If answering the sub-questions **fully addresses** the original query → move to **Decomposing question handler**.
- If the sub-questions are **dependent on the original query** (e.g., *"Discuss each..."* requiring context from the main query) → Switch to **Reasoning question handler**.

---

### **4. Decomposing Question Handler**
<p align="center"><img alt="Question Handler Graph" src="https://github.com/gianghp123/PDF-RAG/blob/main/backend/graph_pngs/decomposing_question_handler_graph.png" height="400"></p>

- **Process sub-questions from step 3**.
- For each sub-question, loop through **retrieve → grade → answer | rewrite** as follows:\
  1\. **Retrieve**: Fetch relevant information using BM25, ChromaDB, and Reranker.\
  2\. **Grade**: Evaluate the relevance of the retrieved documents.\
  3\. **Answer**: If sufficient information is found, generate an answer.\
  4\. **Rewrite**: If information is insufficient, rewrite the sub-question (**max 1 time**).\
  5\. If rewriting still doesn't yield enough information, **combine document knowledge with LLM-generated insights** to answer.\
  6\. Repeat for the remaining sub-questions.\
  7\. Aggregate sub-answers to form the final response.

---

### **5. Reasoning Question Handler**
<p align="center"><img alt="Question Handler Graph" src="https://github.com/gianghp123/PDF-RAG/blob/main/backend/graph_pngs/reasoning_question_handler_graph.png" height="500"></p>

#### **a. Thought Generation**
- The LLM generates **thoughts** (ideas/concepts) focusing on specific aspects of the query.
- **Key rules**:
  - Only one thought per generation.
  - Each thought should address **one distinct issue**.
  - Avoid redundancy by referencing previous **thought-observation** pairs.

#### **b. Observation Generation**
- **Observations** are responses to thoughts, based on retrieved document information.
- **Process**:\
  1\. Retrieve relevant documents for the given thought.  
  2\. Check completeness → If insufficient, rewrite the thought (*max 1 time*).  
  3\. Combine retrieved documents with LLM knowledge to generate an observation.

#### **c. Knowledge Validation Loop**
- After each thought-observation pair, the system checks:
  - If **sufficient** information is gathered → Stop and compile the final answer.
  - If **insufficient** → Generate a new thought based on the current context.

---

### **6. Final Compilation & Formatting**
- Format the final response as **Markdown** (including headings, bullet points, and code blocks if needed) before delivering it to the frontend.

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



[Gradio]: https://img.shields.io/badge/Gradio-FF9900?style=for-the-badge&logo=gradio&logoColor=white
[Gradio-url]: https://gradio.app/
[OpenRouter]: https://img.shields.io/badge/OpenRouter-FF9900?style=for-the-badge&logo=openrouter&logoColor=white
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
