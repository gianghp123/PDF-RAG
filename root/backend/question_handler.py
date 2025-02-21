from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langchain_core.prompts import ChatPromptTemplate
from fastembed.rerank.cross_encoder import TextCrossEncoder
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from retriever_with_reranker import RetrieveWithReranker
from keybert import KeyBERT
from decomposing_question_handler import DecomposingQuestionHandler
from reasoning_question_handler import ReasoningQuestionHandler
from structured_output_classes import (
    SubQuestions,
    GradeSubQuestions,
    GradeDocument
)
from pydantic import BaseModel
from prompts import (
    answer_generator_prompt,
    answer_reformatter_prompt,
    question_regenerator_prompt,
    decomposer_prompt,
    sub_questions_evaluator_prompt,
    knowledge_evaluator_prompt
)


class QuestionHandlerConfig(BaseModel):
    """Configuration for the QuestionHandler.

    Args:
        file_path (str): The path to the PDF file.
        llm_config (dict): Configuration for the ChatOpenAI, e.g., model, base_url, api_key.
        embedding_config (dict): Configuration for the FastEmbed embedding model, e.g., model_name, max_length, batch_size.
        reranker_config (dict): Configuration for the FastEmbed TextCrossEncoder, e.g., model_name.
    """

    file_path: str
    llm_config: dict
    embedding_config: dict
    reranker_config: dict


class State(TypedDict):
    question: str
    keywords: list
    sub_questions: list[str]
    transformed_question: str
    document: str
    final_answer: str
    max_retries: int


