# 🚀 **Introduction**  
This is a personal **Question-Answering (QA) project for PDF documents**, allowing users to **upload local PDF files** or **download PDF files via a link**. The system processes the document's content and provides answers based on user queries.  

### Built With

* [![Next][Next.js]][Next-url]
* [![React][React.js]][React-url]
* [![FastAPI][FastAPI.js]][FastAPI-url]
* [![TailwindCSS][TailwindCSS.js]][TailwindCSS-url]
* [![LangChain][LangChain.js]][LangChain-url]
* [![LangGraph][LangGraph.js]][LangGraph-url]
* [![Motion.js][Motion.js]][Motion-url]
* [![MySQL][MySQL.js]][MySQL-url]
* [![ChromaDB][ChromaDB.js]][ChromaDB-url]
# **Question Processing Workflow**
<p align="center"><img alt="Question Handler Graph" src="https://github.com/gianghp123/PDF-RAG/blob/main/backend/graph_pngs/question_handler_graph.png" height="600"></p>
This workflow is designed to process user queries by combining multiple information retrieval and reasoning techniques. Below is a detailed breakdown of each step:

---

## **1. Preprocessing & Information Retrieval**

### **a. Keyword Extraction**
- Uses **KeyBERT** to extract keywords from the query for keyword-based retrieval (BM25).

### **b. Hybrid Retrieval**
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

## **2. Evaluation & Query Refinement**

### **a. Completeness Check**
- If the retrieved information is **sufficient** to answer the query → Generate the answer and exit.
- If **insufficient** → Proceed to **query rewriting** (step-back prompting).

### **b. Query Rewriting**
- **Goal**: Reformulate the query into a clearer and more general version while maintaining its core focus.
- **Limit**: Rewrite **only once**. If the rewritten query still lacks sufficient information → Move to the next step.

---

## **3. Routing & Question Decomposition**

### **a. Generating Sub-Questions**
- Decompose the original query into smaller, independent sub-questions.

### **b. Routing Sub-Questions**
- If answering the sub-questions **fully addresses** the original query → move to **Decomposing question handler**.
- If the sub-questions are **dependent on the original query** (e.g., *"Discuss each..."* requiring context from the main query) → Switch to **Reasoning question handler**.

---

## **4. Decomposing Question Handler**

- **Process sub-questions from step 3**.
- For each sub-question, loop through **retrieve → grade → answer | rewrite** as follows:
  1. **Retrieve**: Fetch relevant information using BM25, ChromaDB, and Reranker.
  2. **Grade**: Assess the relevance of the retrieved documents.
  3. **Answer**: If sufficient information is found, generate an answer.
  4. **Rewrite**: If information is insufficient, rewrite the sub-question (**max 1 time**).
  5. If rewriting still doesn't yield enough information, **combine document knowledge with LLM-generated insights** to answer.
  6. Repeat for the remaining sub-questions.
  7. Aggregate sub-answers to form the final response.

---

## **5. Reasoning Question Handler**

### **a. Thought Generation**
- The LLM generates **thoughts** (ideas/concepts) focusing on specific aspects of the query.
- **Key rules**:
  - Each thought should address **one distinct issue**.
  - Avoid redundancy by referencing previous **thought-observation** pairs.

### **b. Observation Generation**
- **Observations** are responses to thoughts, based on retrieved document information.
- **Process**:
  1. Retrieve relevant documents for the given thought.
  2. Check completeness → If insufficient, rewrite the thought (**max 1 time**).
  3. **Combine retrieved documents with LLM knowledge** to generate an observation.

### **c. Knowledge Validation Loop**
- After each thought-observation pair, the system checks:
  - If **sufficient** information is gathered → Stop and compile the final answer.
  - If **insufficient** → Generate a new thought based on the current context.

---

## **6. Final Compilation & Formatting**
- Format the final response as **Markdown** (including headings, bullet points, and code blocks if needed) before delivering it to the frontend.

---

## **Special Conditions**
- **Skip decomposition** if sub-questions are dependent on the main query.
- **Prioritize** diverse retrieval (MMR) and accuracy (reranking).
- **Terminate workflow** immediately if reranking returns empty results (i.e., top 2 relevant documents have *score < 0*).

  
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[FastAPI.js]: https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white
[FastAPI-url]: https://fastapi.tiangolo.com/
[TailwindCSS.js]: https://img.shields.io/badge/TailwindCSS-38B2AC?style=for-the-badge&logo=tailwindcss&logoColor=white
[TailwindCSS-url]: https://tailwindcss.com/
[LangChain.js]: https://img.shields.io/badge/LangChain-FF9900?style=for-the-badge&logo=python&logoColor=white
[LangChain-url]: https://www.langchain.com/
[LangGraph.js]: https://img.shields.io/badge/LangGraph-FF5733?style=for-the-badge&logo=graph&logoColor=white
[LangGraph-url]: https://github.com/langchain-ai/langgraph
[Motion.js]: https://img.shields.io/badge/Motion.js-FF3366?style=for-the-badge&logo=framer&logoColor=white
[Motion-url]: https://motion.dev/
[MySQL.js]: https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white
[MySQL-url]: https://www.mysql.com/
[ChromaDB.js]: https://img.shields.io/badge/ChromaDB-FF6F00?style=for-the-badge&logo=database&logoColor=white
[ChromaDB-url]: https://github.com/chroma-core/chroma
