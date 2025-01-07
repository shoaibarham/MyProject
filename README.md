# 💬 SQL Chat with LangChain and Streamlit

A powerful and intuitive Streamlit application that enables natural language querying of SQL databases. Built with LangChain for SQL query generation and Groq for natural language processing, this app supports both SQLite and MySQL databases.

## 🌟 Features

- Natural language to SQL query conversion
- Support for both SQLite and MySQL databases
- Interactive chat interface
- Real-time query execution and results display
- Secure API key and database credential management
- Clear message history functionality
- Streamlit callback handling for real-time updates

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Groq API key
- SQLite database (included) or MySQL database access

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/sql-chat-app.git
cd sql-chat-app
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

## 💻 Usage

### Setting Up the Database

#### Option 1: SQLite Database
- Use the provided `student.db` file in the project directory
- To create a new database, run:
```bash
python sqlite.py
```

#### Option 2: MySQL Database
You'll need the following information:
- Host name
- Username
- Password
- Database name

### Using the Application

1. **Configure Database**
   - Select your database type (SQLite or MySQL) in the sidebar
   - If using MySQL, enter your connection details

2. **Add API Key**
   - Enter your Groq API key in the sidebar

3. **Start Querying**
   - Type your questions in natural language
   - Example: "Show me all students with grades above 90"
   - View the generated SQL query and results

4. **Message History**
   - View your conversation history
   - Clear history using the sidebar button

## 🛠️ Technical Details

### Components

- **DatabaseConfig**: Handles database connection and configuration
- **ChatAgent**: Manages the LangChain agent and query processing
- **StreamlitUI**: Handles the user interface and interaction flow

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
