# MCP Production Project Structure

## 📁 New Organized Structure

```
blackhole_mcp_production/
├── 📂 core/                           # Core MCP system
│   ├── mcp_server.py                  # Main production server
│   ├── mcp_client.py                  # Command-line client
│   ├── conversation_engine.py         # Conversational AI with MongoDB search
│   ├── inter_agent_coordinator.py     # Agent communication coordinator
│   └── config.py                      # Configuration management
│
├── 📂 agents/                         # Production agents directory
│   ├── __init__.py                    # Agent discovery
│   ├── base_agent.py                  # Base agent class
│   ├── agent_manager.py               # Agent lifecycle management
│   │
│   ├── 📂 live_data/                  # Live data agents
│   │   ├── __init__.py
│   │   ├── weather_agent.py           # 🌤️ Live weather monitoring
│   │   └── news_agent.py              # 📰 Live news (future)
│   │
│   ├── 📂 processing/                 # Processing agents
│   │   ├── __init__.py
│   │   ├── math_agent.py              # 🔢 Mathematical calculations
│   │   ├── image_ocr_agent.py         # 🖼️ Image text extraction
│   │   ├── document_agent.py          # 📄 Document analysis
│   │   └── text_analyzer_agent.py     # 📝 Text analysis (future)
│   │
│   ├── 📂 communication/              # Communication agents
│   │   ├── __init__.py
│   │   ├── email_agent.py             # 📧 Email automation
│   │   ├── calendar_agent.py          # 📅 Calendar management
│   │   └── notification_agent.py      # 🔔 Notifications (future)
│   │
│   └── 📂 specialized/                # Specialized agents
│       ├── __init__.py
│       ├── workflow_agent.py          # 🔄 Complex workflows
│       └── search_agent.py            # 🔍 Advanced search
│
├── 📂 database/                       # Database management
│   ├── __init__.py
│   ├── mongodb_manager.py             # MongoDB connection & operations
│   ├── conversation_history.py        # Chat history management
│   ├── agent_logs.py                  # Agent activity logging
│   ├── query_cache.py                 # Query caching system
│   └── schemas/                       # Database schemas
│       ├── conversation_schema.py
│       ├── agent_log_schema.py
│       └── extracted_data_schema.py
│
├── 📂 storage/                        # Data storage
│   ├── 📂 agent_logs/                 # Agent execution logs
│   ├── 📂 conversation_history/       # Chat conversations
│   ├── 📂 extracted_data/             # OCR & document extracts
│   ├── 📂 uploaded_files/             # User uploaded files
│   └── 📂 processed_outputs/          # Agent processing results
│
├── 📂 web_interface/                  # Web interface
│   ├── static/                        # CSS, JS, images
│   ├── templates/                     # HTML templates
│   └── app.py                         # Web application
│
├── 📂 tests/                          # Testing suite
│   ├── test_agents.py                 # Agent testing
│   ├── test_database.py               # Database testing
│   └── test_integration.py            # Integration testing
│
├── 📂 config/                         # Configuration files
│   ├── .env                           # Environment variables
│   ├── agent_config.yaml             # Agent configurations
│   └── database_config.yaml          # Database settings
│
├── 📂 scripts/                        # Utility scripts
│   ├── setup_project.py               # Project setup
│   ├── migrate_data.py                # Data migration
│   └── start_production.py            # Production startup
│
├── 📂 docs/                           # Documentation
│   ├── API.md                         # API documentation
│   ├── AGENTS.md                      # Agent documentation
│   └── DEPLOYMENT.md                  # Deployment guide
│
├── requirements.txt                   # Dependencies
├── README.md                          # Project overview
└── docker-compose.yml                # Docker configuration
```

## 🎯 Key Features

### 🤖 Agent Organization
- **live_data/**: Real-time data agents (weather, news, etc.)
- **processing/**: Data processing agents (math, OCR, documents)
- **communication/**: Communication agents (email, calendar)
- **specialized/**: Complex workflow and search agents

### 💾 MongoDB Integration
- **Conversation History**: All user interactions stored
- **Agent Logs**: Complete agent execution tracking
- **Extracted Data**: OCR text, document analysis results
- **Query Cache**: Fast retrieval of previous results

### 🔍 Intelligent Search
- **MongoDB First**: Search existing data before calling agents
- **Conversational AI**: Context-aware responses
- **Inter-Agent Communication**: Agents collaborate for complex queries

### 📊 Data Flow
1. User query → MongoDB search first
2. If found → Conversational response
3. If not found → Route to appropriate agent(s)
4. Agent processing → Store results in MongoDB
5. Inter-agent communication for complex tasks
6. Final response to user
