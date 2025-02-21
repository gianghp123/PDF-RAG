import dotenv
import mysql.connector
import os
import uuid
from retriever_with_reranker import delete_collection
from mysql.connector.pooling import PooledMySQLConnection
from mysql.connector.abstracts import MySQLConnectionAbstract
from typing import Union

dotenv.load_dotenv()


UPLOAD_DIR = "uploads"


def create_connection(
    database_name: str = None,
) -> Union[PooledMySQLConnection, MySQLConnectionAbstract, None]:
    """
    Create a connection to the MySQL database.

    Args:
        database_name (str): The name of the database to connect to. If not provided, the function will connect to the default database.

    Returns:
        Union[PooledMySQLConnection, MySQLConnectionAbstract, None]: A connection to the MySQL database if the connection is successful, otherwise None.

    Raises:
        Exception: If there is an error while connecting to the database.
    """
    try:
        if database_name:
            conn = mysql.connector.connect(
                host=os.environ.get("DB_HOST"),
                user=os.environ.get("DB_USER"),
                password=os.environ.get("DB_PASSWORD"),
                database=database_name,
            )
            if conn.is_connected():
                print("Connected to MySQL database")
            return conn
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
        )
        if conn.is_connected():
            print("Connected to MySQL database")
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
    return None


def create_database() -> None:
    """
    Create the database if it does not exist.

    This function creates a connection to the MySQL database and then executes a query to create the database if it does not exist.

    Raises:
        Exception: If there is an error while creating the database.
    """
    try:
        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.environ.get('DB_NAME')}")
            print("Database created successfully")
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Error creating the database: {e}")


