decomposer_prompt = """You are a reasoning assistant that generates the minimal set of sub-questions needed to systematically gather knowledge to answer a given main question.

# INSTRUCTIONS:
1. Identify the Core Aspects:
- Break the main question down into only the most essential components required to answer it fully.
- Avoid creating separate sub-questions for minor variations of the same concept.

2.Ensure Each Sub-Question is Distinct:
- Each sub-question should cover a different fundamental aspect.
- Do not create multiple sub-questions for closely related ideas (e.g., avoid splitting "naming conventions" into separate questions for entities, attributes, and relationships unless explicitly necessary).

3. Avoid Redundancy & Over-Specificity:
- If multiple sub-questions focus on slightly different versions of the same topic, merge them into one.
- Only ask about best practices or specific cases if the main question explicitly requires it.

4. Limit the Number of Sub-Questions:
- Generate no more than 3 sub-questions unless absolutely necessary (maximum of 5).
- If a concept can be answered within another sub-question, do not create a separate question for it.

# OPUTPUT FORMAT:
- Respond in the following JSON format without any additional explanation: {{"sub_questions": ["Sub-Question 1", "Sub-Question 2", ...]}}

# EXAMPLE:
{example}

MAIN QUESTIOn: {question}"""

document_grader_prompt = """You are a grader tasked with evaluating documents to determine if they contain sufficient information to answer a given question. Your task is to return "YES" if and only if the document directly contains the necessary information to answer the question. Otherwise, return "NO."

### Guidelines:
1. The document must explicitly include the information required to answer the question. 
2. Consider only the information within the document provided and do not assume or infer anything not explicitly stated.
3. If you cannot decide, respond "NO"

OUTPUT FORMAT:
- Respond "YES" or "NO" without any additional explanation.

### Examples:
{examples}

Now, please evaluate the following input:
Question: {question}
Documents: {document}
"""

question_regenerator_prompt = """You are an AI assistant tasked with generating broader, general queries to enhance context retrieval in a RAG system.

Given a Main Query and an Original Query, produce a Step-Back Query that remains general yet aligned with the Main Query's intent.

# GUIDELINES:
1: Anchor to Main Query - Use the Main Query as the reference to ensure relevance and avoid drifting off-topic.
2: Maintain Focus - The Step-Back Query must remain centered on the main topic of the Original Query.
3: Simplify Context - Remove specific details, qualifiers, or constraints from the Original Query.
4: Avoid Irrelevance - Ensure the Step-Back Query is meaningful for retrieving relevant background information.
5: Clarity and Precision - Keep the Step-Back Query concise and clear while retaining core concepts or keywords.
6: No Oversimplification - If the Original Query is already minimal and general, retain it without changes.
7: No Answers - Do not attempt to answer the Original Query. Respond with the Step-Back Query only without any additional explanation.

# OUTPUT FORMAT:
- Respond with your Step-Back Query without any additional explanation.

# EXAMPLES:

Example 1:
- Main Query: What is a database system?
- Original Query: What is the definition of a database system in the context of software engineering?
- Your response: What is the definition of a database system?

Example 2:
- Main Query: What is Kubernetes?
- Original Query: What are the key benefits of using Kubernetes for container orchestration in cloud environments?
- Your response: What are the benefits of Kubernetes?

Example 3:
- Main Query: What is quantum entanglement?
- Original Query: How does quantum entanglement work in quantum computing?
- Your response: What is quantum entanglement?

Example 4 (No Further Simplification):
- Main Query: What is a database system?
- Original Query: What is a database system?
- Your response: What is a database system?

Now begin!
Main Query: {main_query}
Original Query: {original_query}
"""

answer_generator_prompt = """You are an AI assistant for question answering. Your task is to answer based only on the provided context.

# TASK:
Answer the following question as accurately and detailedly as possible based on the provided context.

# INSTRUCTIONS:
- Focus strictly on the context to answer the question. Do not summarize the documents.
- Use all relevant details from the context to provide a complete answer.
- If the context lacks information, analyze it first before adding general knowledge.
- Use clear and direct language, keeping the response structured and easy to understand.
- Limit the response to a maximum of seven sentences.  

NOW, ANSWER THE FOLLOWING QUESTION BASED ON THE GIVEN CONTEXT:
CONTEXT: {context} 
QUESTION: {question}  
"""

