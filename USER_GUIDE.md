# 🤖 MCP Agent System - User Guide

## 🎯 **How to Use Your User-Friendly MCP System**

Your MCP (Model Context Protocol) system is now fully set up with MongoDB integration and multiple user-friendly interfaces. Here's how to use it:

---

## 🚀 **Quick Start**

### **1. Start the System**
```bash
python production_mcp_server.py
```

### **2. Choose Your Interface**

#### **🌐 Web Interface (Recommended)**
- Open: http://localhost:8000
- Features: Beautiful UI, real-time responses, query history
- Best for: Interactive exploration and testing

#### **💻 Interactive Command Line**
```bash
python user_friendly_interface.py
```
- Features: Terminal-based chat interface
- Best for: Power users and automation

#### **⚡ Quick Single Queries**
```bash
python quick_query.py "Your question here"
```
- Features: One-shot queries with instant results
- Best for: Scripts and quick tests

---

## 💬 **What You Can Ask**

### **🔢 Math Calculations**
```
Calculate 25 * 4
What is 100 + 50?
Compute 20% of 500
Solve 15 + 25 * 2
Find the square root of 144
```

### **🌤️ Weather Queries**
```
What is the weather in Mumbai?
Mumbai weather
Temperature in Delhi
Weather forecast for Bangalore
Climate in New York
```

### **📄 Document Analysis**
```
Analyze this text: Your text content here
Process document content
Extract information from text
Summarize this paragraph: Your content
```

---

## 🌐 **Web Interface Guide**

### **Features:**
- **Real-time Status**: See server, MongoDB, and agent status
- **Query Input**: Type questions naturally
- **Example Buttons**: Click to try sample queries
- **Response Display**: Formatted results with all details
- **Query History**: Track your previous questions
- **Clear/Refresh**: Reset interface and update status

### **How to Use:**
1. Open http://localhost:8000
2. Check the status indicators (should all be green ✅)
3. Type your question in the input box
4. Click "🚀 Send Query" or press Enter
5. View the formatted response below
6. Use "📝 History" to see past queries

---

## 💻 **Interactive Command Line Guide**

### **Starting Interactive Mode:**
```bash
python user_friendly_interface.py
```

### **Available Commands:**
- **help** - Show detailed help guide
- **status** - Check system health
- **history** - View query history
- **clear** - Clear screen
- **quit/exit** - Exit the interface

### **Example Session:**
```
🎯 Your Query: Calculate 25 * 4
⏳ Processing your query...

============================================================
📤 QUERY: Calculate 25 * 4
============================================================
🤖 AGENT: math_agent
✅ STATUS: SUCCESS
🔢 ANSWER: 100.0
💾 MONGODB STORED: ❌ No
🕐 TIME: 12:08:31
============================================================
```

---

## ⚡ **Quick Query Tool Guide**

### **Single Query Syntax:**
```bash
python quick_query.py "Your question here"
```

### **Examples:**
```bash
# Math calculation
python quick_query.py "Calculate 25 * 4"

# Weather query
python quick_query.py "What is the weather in Mumbai?"

# Document analysis
python quick_query.py "Analyze this text: Hello world"
```

### **Output Format:**
```
🚀 MCP QUICK QUERY
==================================================
📤 Query: Calculate 100 + 200
==================================================
✅ Server: Ready
✅ MongoDB: Connected
✅ Agents: 3 loaded

⏳ Processing...
📊 RESULT:
------------------------------
🤖 Agent: math_agent
✅ Status: SUCCESS
🔢 Answer: 300.0
💾 MongoDB: ❌ Not Stored
🕐 Time: 12:11:01

✅ Query completed successfully!
```

---

## 🤖 **Available Agents**

### **🔢 Math Agent**
- **Triggers**: calculate, compute, math, +, -, *, /, %
- **Capabilities**: Basic arithmetic, percentages, formulas
- **Examples**: "Calculate 25 * 4", "What is 20% of 500?"

### **🌤️ Weather Agent**
- **Triggers**: weather, temperature, forecast, climate
- **Capabilities**: Real-time weather data, forecasts
- **Examples**: "Weather in Mumbai", "Temperature in Delhi"

### **📄 Document Agent**
- **Triggers**: analyze, document, text, process
- **Capabilities**: Text analysis, content processing
- **Examples**: "Analyze this text: Hello world"

---

## 💾 **MongoDB Integration**

### **What Gets Stored:**
- All queries and responses
- Agent processing results
- Timestamps and metadata
- Enhanced analytics data

### **Storage Features:**
- **Real-time storage**: Every interaction saved
- **Query history**: Track all past queries
- **Agent analytics**: Performance metrics
- **Enhanced functions**: Advanced storage capabilities

### **Access Stored Data:**
```python
# Using enhanced storage functions
from enhanced_mongodb_storage import get_agent_history, get_all_agent_stats

# Get agent history
history = get_agent_history("math_agent", limit=10)

# Get statistics
stats = get_all_agent_stats()
```

---

## 🔧 **Troubleshooting**

### **Server Not Running:**
```bash
# Start the server
python production_mcp_server.py

# Check if running
curl http://localhost:8000/api/health
```

### **MongoDB Issues:**
- Check your .env file for correct MongoDB credentials
- Verify internet connection for cloud MongoDB
- Run: `python connect_agents_mongodb_fixed.py`

### **Agent Not Responding:**
- Check agent status: http://localhost:8000/api/agents
- Restart server: Stop and run `python production_mcp_server.py`
- Check logs for error messages

---

## 📊 **System Monitoring**

### **Health Check:**
- Web: http://localhost:8000/api/health
- Command: `curl http://localhost:8000/api/health`

### **Agent Status:**
- Web: http://localhost:8000/api/agents
- Interactive: Type `status` in interactive mode

### **API Documentation:**
- Full API docs: http://localhost:8000/docs

---

## 💡 **Tips for Best Results**

### **Query Writing:**
- Be specific and clear
- Use natural language
- Include context when needed
- Try different phrasings if needed

### **Math Queries:**
- Use standard operators: +, -, *, /, %
- Be explicit: "Calculate" or "What is"
- Include units when relevant

### **Weather Queries:**
- Use city names clearly
- Try variations: "weather in", "temperature of"
- Include country for ambiguous cities

### **Document Analysis:**
- Prefix with "Analyze this text:"
- Provide clear, readable content
- Specify what type of analysis you want

---

## 🎉 **You're All Set!**

Your user-friendly MCP system is ready to use with:
- ✅ Multiple interfaces (web, interactive, quick query)
- ✅ MongoDB storage and analytics
- ✅ 3 intelligent agents (math, weather, document)
- ✅ Real-time processing and responses
- ✅ Query history and monitoring

**Start exploring with any interface and enjoy your intelligent agent system!**
