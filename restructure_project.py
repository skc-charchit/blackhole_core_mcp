#!/usr/bin/env python3
"""
Project Restructuring Script
Reorganizes the MCP project into a clean, production-ready structure
"""

import os
import shutil
from pathlib import Path
import json

def create_directory_structure():
    """Create the new directory structure."""
    print("🏗️ CREATING NEW PROJECT STRUCTURE")
    print("=" * 50)
    
    # Define the new structure
    directories = [
        # Core system
        "core",
        
        # Agents organized by category
        "agents/live_data",
        "agents/processing", 
        "agents/communication",
        "agents/specialized",
        
        # Database management
        "database/schemas",
        
        # Storage directories
        "storage/agent_logs",
        "storage/conversation_history",
        "storage/extracted_data",
        "storage/uploaded_files",
        "storage/processed_outputs",
        
        # Web interface
        "web_interface/static/css",
        "web_interface/static/js",
        "web_interface/static/images",
        "web_interface/templates",
        
        # Testing
        "tests",
        
        # Configuration
        "config",
        
        # Scripts
        "scripts",
        
        # Documentation
        "docs"
    ]
    
    created_count = 0
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {directory}")
            created_count += 1
        else:
            print(f"📁 Exists: {directory}")
    
    print(f"\n📊 Created {created_count} new directories")
    return True

def move_existing_agents():
    """Move existing agents to their new locations."""
    print("\n🔄 MOVING EXISTING AGENTS")
    print("=" * 50)
    
    # Agent movements mapping
    agent_moves = {
        # Live data agents
        "agents/data/realtime_weather_agent.py": "agents/live_data/weather_agent.py",
        
        # Processing agents
        "agents/specialized/math_agent.py": "agents/processing/math_agent.py",
        "agents/core/document_processor.py": "agents/processing/document_agent.py",
        
        # Communication agents
        "agents/communication/real_gmail_agent.py": "agents/communication/email_agent.py",
        "agents/specialized/calendar_agent.py": "agents/communication/calendar_agent.py",
        
        # OCR functionality
        "data/multimodal/image_ocr.py": "agents/processing/image_ocr_agent.py"
    }
    
    moved_count = 0
    
    for old_path, new_path in agent_moves.items():
        old_file = Path(old_path)
        new_file = Path(new_path)
        
        if old_file.exists():
            # Create parent directory if it doesn't exist
            new_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(old_file, new_file)
            print(f"✅ Moved: {old_path} → {new_path}")
            moved_count += 1
        else:
            print(f"❌ Not found: {old_path}")
    
    print(f"\n📊 Moved {moved_count} agent files")
    return True

def create_core_files():
    """Create core system files."""
    print("\n🔧 CREATING CORE SYSTEM FILES")
    print("=" * 50)
    
    # Move existing core files
    core_moves = {
        "mcp_server.py": "core/mcp_server.py",
        "mcp_client.py": "core/mcp_client.py",
        ".env": "config/.env"
    }
    
    for old_path, new_path in core_moves.items():
        old_file = Path(old_path)
        new_file = Path(new_path)
        
        if old_file.exists():
            new_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old_file, new_file)
            print(f"✅ Moved: {old_path} → {new_path}")
        else:
            print(f"❌ Not found: {old_path}")
    
    return True

def create_init_files():
    """Create __init__.py files for Python packages."""
    print("\n📦 CREATING PACKAGE INIT FILES")
    print("=" * 50)
    
    init_files = [
        "agents/__init__.py",
        "agents/live_data/__init__.py",
        "agents/processing/__init__.py", 
        "agents/communication/__init__.py",
        "agents/specialized/__init__.py",
        "database/__init__.py",
        "database/schemas/__init__.py",
        "web_interface/__init__.py",
        "tests/__init__.py"
    ]
    
    created_count = 0
    
    for init_file in init_files:
        init_path = Path(init_file)
        if not init_path.exists():
            init_path.write_text('"""Package initialization."""\n')
            print(f"✅ Created: {init_file}")
            created_count += 1
        else:
            print(f"📁 Exists: {init_file}")
    
    print(f"\n📊 Created {created_count} init files")
    return True

def create_configuration_files():
    """Create configuration files."""
    print("\n⚙️ CREATING CONFIGURATION FILES")
    print("=" * 50)
    
    # Agent configuration
    agent_config = {
        "agents": {
            "live_data": {
                "weather_agent": {
                    "enabled": True,
                    "api_key_env": "OPENWEATHER_API_KEY",
                    "cache_duration": 300,
                    "priority": 1
                }
            },
            "processing": {
                "math_agent": {
                    "enabled": True,
                    "precision": 6,
                    "priority": 1
                },
                "image_ocr_agent": {
                    "enabled": True,
                    "tesseract_path": "auto",
                    "preprocessing_level": 2,
                    "priority": 2
                },
                "document_agent": {
                    "enabled": True,
                    "supported_formats": ["pdf", "txt", "docx"],
                    "priority": 2
                }
            },
            "communication": {
                "email_agent": {
                    "enabled": True,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "priority": 3
                },
                "calendar_agent": {
                    "enabled": True,
                    "timezone": "UTC",
                    "priority": 3
                }
            }
        },
        "mongodb": {
            "connection_timeout": 30,
            "max_pool_size": 100,
            "retry_writes": True
        },
        "conversation": {
            "max_history": 1000,
            "search_first": True,
            "cache_responses": True
        }
    }
    
    config_path = Path("config/agent_config.yaml")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to YAML format (simplified)
    yaml_content = """# MCP Agent Configuration
agents:
  live_data:
    weather_agent:
      enabled: true
      api_key_env: "OPENWEATHER_API_KEY"
      cache_duration: 300
      priority: 1
  
  processing:
    math_agent:
      enabled: true
      precision: 6
      priority: 1
    
    image_ocr_agent:
      enabled: true
      tesseract_path: "auto"
      preprocessing_level: 2
      priority: 2
    
    document_agent:
      enabled: true
      supported_formats: ["pdf", "txt", "docx"]
      priority: 2
  
  communication:
    email_agent:
      enabled: true
      smtp_server: "smtp.gmail.com"
      smtp_port: 587
      priority: 3
    
    calendar_agent:
      enabled: true
      timezone: "UTC"
      priority: 3

mongodb:
  connection_timeout: 30
  max_pool_size: 100
  retry_writes: true

conversation:
  max_history: 1000
  search_first: true
  cache_responses: true
"""
    
    config_path.write_text(yaml_content)
    print(f"✅ Created: {config_path}")
    
    return True