def create_tables() -> None:
    """
    Create the tables in the database if they do not exist.

    This function creates a connection to the MySQL database and then executes a query to create the tables if they do not exist.

    Raises:
        Exception: If there is an error while creating the tables.
    """
    try:
        conn = create_connection(database_name=os.environ.get("DB_NAME"))
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
            CREATE TABLE IF NOT EXISTS files (
                file_id INT AUTO_INCREMENT PRIMARY KEY,
                source VARCHAR(255) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR(36) PRIMARY KEY, 
                file_id INT NOT NULL, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(36) NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
            """
            )
            print("Tables created successfully")
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Error creating the tables: {e}")


def insert_file(file_source) -> None:
    """
    Insert a file source to the database.

    Args:
        file_source (str): The path to the file source.
    """
    conn = create_connection(database_name=os.environ.get("DB_NAME"))
    cursor = conn.cursor()
    query = """
        INSERT IGNORE INTO files (source)
        VALUES (%s);
    """
    cursor.execute(query, (file_source,))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"{file_source} inserted successfully.")


def delete_file_by_id(file_id: int) -> None:
    """
    Delete a file and all related sessions from the database, including the ChromaDB collection.

    Args:
        file_id (int): The ID of the file to be deleted.

    Raises:
        mysql.connector.Error: If there is an error while deleting the file or related sessions.
    """

    conn = create_connection(database_name=os.environ.get("DB_NAME"))
    cursor = conn.cursor()
    try:
        file_source = get_file_by_id(file_id)
        if not file_source:
            print(f"File with ID {file_id} not found.")
        else:
            file_path = os.path.join(UPLOAD_DIR, file_source[0])
            delete_collection(file_path)

        # Xóa file
        delete_file_query = """
            DELETE FROM files WHERE file_id = %s;
        """
        cursor.execute(delete_file_query, (file_id,))
        conn.commit()
        print(
            f"File with ID {file_id} and all related sessions have been deleted successfully."
        )

    except mysql.connector.Error as err:
        # Nếu có lỗi, rollback transaction
        conn.rollback()
        print(f"Error: {err}")

    finally:
        cursor.close()
        conn.close()


def create_session(file_id) -> None:
    """
    Create a new session for a given file_id.

    Args:
        file_id (int): The ID of the file for the session.

    Returns:
        str: The session ID for the new session.

    """
    session_id = str(uuid.uuid4())

    conn = create_connection(database_name=os.environ.get("DB_NAME"))
    cursor = conn.cursor()
    query = """
        INSERT INTO sessions (session_id, file_id)
        VALUES (%s, %s);
    """
    cursor.execute(query, (session_id, file_id))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Session '{session_id}' created successfully.")
    return session_id


def delete_session_by_id(session_id) -> None:
    """
    Delete a session by its ID.

    Args:
        session_id (str): The ID of the session to delete.

    Raises:
        mysql.connector.Error: If there is an error while deleting the session.
    """
    conn = create_connection(database_name=os.environ.get("DB_NAME"))
    cursor = conn.cursor()
    query = """
        DELETE FROM sessions WHERE session_id = %s;
    """
    cursor.execute(query, (session_id,))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Session '{session_id}' deleted successfully.")


def save_question_answer(session_id, question, answer) -> None:
    """
    Save a question and answer to the database.

    Args:
        session_id (str): The ID of the session the question and answer belongs to.
        question (str): The question asked.
        answer (str): The answer given.

    Raises:
        mysql.connector.Error: If there is an error while saving the question and answer.
    """

    conn = create_connection(database_name=os.environ.get("DB_NAME"))
    cursor = conn.cursor()
    query = """
        INSERT INTO chat_history (session_id, question, answer)
        VALUES (%s, %s, %s);
    """
    cursor.execute(query, (session_id, question, answer))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Question and answer for session '{session_id}' saved successfully.")


def get_all_file_info() -> list:
    """
    Get all file information from the database.

    Returns:
        list: A list of dictionaries. Each dictionary contains the file_id, source, and created_at of a file.
    """

    conn = create_connection(database_name=os.environ.get("DB_NAME"))
    cursor = conn.cursor()
    query = """
        SELECT file_id, source, created_at FROM files;
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    if not result:
        return []
    return [
        {
            "file_id": row[0],
            "source": row[1],
            "created_at": row[2].strftime("%Y-%m-%d %H:%M:%S"),
        }
        for row in result
    ]


def get_file_by_id(file_id) -> Union[str, None]:
    """
    Retrieve the source of a file from the database using its file ID.

    Args:
        file_id (int): The ID of the file to retrieve.

    Returns:
        Union[str, None]: The source of the file if found, otherwise None.
    """

    conn = create_connection(database_name=os.environ.get("DB_NAME"))
    cursor = conn.cursor()
    query = """
        SELECT source FROM files WHERE file_id = %s;
    """
    cursor.execute(query, (file_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        print(result[0])
        return result[0]
    else:
        return None


def get_all_sessions(file_id) -> list:
    """
    Retrieve all session information from the database for a given file ID.

    Args:
        file_id (int): The ID of the file to retrieve sessions for.

    Returns:
        list: A list of dictionaries. Each dictionary contains the session_id and created_at of a session.
    """
    conn = create_connection(database_name=os.environ.get("DB_NAME"))
    cursor = conn.cursor()
    query = """
        SELECT session_id, created_at FROM sessions WHERE file_id = %s;
    """
    cursor.execute(query, (file_id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    if len(result) == 0:
        return []
    return [
        {"session_id": row[0], "created_at": row[1].strftime("%Y-%m-%d %H:%M:%S")}
        for row in result
    ]


def get_all_question_answer(session_id) -> list:
    """
    Retrieve all question and answer information from the database for a given session ID.

    Args:
        session_id (str): The ID of the session to retrieve question and answer information for.

    Returns:
        list: A list of dictionaries. Each dictionary contains the question, answer, and timestamp of a question and answer pair.
    """
    conn = create_connection(database_name=os.environ.get("DB_NAME"))
    cursor = conn.cursor()
    query = """
        SELECT question, answer, timestamp FROM chat_history WHERE session_id = %s;
    """
    cursor.execute(query, (session_id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    if len(result) == 0:
        return []
    return [
        {
            "question": row[0],
            "answer": row[1],
            "timestamp": row[2].strftime("%Y-%m-%d %H:%M:%S"),
        }
        for row in result
    ]
