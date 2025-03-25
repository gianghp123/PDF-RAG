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
)


def update_list(lst, index, new_value):
    if 0 <= index < len(lst):
        lst[index] = new_value
    return lst


class State(TypedDict):
    question: str
    keywords: list
    knowledge: Annotated[list, operator.add]
    sub_questions: list[str]
    document: str
    current_thought_index: int
    final_answer: str
    max_retries: int


class DecomposingQuestionHandler:
    def __init__(self, llm: ChatOpenAI, retriever: RetrieveWithReranker):
        """
        Initialize a DecomposingQuestionHandler.

        Args:
            llm (ChatOpenAI): A configured langchain OpenAI chat model.
            retriever (RetrieveWithReranker): A configured langchain retriever with reranker.
        """

        self.llm = llm
        self.retriever = retriever

    def _retrieve(self, state: State):
        current_thought_index = state.get("current_thought_index", 0)
        query = state["sub_questions"][current_thought_index]
        keywords = state["keywords"]
        result = self.retriever.search(query, keywords)
        document = ""
        for i, r in enumerate(result):
            document += f"Document {i+1}: {r.page_content}\n\n"
        return {"document": document}

    def _grade_document(self, state: State):
        current_thought_index = state.get("current_thought_index", 0)
        query = state["sub_questions"][current_thought_index]
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
            return "Regenerate question"

    def _regenerate_question(self, state: State):
        current_thought_index = state.get("current_thought_index", 0)
        current_thought = state["sub_questions"][current_thought_index]
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
                "original_query": current_thought,
                "main_query": state["question"],
            }
        )
        return {
            "sub_questions": update_list(
                state["sub_questions"], current_thought_index, result.content
            ),
            "max_retries": state["max_retries"] - 1,
        }

    def _generate_answer(self, state: State):
        current_thought_index = state.get("current_thought_index", 0)
        current_thought = state["sub_questions"][current_thought_index]
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
        result = chain.invoke({"question": current_thought, "context": context})
        return {
            "knowledge": [{"thought": current_thought, "observation": result.content}],
            "current_thought_index": state.get("current_thought_index", 0) + 1,
            "max_retries": 1,
        }

    def _should_continue(self, state: State):
        if state["current_thought_index"] >= len(state["sub_questions"]):
            return "Enough knowledge"
        else:
            return "Need more knowledge"

    def _generate_final_answer(self, state: State):
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
        Constructs a state graph for the decomposing question handler.

        The graph includes the following nodes and edges:

        - retrieve: retrieves relevant documents based on the sub-question
        - generate_answer: generates an answer based on the retrieved documents
        - regenerate_question: regenerates a new sub-question if the document is insufficient
        - generate_final_answer: generates a final answer based on accumulated knowledge
        - START: the starting point of the graph
        - END: the endpoint of the graph

        The graph is connected by the following edges:

        - START -> retrieve
        - retrieve -> generate_answer (if the document is graded sufficiently)
        - retrieve -> regenerate_question (if the document is not sufficient)
        - regenerate_question -> retrieve
        - generate_answer -> generate_final_answer (if all sub-questions are answered)
        - generate_answer -> retrieve (if more sub-questions need answering)
        - generate_final_answer -> END

        The graph is compiled into an application using the `compile` method of the `StateGraph` class.

        Returns:
            The compiled state machine application.
        """

        workflow = StateGraph(state_schema=State)
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("generate_answer", self._generate_answer)
        workflow.add_node("regenerate_question", self._regenerate_question)
        workflow.add_node("generate_final_answer", self._generate_final_answer)
        workflow.add_edge(START, "retrieve")
        workflow.add_conditional_edges(
            "retrieve",
            self._grade_document,
            {
                "Generate answer": "generate_answer",
                "Regenerate question": "regenerate_question",
            },
        )
        workflow.add_edge("regenerate_question", "retrieve")
        workflow.add_conditional_edges(
            "generate_answer",
            self._should_continue,
            {
                "Enough knowledge": "generate_final_answer",
                "Need more knowledge": "retrieve",
            },
        )
        workflow.add_edge("generate_final_answer", END)
        app = workflow.compile()
        return app
