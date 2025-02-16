from database import get_file_by_id
from question_handler import QuestionHandlerConfig, QuestionHandler
import os

UPLOAD_PATH = "uploads"


class AppManager:
    def __init__(self):
        """
        Initializes the AppManager instance with default values.

        Attributes:
            current_app (dict or None): Holds the current application configuration and state.
        """
        self.current_app = None

    async def active_app(self, file_id, llm_config, embedding_config, reranker_config):
        """
        Activate an application with the given file_id and configuration.
        Saves the QuestionHandler instance in the current_app attribute.

        Args:
            file_id (int): The ID of the file to load.
            llm_config (dict): Configuration for the ChatOpenAI, e.g., model, base_url, api_key.
            embedding_config (dict): Configuration for the FastEmbed embedding model, e.g., model_name, max_length, batch_size.
            reranker_config (dict): Configuration for the FastEmbed TextCrossEncoder, e.g., model_name.
        """
        source = get_file_by_id(file_id)
        config = QuestionHandlerConfig(
            file_path=os.path.join(UPLOAD_PATH, source),
            llm_config=llm_config,
            embedding_config=embedding_config,
            reranker_config=reranker_config,
        )
        app = QuestionHandler(config).build_graph()
        self.current_app = {"file_id": file_id, "app": app}
