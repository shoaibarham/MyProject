import streamlit as st
from pathlib import Path
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq
from typing import Optional, Dict, List

st.set_page_config(page_title="LangChain SQL Chat", page_icon="💬", layout="wide")

# Custom CSS for modern styling
st.markdown(
    """
    <style>
    body { background-color: #f4f4f9; }
    .big-font { font-size: 32px !important; font-weight: bold; color: #333; }
    .medium-font { font-size: 18px !important; color: #555; }
    .chat-message { padding: 12px; border-radius: 10px; margin: 8px 0; }
    .user-message { background-color: #0078D7; color: white; text-align: right; }
    .assistant-message { background-color: #e1eafd; text-align: left; }
    .footer { text-align: center; padding: 10px; font-size: 14px; color: #777; }
    </style>
    """,
    unsafe_allow_html=True,
)

class DatabaseConfig:
    LOCAL_DB = "USE_LOCALDB"
    MYSQL = "USE_MYSQL"

    def __init__(self):
        self.db_uri: str = ''
        self.mysql_config: Dict[str, str] = {}

    def configure_db(self) -> SQLDatabase:
        try:
            if self.db_uri == self.LOCAL_DB:
                return self._configure_sqlite()
            elif self.db_uri == self.MYSQL:
                return self._configure_mysql()
            else:
                raise ValueError("Invalid database configuration.")
        except Exception as e:
            st.error(f"Database error: {str(e)}")
            st.stop()

    def _configure_sqlite(self) -> SQLDatabase:
        try:
            dbfilepath = (Path(__file__).parent / "routes.db").absolute()
            if not dbfilepath.exists():
                raise FileNotFoundError(f"Database file not found: {dbfilepath}")
            creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
            return SQLDatabase(create_engine("sqlite:///", creator=creator))
        except Exception as e:
            st.error(f"SQLite error: {str(e)}")
            st.stop()

    def _configure_mysql(self) -> SQLDatabase:
        try:
            if not all(field in self.mysql_config for field in ["host", "user", "password", "database"]):
                raise ValueError("Incomplete MySQL credentials.")
            connection_string = (
                f"mysql+mysqlconnector://{self.mysql_config['user']}:{self.mysql_config['password']}"
                f"@{self.mysql_config['host']}/{self.mysql_config['database']}"
            )
            return SQLDatabase(create_engine(connection_string))
        except Exception as e:
            st.error(f"MySQL error: {str(e)}")
            st.stop()

class ChatAgent:
    def __init__(self, db: SQLDatabase, api_key: str):
        self.llm = ChatGroq(groq_api_key=api_key, model='gemma2-9b-it')
        self.toolkit = SQLDatabaseToolkit(db=db, llm=self.llm)
        self.agent = create_sql_agent(
            llm=self.llm, 
            toolkit=self.toolkit,
            verbose=False,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
        )

    def get_response(self, query: str, callbacks: List[StreamlitCallbackHandler]) -> str:
        raw_response = self.agent.run(query, callbacks=callbacks)
        return raw_response.split("Complete!")[-1].strip() if "Complete!" in raw_response else raw_response.strip()

class StreamlitUI:
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.setup_sidebar()
        self.display_header()

    def display_header(self):
        st.markdown('<p class="big-font">💬 SQL Chat Assistant</p>', unsafe_allow_html=True)
        st.markdown("---")

    def setup_sidebar(self):
        with st.sidebar:
            st.markdown("### Database Configuration")
            options = ["SQLite (routes.db)", "Connect to MySQL"]
            choice = st.radio("Choose Database:", options)
            self.db_config.db_uri = DatabaseConfig.MYSQL if options.index(choice) == 1 else DatabaseConfig.LOCAL_DB
            
            if self.db_config.db_uri == DatabaseConfig.MYSQL:
                self.db_config.mysql_config = {
                    "host": st.text_input("Host"),
                    "user": st.text_input("User"),
                    "password": st.text_input("Password", type="password"),
                    "database": st.text_input("Database")
                }
            
            st.markdown("### API Key")
            self.api_key = st.text_input("Groq API Key", type="password")

    def initialize_chat(self):
        if not self.api_key:
            st.warning("Enter Groq API Key to continue.")
            return None
        try:
            db = self.db_config.configure_db()
            return ChatAgent(db, self.api_key) if db else None
        except Exception as e:
            st.error(f"Chat setup error: {str(e)}")
            return None

    def run_chat_interface(self, chat_agent: ChatAgent):
        if not chat_agent:
            return 
        
        if "messages" not in st.session_state or st.sidebar.button("Clear Chat"):
            st.session_state["messages"] = [{'role': 'assistant', 'content': 'How can I help you?'}]
        
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        user_query = st.chat_input("Enter your SQL question:")
        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)
            with st.chat_message("assistant"):
                response = chat_agent.get_response(user_query, callbacks=[])
                st.session_state.messages.append({'role': 'assistant', 'content': response})
                st.write(response)

    def display_footer(self):
        st.markdown('<div class="footer">SQL Chat Assistant - Powered by LangChain</div>', unsafe_allow_html=True)

def main():
    ui = StreamlitUI()
    chat_agent = ui.initialize_chat()
    ui.run_chat_interface(chat_agent)
    ui.display_footer()

if __name__ == "__main__":
    main()