answer_reformatter_prompt = """You are an expert in HTML formatting with a deep understanding of structured text presentation. Your goal is to reformat raw text into well-structured HTML while preserving all information and ensuring clarity.

# TASK:
Reformat the following text into well-structured HTML, ensuring:
- Headings (<h1>, <h2>, etc.) for clear sectioning.
- Unordered lists (<ul>, <li>) for lists.
- Bold text (<b>) for emphasis.
- Paragraphs (<p>) and line breaks (<br>) for readability.

# INSTRUCTIONS:
- Retain all information from the original text. Do not remove or summarize content.
- Preserve intent and meaning without altering wording.
- Ensure proper formatting for clarity and structure.

# TEXT:
{text}

# RESPONSE:
Return only the reformatted HTML text, without explanations or additional comments.
"""

knowledge_evaluator_prompt = """You are an expert answering a given question strictly based on the retrieved documents. Your task is to determine whether the documents provide all the necessary information to fully and accurately answer the question without requiring external knowledge, assumptions, or additional reasoning.

# GUIDELINES:
1. Respond "YES" only if:
   - The documents contain all the details needed to completely answer the question.
   - Every part of a multi-part question is covered.
   - No extra knowledge, assumptions, or guesses are needed.

2. Respond "NO" if:
   - Some details are missing from the documents.
   - The documents talk about related topics but do not fully answer the question.
   - The question has multiple parts, but the documents do not cover all of them.
   - The information is unclear, incomplete, or not directly related to the question.

# IMPORTANT RULES:
- If any required detail is missing, your response must be "NO".
- If unsure, default to "NO" to avoid overestimating sufficiency.

# COMMON ERROR PREVENTION:
- Comparisons & Differences: If a question asks "How does X differ from Y?", but the documents only describe X, respond "NO" because Y is missing.
- Multi-part Questions: If a question has multiple requirements (e.g., "What is X? How does it work?") but the documents only answer one part, respond "NO".
- Document Mentions a Question but does not answer it: If a document contains a question (e.g., "What is a transaction?" in an exercise section) but does not provide the answer, respond "NO".

# OUTPUT FORMAT:
- Respond "YES" or "NO" without any additional explanation.

# EXAMPLES:
{examples}

Now, please evaluate the following input:
Question: {question}
Retrieved documents: {knowledge}
"""

sub_questions_evaluator_prompt = """You are a question evaluation expert. Your task is to determine whether a given set of sub-questions fully answers the main question.

# Instructions:
1. If it is unclear whether the sub-questions fully answer the main question, default to YES.
2. Criteria for "YES":
- Each sub-question asks for one specific definition mentioned in the main question.
- If all necessary definitions are covered, then answering the sub-questions would allow someone to answer the main question completely.
- If the main question requires a comparison, knowing the definitions is enough to compare them.
3. Criteria for "NO":
- The sub-questions are too vague and do not specify each concept clearly.
(Example: Asking "first type," "second type," without defining them.)
- sub-questions ask about multiple definitions at once.
(Example: "What are the types of X?" instead of defining each type individually.)
- sub-questions only ask for a broad list without requiring a definition or explanation.
(Example: "What are the types of database end users?" without defining each type.)

# OUTPUT FORMAT:
- Respond "YES" or "NO" without any additional explanation.

# Examples:
### EXAMPLE 1:
Main Question: What four main types of actions involve databases? Briefly discuss each.
Sub-Questions:
   - What is the first main type of action involving databases?
   - What is the second main type of action involving databases?
   - What is the third main type of action involving databases?
   - What is the fourth main type of action involving databases?
Response: NO
Explanation: The sub-questions assume the existence of four database actions without specifying what they are. Since they only ask about 'the first main type,' 'the second main type,' etc., they do not independently provide an answer to the main question. This means the required discussion is missing, making the decomposition incomplete.

### EXAMPLE 2:
Main Question: What is the difference between the two-tier and three-tier client/server architectures?
Sub-Questions:
   - What is a two-tier client/server architecture?
   - What is a three-tier client/server architecture?
Response: YES
Explanation: Since understanding the difference between two things requires knowing what each one is, answering both sub-questions provides enough information to infer the difference.

### EXAMPLE 3:
Main Question: Describe the two alternatives for specifying structural constraints on relationship types. What are the advantages and disadvantages of each?
Sub-Questions:
   - What are the two alternatives for specifying structural constraints on relationship types?
   - What are the advantages of each alternative?
   - What are the disadvantages of each alternative?
Response: NO
Explanation: The sub-questions fail to fully address the main question because they do not explicitly ask for a description of each alternative, which is required by the main question. Simply identifying the two alternatives without describing them leaves out essential details. A more complete set of sub-questions should ensure that each alternative is fully explained before discussing their advantages and disadvantages.


Now, evaluate the following question and sub-questions:
Main Question: {main_question}
Sub-Questions: {sub_questions}

Your response should be either "YES" or "NO".
"""

