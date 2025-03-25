from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict, Annotated
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from retriever_with_reranker import RetrieveWithReranker
import operator
from prompts import (
    answer_generator_prompt,
    document_grader_prompt,
    question_regenerator_prompt,
    knowledge_evaluator_prompt,
    reasoning_prompt,
)


class State(TypedDict):
    question: str
    keywords: list
    knowledge: Annotated[list, operator.add]
    current_thought: str
    document: str
    final_answer: str
    max_retries: int
    max_generations: int


class ReasoningQuestionHandler:

    def __init__(self, llm: ChatOpenAI, retriever: RetrieveWithReranker):
        """
        Initialize a ReasoningQuestionHandler.

        Args:
            llm (ChatOpenAI): A configured langchain OpenAI chat model.
            retriever (RetrieveWithReranker): A configured langchain retriever with reranker.
        """
        self.llm = llm
        self.retriever = retriever

    def _generate_sub_question(self, state: State):
        reformatted_knowledge = ""
        if state["knowledge"]:
            for k in state["knowledge"]:
                reformatted_knowledge += (
                    f"- Thought: {k['thought']}\n- Observation: {k['observation']}\n"
                )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    reasoning_prompt,
                ),
                (
                    "human",
                    """ Main Question:  
                {question}  

                Previous Thoughts and Observations:  
                {previous}
                """,
                ),
            ]
        )
        chain = prompt | self.llm
        sub_question = chain.invoke(
            {"question": state["question"], "previous": reformatted_knowledge}
        )
        return {"current_thought": sub_question.content}

    def _retrieve(self, state: State):
        query = state["current_thought"]
        keywords = state["keywords"]
        result = self.retriever.search(query, keywords)
        document = ""
        for i, r in enumerate(result):
            document += f"Document {i+1}: {r.page_content}\n\n"
        return {"document": document}

    def _grade_document(self, state: State):
        query = state["current_thought"]
        examples = f"""
        # Case 1: 
        Question: What is the definition of database?
        Document: databases  and  database  systems  are  an  essential  component  of  life  in  modern  society:  most  of  us  encounter several activities every day that involve some interaction with a database. For example, if we go to the bank to deposit or withdraw funds, if we make a hotel or  airline  reservation,  if  we  access  a  computerized  library  catalog  to  search  for  a  bibliographic  item,  or  if  we  purchase  something  online—such  as  a  book,  toy,  or  computer—chances are that our activities will involve someone or some computer program accessing a database.
        Response: NO
        Explanation: The document does not directly provide the necessary information to answer the question.
        # Case 2:
        Question: What is the definition of database?
        Document: A database is a collection of related data.1 By data, we mean known facts that can be  recorded  and  that  have  implicit  meaning.  For  example,  consider  the  names, telephone numbers, and addresses of the people you know. Nowadays, this data is typically stored in mobile phones, which have their own simple database software. This  data  can  also  be  recorded  in  an  indexed  address  book  or  stored  on  a  hard  drive, using a personal computer and software such as Microsoft Access or Excel. This collection of related data with an implicit meaning is a database.
        Response: YES
        Explanation: The document directly provides the necessary information to answer the question.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    document_grader_prompt,
                )
            ]
        )
        chain = prompt | self.llm
        result = chain.invoke(
            {"question": query, "document": state["document"], "examples": examples}
        )
        if  "YES" in result.content.upper() or state["max_retries"] <= 0:
            return "Generate answer"
        else:
            return "Regenerate thought"

    def _regenerate_question(self, state: State):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    question_regenerator_prompt,
                )
            ]
        )
        chain = prompt | self.llm
        result = chain.invoke(
            {
                "original_query": state["current_thought"],
                "main_query": state["question"],
            }
        )
        return {
            "current_thought": result.content,
            "max_retries": state["max_retries"] - 1,
        }

    def _generate_answer(self, state: State):
        current_sub_question = state["current_thought"]
        context = state["document"]
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    answer_generator_prompt,
                )
            ]
        )
        chain = prompt | self.llm
        result = chain.invoke({"question": current_sub_question, "context": context})
        if state["max_retries"] <= 0:
            return {
                "knowledge": [
                    {"thought": state["current_thought"], "observation": result.content}
                ],
                "max_retries": 1,
                "max_generations": state["max_generations"] - 1,
            }
        elif state["max_generations"] >= 2:
            return {
                "knowledge": [
                    {"thought": state["current_thought"], "observation": result.content}
                ],
                "max_retries": 1,
            }
        else:
            return {
                "knowledge": [
                    {"thought": state["current_thought"], "observation": result.content}
                ],
                "max_retries": 1,
                "max_generations": state["max_generations"] + 1,
            }

    def _should_continue(self, state: State):
        question = state["question"]
        examples = f"""
        Example question: What is the difference between a database schema and a database state?
        
        Example 1:
        - Retrieved documents: "A database schema is the structure or blueprint of a database that defines how data is organized. It includes definitions of tables, columns, data types, relationships, constraints, and other elements that dictate the database design."
        - Your response: NO
        - Explanation: "This document contains only the definition of a database schema, so the information is not enough to answer the question about the difference between a database schema and a database state."

        Example 2:
        - Retrieved documents: "A database schema is the structure or blueprint of a database that defines how data is organized. It includes definitions of tables, columns, data types, relationships, constraints, and other elements that dictate the database design.\nA database state refers to the actual data contained in the database at a specific moment in time. It represents the current snapshot of all the data stored in the database, which can change as data is added, modified, or deleted."
        - Your response: YES
        - Explanation: "This document contains all the knowledge required to answer the provided question, which are the definitions of database schema and database state."
        """
        knowledge = "\n".join(
            [k["observation"] for k in state.get("knowledge", []) if k["observation"]]
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    knowledge_evaluator_prompt,
                )
            ]
        )
        chain = prompt | self.llm
        result = chain.invoke(
            {"knowledge": knowledge, "question": question, "examples": examples}
        )
        if "YES" in result.content.upper() or state["max_generations"] <= 0:
            return "Enough knowledge"
        else:
            return "Need more knowledge"

    def _generate_final_answer(self, state: State):
        if state["max_generations"] <= 0:
            return {
                "final_answer": "The question could not be answered. Please try a different question."
            }
        knowledge = "\n".join(
            [k["observation"] for k in state.get("knowledge", []) if k["observation"]]
        )
        question = state["question"]
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    answer_generator_prompt,
                )
            ]
        )
        chain = prompt | self.llm
        result = chain.invoke({"question": question, "context": knowledge})
        return {"final_answer": result.content}

    def build_graph(self):
        """
        Builds a state graph for reasoning question handler.

        The graph consists of the following nodes and edges:

        - generate_thought: generates a sub-question based on the input question
        - retrieve: retrieves relevant documents based on the sub-question
        - generate_answer: generates an answer based on the retrieved documents
        - regenerate_thought: regenerates a new sub-question based on the input question
        - generate_final_answer: generates a final answer based on the generated answers
        - START: the starting point of the graph
        - END: the ending point of the graph

        The graph is connected by the following edges:

        - START -> generate_thought
        - generate_thought -> retrieve
        - retrieve -> generate_answer (if the document is graded high enough)
        - retrieve -> regenerate_thought (if the document is graded low enough)
        - generate_answer -> generate_final_answer (if enough knowledge is generated)
        - generate_answer -> generate_thought (if not enough knowledge is generated)
        - regenerate_thought -> retrieve
        - generate_final_answer -> END

        The graph is compiled into a state machine app using the `compile` method of the `StateGraph` class.

        Returns:
            The compiled state machine app.
        """
        workflow = StateGraph(State)
        workflow.add_node("generate_thought", self._generate_sub_question)
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("generate_answer", self._generate_answer)
        workflow.add_node("regenerate_thought", self._regenerate_question)
        workflow.add_node("generate_final_answer", self._generate_final_answer)
        workflow.add_edge(START, "generate_thought")
        workflow.add_edge("generate_thought", "retrieve")
        workflow.add_edge("regenerate_thought", "retrieve")
        workflow.add_conditional_edges(
            "generate_answer",
            self._should_continue,
            {
                "Enough knowledge": "generate_final_answer",
                "Need more knowledge": "generate_thought",
            },
        )
        workflow.add_conditional_edges(
            "retrieve",
            self._grade_document,
            {
                "Generate answer": "generate_answer",
                "Regenerate thought": "regenerate_thought",
            },
        )
        workflow.add_edge("generate_final_answer", END)
        app = workflow.compile()
        return app
