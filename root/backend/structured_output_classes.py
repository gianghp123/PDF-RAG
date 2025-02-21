from pydantic import Field, BaseModel

class GradeDocument(BaseModel):
    """Grade the provided documents based if they contain enough information to directly answer the given question."""

    result: str = Field(
        description="the result of the evaluation 'YES' or 'NO' only."
    )

class SubQuestions(BaseModel):
    """a list of sub-questions to systematically gather knowledge needed to answer a given main question."""

    sub_questions: list[str] = Field(
        description="the list of sub-questions"
    )
    
class GradeSubQuestions(BaseModel):
    """Grade whether the provided sub-questions fully answer the main question. 
    The output should be 'YES' if answering all sub-questions provides a complete answer, otherwise 'NO'."""

    result: str = Field(
        description="The result of the evaluation: 'YES' if the sub-questions fully answer the main question, otherwise 'NO'."
    )