class QuestionHandler:
    def __init__(self, config: QuestionHandlerConfig):
        """
        Initializes the QuestionHandler instance with the given configuration.

        Args:
            config (QuestionHandlerConfig): Configuration for the QuestionHandler, e.g., file_path, llm_config, embedding_config, reranker_config.

        Attributes:
            config (QuestionHandlerConfig): The configuration used to initialize the QuestionHandler.
            llm (ChatOpenAI): The configured ChatOpenAI model.
            retriever (RetrieveWithReranker): The configured retriever with reranker.
            decomposing_question_handler (StateGraph): The graph for the decomposing question handler.
            reasoning_question_handler (StateGraph): The graph for the reasoning question handler.
            kw_model (KeyBERT): The KeyBERT model used for extracting keywords.
        """
        self.config = config
        self.llm = self._init_llm()
        self.retriever = self._init_retriever()
        self.decomposing_question_handler = DecomposingQuestionHandler(
            self.llm, self.retriever
        ).build_graph()
        self.reasoning_question_handler = ReasoningQuestionHandler(
            self.llm, self.retriever
        ).build_graph()
        self.kw_model = KeyBERT()

    def _init_llm(self):
        return ChatOpenAI(**self.config.llm_config)

    def _init_retriever(self):
        return RetrieveWithReranker(
            file_path=self.config.file_path,
            reranker=TextCrossEncoder(**self.config.reranker_config),
            embedding=FastEmbedEmbeddings(**self.config.embedding_config),
        )

    def _extract_keywords(self, state: State):
        question = state["question"]
        return {
            "keywords": [
                k[0]
                for k in self.kw_model.extract_keywords(
                    question, keyphrase_ngram_range=(2, 3), diversity=0.7, use_mmr=True
                )
            ]
        }

    def _retrieve(self, state: State):
        query = state.get("transformed_question", state["question"])
        keywords = state["keywords"]
        result = self.retriever.search(query, keywords)
        if len(result) == 0:
            return {"document": ""}
        document = ""
        for i, r in enumerate(result):
            document += f"Document {i+1}: {r.page_content}\n\n"
        return {"document": document}

    def _grade_document(self, state: State):
        question = state["question"]
        knowledge = state["document"] or ''
        if not knowledge:
            return "Generate answer"
        examples = f"""
        Example 1:
        - Question: What is the difference between a database schema and a database state?
        - Retrieved documents: "A database schema is the structure or blueprint of a database that defines how data is organized. It includes definitions of tables, columns, data types, relationships, constraints, and other elements that dictate the database design."
        - Your response: {GradeDocument(result="NO").model_dump_json()}
        - Explanation: "This document contains only the definition of a database schema, so the information is not enough to answer the question about the difference between a database schema and a database state."

        Example 2:
        - Question: What is the difference between a database schema and a database state?
        - Retrieved documents: "A database schema is the structure or blueprint of a database that defines how data is organized. It includes definitions of tables, columns, data types, relationships, constraints, and other elements that dictate the database design.\nA database state refers to the actual data contained in the database at a specific moment in time. It represents the current snapshot of all the data stored in the database, which can change as data is added, modified, or deleted."
        - Your response: {GradeDocument(result="YES").model_dump_json()}
        - Explanation: "This document contains all the knowledge required to answer the provided question, which are the definitions of database schema and database state."
        
        Example 3:
        - Question: Discuss the naming conventions used for ER schema diagrams.
        - Retrieved documents: "Figures 3.9 through 3.13 illustrate examples of the participation of entity types in relationship types by displaying their entity sets and relationship sets. In ER diagrams, the emphasis is on representing the schemas rather than the instances. This is more useful in database design because a database schema changes rarely, whereas the contents of the entity sets may change frequently."
        - Your response: {GradeDocument(result="NO").model_dump_json()}
        - Explanation: The retrieved documents discuss ER diagram structure but do not explicitly mention naming conventions, making them insufficient.
        
        Example 4:
        - Question: What is a transaction? How does it differ from an Update operation?
        - Retrieved documents: "A transaction in a database is a sequence of operations performed as a single logical unit of work. Transactions follow the ACID properties: Atomicity, Consistency, Isolation, and Durability."
        - Your response: {GradeDocument(result="NO").model_dump_json()}
        - Explanation: "The document provides a definition of a transaction but does not mention update operations, which are necessary to fully answer the question. Since the question explicitly asks for a comparison, and one side of the comparison is missing, the retrieved information is insufficient."
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    knowledge_evaluator_prompt,
                )
            ]
        )
        chain = prompt | self.llm.with_structured_output(schema=GradeDocument, method = 'json_mode')
        result = chain.invoke(
            {"knowledge": knowledge, "question": question, "examples": examples}
        )
        if "YES" in  result.result or not state["document"]:
            return "Generate answer"
        elif state["max_retries"] <= 0:
            return "Decompose question"
        else:
            return "Regenerate question"

    def _regenerate_question(self, state: State):
        query = state.get("transformed_question", state["question"])
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
                "original_query": query,
                "main_query": state["question"],
            }
        )
        return {
            "transformed_question": result.content,
            "max_retries": state["max_retries"] - 1,
        }

    def _generate_answer(self, state: State):
        question = state["question"]
        context = state["document"]
        if not context:
            return {
                "final_answer": "The question seems to be not related to the current document or cannot be answered. Please try a different question."
            }
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    answer_generator_prompt,
                )
            ]
        )
        chain = prompt | self.llm
        result = chain.invoke({"question": question, "context": context})
        return {"final_answer": result.content}

    def _generate_sub_questions(self, state: State):
        question = state["question"]
        example = f"""
                Main Question: "What are the difference between database schema and database state?"
                Your response: {SubQuestions(sub_questions=["What is a database schema?", "What is a database state?"]).model_dump_json()}
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("human", decomposer_prompt),
            ]
        )
        chain = prompt | self.llm.with_structured_output(SubQuestions, method='json_mode')
        result = chain.invoke({"question": question, "example": example})
        return {"sub_questions": result.sub_questions}

    def _decomposing_question_handler_node(self, state: State):
        input = {
            "question": state["question"],
            "keywords": state["keywords"],
            "sub_questions": state["sub_questions"],
            "max_retries": 1,
        }
        result = self.decomposing_question_handler.invoke(input)
        return {"final_answer": result["final_answer"]}

    def _reasoning_question_handler_node(self, state: State):
        input = {
            "question": state["question"],
            "keywords": state["keywords"],
            "max_retries": 1,
            "max_generations": 2,
        }
        result = self.reasoning_question_handler.invoke(input)
        return {"final_answer": result["final_answer"]}

    def _reformat_final_answer(self, state: State):
        if not state["document"]:
            return {"final_answer": state["final_answer"]}
        final_answer = state["final_answer"]
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    answer_reformatter_prompt,
                )
            ]
        )
        chain = prompt | self.llm
        result = chain.invoke({"text": final_answer})
        return {"final_answer": result.content}

    def _route_node(self, state: State):
        sub_questions = "\n".join(state["sub_questions"])
        examples = f"""
        ### EXAMPLE 1:
        Main Question: What four main types of actions involve databases? Briefly discuss each.
        Sub-Questions:
            - What is the first main type of action involving databases?
            - What is the second main type of action involving databases?
            - What is the third main type of action involving databases?
            - What is the fourth main type of action involving databases?
        Response: {GradeSubQuestions(result='NO').model_dump_json()}
        Explanation: The sub-questions assume the existence of four database actions without specifying what they are. Since they only ask about 'the first main type,' 'the second main type,' etc., they do not independently provide an answer to the main question. This means the required discussion is missing, making the decomposition incomplete.

        ### EXAMPLE 2:
        Main Question: What is the difference between the two-tier and three-tier client/server architectures?
        Sub-Questions:
            - What is a two-tier client/server architecture?
            - What is a three-tier client/server architecture?
        Response: {GradeSubQuestions(result='YES').model_dump_json()}
        Explanation: Since understanding the difference between two things requires knowing what each one is, answering both sub-questions provides enough information to infer the difference.

        ### EXAMPLE 3:
        Main Question: Describe the two alternatives for specifying structural constraints on relationship types. What are the advantages and disadvantages of each?
        Sub-Questions:
            - What are the two alternatives for specifying structural constraints on relationship types?
            - What are the advantages of each alternative?
            - What are the disadvantages of each alternative?
        Response: {GradeSubQuestions(result='NO').model_dump_json()}
        Explanation: The sub-questions fail to fully address the main question because they do not explicitly ask for a description of each alternative, which is required by the main question. Simply identifying the two alternatives without describing them leaves out essential details. A more complete set of sub-questions should ensure that each alternative is fully explained before discussing their advantages and disadvantages.
        """
        question = state["question"]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    sub_questions_evaluator_prompt,
                )
            ]
        )
        chain = prompt | self.llm.with_structured_output(GradeSubQuestions, method='json_mode')
        score = chain.invoke(
            {
                "main_question": question,
                "examples": examples,
                "sub_questions": sub_questions,
            }
        )
        if "YES" in score.result:
            return "Decomposing approach can solve the question"
        else:
            return "Another approach"

    def build_graph(self):
        """
        Constructs a state graph for the question handler.

        The graph includes the following nodes and edges:

        - extract_keywords: extracts keywords from the question
        - retrieve: retrieves relevant documents based on the sub-question
        - regenerate_question: regenerates a new sub-question if the document is insufficient
        - decompose_question: decomposes a question into multiple sub-questions
        - generate_final_answer: generates a final answer based on accumulated knowledge
        - reformat_final_answer: reformats the final answer
        - START: the starting point of the graph
        - END: the endpoint of the graph

        The graph is connected by the following edges:

        - START -> extract_keywords
        - extract_keywords -> retrieve
        - retrieve -> generate_answer (if the document is graded sufficiently)
        - retrieve -> regenerate_question (if the document is not sufficient)
        - regenerate_question -> retrieve
        - generate_answer -> reformat_final_answer (if all sub-questions are answered)
        - generate_answer -> retrieve (if more sub-questions need answering)
        - generate_final_answer -> reformat_final_answer
        - reformat_final_answer -> END

        The graph is compiled into an application using the `compile` method of the `StateGraph` class.

        Returns:
            The compiled state machine application.
        """
        workflow = StateGraph(state_schema=State)
        workflow.add_node("extract_keywords", self._extract_keywords)
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("regenerate_question", self._regenerate_question)
        workflow.add_node("decompose_question", self._generate_sub_questions)
        workflow.add_node("generate_final_answer", self._generate_answer)
        workflow.add_node(
            "decomposing_question_handler_node", self._decomposing_question_handler_node
        )
        workflow.add_node(
            "reasoning_question_handler_node", self._reasoning_question_handler_node
        )
        workflow.add_node("reformat_final_answer", self._reformat_final_answer)
        workflow.add_edge(START, "extract_keywords")
        workflow.add_edge("extract_keywords", "retrieve")
        workflow.add_conditional_edges(
            "retrieve",
            self._grade_document,
            {
                "Generate answer": "generate_final_answer",
                "Decompose question": "decompose_question",
                "Regenerate question": "regenerate_question",
            },
        )
        workflow.add_conditional_edges(
            "decompose_question",
            self._route_node,
            {
                "Decomposing approach can solve the question": "decomposing_question_handler_node",
                "Another approach": "reasoning_question_handler_node",
            },
        )
        workflow.add_edge("regenerate_question", "retrieve")
        workflow.add_edge("decomposing_question_handler_node", "reformat_final_answer")
        workflow.add_edge("generate_final_answer", "reformat_final_answer")
        workflow.add_edge("reasoning_question_handler_node", "reformat_final_answer")
        workflow.add_edge("reformat_final_answer", END)
        app = workflow.compile()
        return app