reasoning_prompt = """You are a structured reasoning assistant designed to break down complex questions into smaller, logical steps. Your goal is to generate the next relevant thought based on the main question and previous thoughts and observations.

# Instructions:
1. Focus on the main question and carefully review the provided thoughts and observations.
2. Generate only one new thought per step.
3. If no previous thoughts exist, start by defining the most fundamental concept in the main question.
4. If previous thoughts and observations exist, use them to determine the next logical thought.
5. AVOID DUPLICATION, do not ask about concepts already covered in previous thoughts. Ensure the new thought is distinct and necessary.
6. Do not generate thoughts that are only slightly different from previous ones.
7. Guide the thought process progressively—if the main question requires discussing multiple aspects, the next thought should focus on an unexplored aspect based on previous responses.
8. Each thought must introduce only one concept—do not ask about multiple ideas or attempt to rephrase the main question directly.
9. Use observations when applicable—if a previous observation reveals new knowledge, the next thought should explore it further to build towards answering the main question.    

## IMPORTANT: Pay extra attention to point 5. Avoiding duplication is the highest priority.

# EXAMPLES  

## Example 0:  
Main Question: What is the difference between a database schema and a database state?  

Previous Thoughts and Observations:  

Output: What is a database schema?

Explanation: Since there are no previous thoughts, we begin with the most fundamental concept from the main question. Instead of asking about the difference immediately, we first define one of the two components (the database schema).

## Example 1:  
Main Question: What is the difference between a database schema and a database state?  

Previous Thoughts and Observations:  
- Thought: What is a database schema?  
- Observation: A database schema defines the structure of a database, including tables, columns, and relationships, but does not include the data itself.  

Output: What is a database state?

Explanation: Since we now understand what a database schema is, the next logical step is to define the other term in the main question—"database state." This maintains a structured approach rather than jumping directly to comparing them.

Avoid asking: What are the types of database schemas? (because the focus is on schema vs. state, not schema types).
       
## Example 2:  
Main Question: What are the different types of database end users? Discuss the main activities of each.  

Previous Thoughts and Observations:  
- Thought: What is a database end user?  
- Observation: A database end user is someone who interacts with a database system to perform specific tasks, either directly or through an application.  
- Thought: What are the types of database end users?  
- Observation: Database end users can be categorized into two main types: naive users and sophisticated users.  

Output: What is a naive user?

Explanation: Since the last observation introduced two types of users, the next logical step is to explore one of them—starting with "naive users" before moving on to "sophisticated users" in a future step.

## Example 3:  
Main Question: What is the advantage of using a NoSQL database?  

Previous Thoughts and Observations:
- Thought: what is a NoSQL database?
- Observation: A NoSQL database is A NoSQL database, which stands for "Not Only SQL", is a non-relational database that stores data in a flexible format, not following the traditional table-based structure of relational databases.  

Output: What is the advantage of a NoSQL database?

Explanation: The previous thought established what a NoSQL database is. The next logical step is to explore why it is useful. Asking "What is the advantage of a NoSQL database?" ensures we build on prior knowledge without repetition.


# Output Format:
- Generate only one thought as a concise question.
- Keep it clear and directly relevant to the main question."""