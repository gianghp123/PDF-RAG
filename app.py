import gradio as gr
import os
from pathlib import Path
from gradio import ChatMessage
import json
from config import embedding_config, llm_config, reranker_config
from question_handler import QuestionHandler, QuestionHandlerConfig
import re


UPLOAD_DIR = "uploads"
HISTORY_FILE = "chat_histories.json"
CURRENT_FILE = "current_file.json"


def clean_html_text(text):
    text = re.sub(r"```html\n?", "", text)
    text = re.sub(r"\n?```", "", text)
    text = text.replace("\\n", "\n")
    return text.strip()


class ChatManager:
    def __init__(self):
        self.chat_histories = self.load_histories()
        self.app = None
        self.current_file = None
        # Khôi phục file gần nhất khi khởi tạo
        self.restore_last_file()

    def restore_last_file(self):
        """Khôi phục file gần nhất từ current_file.json và khởi tạo QuestionHandler."""
        if os.path.exists(CURRENT_FILE):
            with open(CURRENT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_file = data.get("current_file")
                if last_file and os.path.exists(f"{UPLOAD_DIR}/{last_file}"):
                    self.current_file = last_file
                    # Khởi tạo QuestionHandler cho file gần nhất
                    question_handler_config = QuestionHandlerConfig(
                        file_path=f"{UPLOAD_DIR}/{last_file}",
                        llm_config=llm_config,
                        embedding_config=embedding_config,
                        reranker_config=reranker_config,
                    )
                    self.app = QuestionHandler(question_handler_config).build_graph()

    def upload_file(self, file):
        """Xử lý file PDF được upload và khởi tạo QuestionHandler."""
        Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

        if not file:
            return "Please upload a file!", None

        file_name = os.path.basename(file.name)
        file_location = f"{UPLOAD_DIR}/{file_name}"

        with open(file.name, "rb") as source_file:
            with open(file_location, "wb") as target_file:
                target_file.write(source_file.read())

        with open(CURRENT_FILE, "w", encoding="utf-8") as f:
            json.dump({"current_file": file_name}, f)

        question_handler_config = QuestionHandlerConfig(
            file_path=file_location,
            llm_config=llm_config,
            embedding_config=embedding_config,
            reranker_config=reranker_config,
        )
        self.app = QuestionHandler(question_handler_config).build_graph()
        self.current_file = file_name

        formatted_history = self.format_history_for_display(
            self.get_history_for_file(file_name)
        )
        return f"File '{file_name}' uploaded successfully!", gr.update(
            value=formatted_history, label=f"Current file: {file_name}"
        )

    def load_histories(self):
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    return {
                        file: [
                            ChatMessage(role=msg[0], content=msg[1]) for msg in history
                        ]
                        for file, history in data.items()
                    }
        return {}

    def save_histories(self):
        data = {
            file: [(msg.role, msg.content) for msg in history]
            for file, history in self.chat_histories.items()
        }
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_history_for_file(self, selected_file):
        if selected_file not in self.chat_histories:
            self.chat_histories[selected_file] = []
        return self.chat_histories[selected_file]

    def format_history_for_display(self, history):
        formatted_history = []
        for msg in history:
            if msg.role == "assistant":
                cleaned_content = clean_html_text(msg.content)
                formatted_history.append(
                    ChatMessage(role="assistant", content=cleaned_content)
                )
            else:
                formatted_history.append(msg)
        return formatted_history

    def generate_response(self, message, history):
        if not self.current_file or not self.app:
            return "Please upload a file first."

        current_history = self.get_history_for_file(self.current_file)
        current_history.append(ChatMessage(role="user", content=message))

        response = self.app.invoke(
            {
                "question": message,
                "max_retries": 1,
            }
        )
        answer = response["final_answer"]
        cleaned_answer = clean_html_text(answer)

        current_history.append(ChatMessage(role="assistant", content=cleaned_answer))
        self.save_histories()

        return self.format_history_for_display(current_history)


chat_manager = ChatManager()

css = ".chatbot {font-size: 12px;}"

with gr.Blocks(theme=gr.themes.Base(), css=css) as demo:
    with gr.Sidebar():
        upload_input = gr.File(label="Upload File", file_types=[".pdf"])
        upload_btn = gr.Button("Upload")
        upload_output = gr.Textbox(label="Upload Status", interactive=False)

    initial_history = (
        chat_manager.format_history_for_display(
            chat_manager.get_history_for_file(chat_manager.current_file)
        )
        if chat_manager.current_file
        else []
    )
    chat_interface = gr.ChatInterface(
        fn=chat_manager.generate_response,
        type="messages",
        chatbot=gr.Chatbot(
            value=initial_history,
            render_markdown=True,
            height=400,
            type="messages",
            elem_id=".chatbot",
            show_copy_button=True,
            label=f"Current file: {chat_manager.current_file or 'None'}",
        ),
    )

    upload_btn.click(
        fn=chat_manager.upload_file,
        inputs=[upload_input],
        outputs=[
            upload_output,
            chat_interface.chatbot,
        ],
    )

if __name__ == "__main__":
    demo.launch()