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


# Set page config FIRST
st.set_page_config(page_title="LangChain SQL Chat", page_icon="💬", layout="wide")


# Custom CSS for styling
st.markdown(
    """
    <style>
    .big-font {
        font-size: 30px !important;
        font-weight: bold;
    }
    .medium-font {
        font-size: 20px !important;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f1f1f1;
        text-align: center;
        padding: 10px;
    }
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
                raise ValueError("Invalid database configuration. Please choose a valid database type.")
        except Exception as e:
            st.error(f"Error configuring database: {str(e)}")
            st.stop()  # Stop the app if there's an error

    def _configure_sqlite(self) -> SQLDatabase:
        try:
            dbfilepath = (Path(__file__).parent / "student.db").absolute()  # Ensure the file exists
            if not dbfilepath.exists():
                raise FileNotFoundError(f"SQLite database file not found at: {dbfilepath}")
            
            creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
            return SQLDatabase(create_engine("sqlite:///", creator=creator))
        except Exception as e:
            st.error(f"Error configuring SQLite database: {str(e)}")
            st.stop()

    def _configure_mysql(self) -> SQLDatabase:
        try:
            required_fields = ["host", "user", "password", "database"]
            if not all(field in self.mysql_config for field in required_fields):
                raise ValueError("Please provide all MySQL connection details.")
            
            connection_string = (
                f"mysql+mysqlconnector://{self.mysql_config['user']}:{self.mysql_config['password']}"
                f"@{self.mysql_config['host']}/{self.mysql_config['database']}"
            )
            return SQLDatabase(create_engine(connection_string))
        except Exception as e:
            st.error(f"Error configuring MySQL database: {str(e)}")
            st.stop()


class ChatAgent: 
    def __init__(self, db: SQLDatabase, api_key: str):
        self.llm = ChatGroq(groq_api_key=api_key, model='gemma2-9b-it')
        self.toolkit = SQLDatabaseToolkit(db=db, llm=self.llm)
        self.agent = create_sql_agent(
            llm=self.llm, 
            toolkit=self.toolkit,
            verbose=True, 
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
        )

    def get_response(self, query: str, callbacks: List[StreamlitCallbackHandler]) -> str: 
        return self.agent.run(query, callbacks=callbacks)


class StreamlitUI:
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.setup_sidebar()
        self.display_header()
        self.display_summary()

    def display_header(self):
        st.markdown('<p class="big-font">💬 Chat with SQL Database</p>', unsafe_allow_html=True)
        st.markdown('<p class="medium-font">Ask natural language questions and get answers from your SQL database!</p>', unsafe_allow_html=True)
        st.markdown("---")

    def display_summary(self):
        st.markdown("""
        ### **How It Works**
        1. **Choose Your Database**: Select either a local SQLite database or connect to a MySQL database.
        2. **Enter Your Query**: Type your question in natural language (e.g., "Show me all students with grades above 90").
        3. **Get Insights**: The app will translate your query into SQL, execute it, and display the results.
        """)
        st.markdown("---")

    def setup_sidebar(self):
        with st.sidebar:
            st.markdown("### **Database Configuration**")
            radio_opts = ["Use SQLLite 3 Database: Student.db", "Connect to your SQL Database"]
            selected_opt = st.radio(
                label="Choose your database:", 
                options=radio_opts
            )
            
            if radio_opts.index(selected_opt) == 1:  # Connect to SQL workbench
                self.db_config.db_uri = DatabaseConfig.MYSQL
                self.db_config.mysql_config = {
                    "host": st.text_input("MySQL Host Name"),
                    "user": st.text_input("SQL Username"),
                    "password": st.text_input("SQL Password", type="password"),
                    "database": st.text_input("SQL Database Name")
                }
            else:  # Use SQLite
                self.db_config.db_uri = DatabaseConfig.LOCAL_DB

            st.markdown("---")
            st.markdown("### **API Key**")
            self.api_key = st.text_input("Groq API Key", type="password")
            st.markdown("---")
            st.markdown("### **Instructions**")
            st.info("""
            - Provide your Groq API key to enable the chat functionality.
            - Ensure your database credentials are correct.
            - Use natural language to query your database.
            """)

    def initialize_chat(self):
        if not self.api_key:
            st.info("Please add Groq API key")
            return None
        
        try:
            db = self.db_config.configure_db()
            if db is None:
                st.error("Failed to configure the database.")
                return None
            return ChatAgent(db, self.api_key)
        except Exception as e:
            st.error(f"Error initializing chat agent: {str(e)}")
            return None

    def run_chat_interface(self, chat_agent: ChatAgent):
        if not chat_agent:
            return 
        
        if "messages" not in st.session_state or st.sidebar.button("Clear Message History"):
            st.session_state["messages"] = [
                {'role': 'assistant', 'content': 'How can I help you?'}
                ]
        
        for message in st.session_state.messages:
            st.chat_message(message["role"]).write(message["content"])

        user_query = st.chat_input(placeholder="What query do you want to perform on the database? ")

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)

            with st.chat_message("assistant"):
                streamlit_callback = StreamlitCallbackHandler(st.container())  # Create the callback handler
                response = chat_agent.get_response(user_query, callbacks=[streamlit_callback])  # Pass `callbacks` (plural)
                # st.session_state.messages.append(
                #     {'role': 'assistant', 'content': response}
                # )
                # st.write(response)

                # Format the response as a list if it is a list
                if isinstance(response, list):
                    st.markdown("**Response:**")
                    for item in response:
                        if isinstance(item, dict):  # Check if each item is a dictionary
                            st.markdown(f"- **{item['name']}**: Grade = {item['grade']}")
                        else:
                            st.markdown(f"- {item}")
                else:
                    st.write(response)  # Display as plain text if not a list

                st.session_state.messages.append(
                    {'role': 'assistant', 'content': response}
                )

    def display_footer(self):
        st.markdown("---")
        st.markdown(
            '<div class="footer">'
            'Made with ❤️ by Akshada | Powered by LangChain and Streamlit'
            '</div>',
            unsafe_allow_html=True
        )


def main():
    ui = StreamlitUI()
    chat_agent = ui.initialize_chat()
    ui.run_chat_interface(chat_agent)
    ui.display_footer()


if __name__ == "__main__":
    main()