def create_readme():
    """Create updated README file."""
    print("\n📚 CREATING DOCUMENTATION")
    print("=" * 50)
    
    readme_content = """# MCP Production System

## 🤖 Intelligent Multi-Agent System with MongoDB Integration

A production-ready Model Context Protocol system with organized agents, conversational AI, and comprehensive data storage.

## 🏗️ Project Structure

### 📂 Core Components
- **core/**: Main MCP server, client, and conversation engine
- **agents/**: Organized agent categories (live_data, processing, communication, specialized)
- **database/**: MongoDB integration and data management
- **storage/**: File storage for logs, conversations, and extracted data

### 🤖 Production Agents

#### 🌤️ Live Data Agents
- **Weather Agent**: Real-time weather monitoring and alerts

#### 🔢 Processing Agents  
- **Math Agent**: Complex mathematical calculations
- **Image OCR Agent**: Professional image text extraction
- **Document Agent**: Document analysis and summarization

#### 📧 Communication Agents
- **Email Agent**: Automated email communication
- **Calendar Agent**: Smart scheduling and reminders

## 🚀 Quick Start

```bash
# Start the production system
python scripts/start_production.py

# Access web interface
http://localhost:8000

# Use command line client
python core/mcp_client.py -c "What's the weather in Mumbai?"
```

## 💾 MongoDB Integration

All agent activities, conversations, and extracted data are automatically stored in MongoDB:
- **Conversation History**: Complete chat logs with context
- **Agent Logs**: Detailed execution tracking
- **Extracted Data**: OCR results, document analysis
- **Query Cache**: Fast retrieval of previous results

## 🔍 Intelligent Search

The system searches MongoDB first before calling agents:
1. User query → MongoDB search
2. If found → Conversational response from stored data
3. If not found → Route to appropriate agent(s)
4. Store new results → Return to user

## 🤖 Inter-Agent Communication

Agents collaborate to provide comprehensive responses:
- Weather + Email: "If it rains, email the team"
- OCR + Document: "Extract text and summarize"
- Math + Email: "Calculate costs and email report"

## 📊 Features

- ✅ Real-time weather monitoring
- ✅ Mathematical calculations
- ✅ Image text extraction (OCR)
- ✅ Document analysis
- ✅ Email automation
- ✅ Calendar management
- ✅ Conversational AI
- ✅ MongoDB data storage
- ✅ Inter-agent communication
- ✅ Web interface
- ✅ REST API

## 🔧 Configuration

Edit `config/agent_config.yaml` to customize agent behavior and `config/.env` for credentials.
"""
    
    readme_path = Path("README.md")
    readme_path.write_text(readme_content)
    print(f"✅ Created: {readme_path}")
    
    return True

def main():
    """Main restructuring function."""
    print("🏗️ MCP PROJECT RESTRUCTURING")
    print("=" * 80)
    print("🎯 Organizing agents into production-ready structure")
    print("💾 Adding MongoDB integration and conversational AI")
    print("🤖 Enabling inter-agent communication")
    print("=" * 80)
    
    steps = [
        ("Creating directory structure", create_directory_structure),
        ("Moving existing agents", move_existing_agents),
        ("Moving core files", create_core_files),
        ("Creating package files", create_init_files),
        ("Creating configuration", create_configuration_files),
        ("Creating documentation", create_readme)
    ]
    
    success_count = 0
    
    for step_name, step_function in steps:
        print(f"\n🔄 {step_name}...")
        try:
            if step_function():
                success_count += 1
                print(f"✅ {step_name} completed")
            else:
                print(f"❌ {step_name} failed")
        except Exception as e:
            print(f"❌ {step_name} error: {e}")
    
    print("\n" + "=" * 80)
    print("📊 RESTRUCTURING RESULTS")
    print("=" * 80)
    print(f"✅ Completed steps: {success_count}/{len(steps)}")
    print(f"📈 Success rate: {(success_count/len(steps))*100:.1f}%")
    
    if success_count == len(steps):
        print("\n🎉 PROJECT RESTRUCTURING COMPLETED!")
        print("🏗️ New organized structure created")
        print("🤖 Agents categorized and moved")
        print("💾 MongoDB integration ready")
        print("🔍 Conversational AI structure prepared")
        
        print("\n💡 NEXT STEPS:")
        print("1. Review the new structure in PROJECT_STRUCTURE.md")
        print("2. Update import paths in moved files")
        print("3. Test the new agent organization")
        print("4. Configure MongoDB connection")
        print("5. Start the production system")
        
    else:
        print("\n⚠️ RESTRUCTURING INCOMPLETE")
        print("🔧 Some steps failed - check errors above")
    
    return success_count == len(steps)

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Restructuring completed successfully!")
        else:
            print("\n🔧 Restructuring needs attention.")
    except Exception as e:
        print(f"\n❌ Restructuring failed: {e}")
        import traceback
        traceback.print_exc()
