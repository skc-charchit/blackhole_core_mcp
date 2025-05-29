#!/usr/bin/env python3
"""
Check Current Agents in MCP System
"""

import requests
import os
from pathlib import Path

def check_loaded_agents():
    """Check agents loaded by the MCP server."""
    try:
        response = requests.get("http://localhost:8000/api/mcp/agents", timeout=5)
        if response.status_code == 200:
            result = response.json()
            agents = result.get("agents", {})
            
            print("🤖 AGENTS LOADED BY MCP SERVER:")
            print("=" * 50)
            print(f"📊 Total Loaded Agents: {len(agents)}")
            print()
            
            for i, (name, info) in enumerate(agents.items(), 1):
                print(f"{i}. 🔧 {name}")
                print(f"   📝 Description: {info.get('description', 'No description')}")
                print(f"   🏷️ Category: {info.get('category', 'unknown')}")
                print(f"   ⚡ Capabilities: {', '.join(info.get('capabilities', []))}")
                print()
            
            return agents
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return {}
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to MCP server. Is it running?")
        return {}
    except Exception as e:
        print(f"❌ Error checking loaded agents: {e}")
        return {}

def check_agent_files():
    """Check agent files in the filesystem."""
    print("\n📁 AGENT FILES IN FILESYSTEM:")
    print("=" * 50)
    
    agents_dir = Path("agents")
    if not agents_dir.exists():
        print("❌ Agents directory not found")
        return []
    
    agent_files = []
    
    # Python agent files
    python_agents = list(agents_dir.rglob("*.py"))
    python_agents = [f for f in python_agents if f.name not in ["__init__.py", "base_agent.py", "agent_loader.py"]]
    
    # JavaScript agent files
    js_agents = list(agents_dir.rglob("*.js"))
    
    print("🐍 PYTHON AGENTS:")
    for i, agent_file in enumerate(python_agents, 1):
        relative_path = agent_file.relative_to(agents_dir)
        print(f"  {i}. {relative_path}")
        agent_files.append(str(relative_path))
    
    print(f"\n📊 Total Python Agents: {len(python_agents)}")
    
    print("\n🟨 JAVASCRIPT AGENTS:")
    for i, agent_file in enumerate(js_agents, 1):
        relative_path = agent_file.relative_to(agents_dir)
        print(f"  {i}. {relative_path}")
        agent_files.append(str(relative_path))
    
    print(f"\n📊 Total JavaScript Agents: {len(js_agents)}")
    print(f"📊 Total Agent Files: {len(agent_files)}")
    
    return agent_files

def categorize_agents():
    """Categorize agents by functionality."""
    print("\n🏷️ AGENT CATEGORIZATION:")
    print("=" * 50)
    
    categories = {
        "🌤️ Weather & Data": [
            "realtime_weather_agent.py"
        ],
        "📧 Communication": [
            "real_gmail_agent.py",
            "gmail_agent.py"
        ],
        "🔢 Mathematical": [
            "math_agent.py"
        ],
        "📅 Calendar & Scheduling": [
            "calendar_agent.py"
        ],
        "📄 Document Processing": [
            "document_processor.py"
        ],
        "💾 Database": [
            "mongodb_connection.js",
            "mongodb_schema.js"
        ],
        "🖼️ Image Processing": [
            "image_ocr_agent.js"
        ],
        "📑 PDF Processing": [
            "pdf_extractor_agent.js"
        ],
        "🔍 Search & Data": [
            "search_agent.js",
            "live_data_agent.js"
        ],
        "🛠️ Templates & Utils": [
            "simple_agent_template.py",
            "agent_manager.js"
        ]
    }
    
    total_categorized = 0
    
    for category, agents in categories.items():
        print(f"\n{category}:")
        existing_agents = []
        
        for agent in agents:
            agent_path = Path("agents") / agent
            if agent_path.exists():
                existing_agents.append(agent)
                print(f"  ✅ {agent}")
            else:
                # Check if it exists in subdirectories
                found = False
                for found_path in Path("agents").rglob(agent):
                    existing_agents.append(str(found_path.relative_to(Path("agents"))))
                    print(f"  ✅ {found_path.relative_to(Path('agents'))}")
                    found = True
                    break
                
                if not found:
                    print(f"  ❌ {agent} (not found)")
        
        total_categorized += len(existing_agents)
        print(f"  📊 Count: {len(existing_agents)}")
    
    print(f"\n📊 TOTAL CATEGORIZED AGENTS: {total_categorized}")

def show_agent_capabilities():
    """Show capabilities of each agent type."""
    print("\n⚡ AGENT CAPABILITIES:")
    print("=" * 50)
    
    capabilities = {
        "🌤️ Real-Time Weather Agent": [
            "Live weather data from OpenWeatherMap API",
            "Global city support",
            "Natural language weather queries",
            "Weather condition monitoring for conditional logic"
        ],
        "🔢 Math Agent": [
            "Mathematical calculations and expressions",
            "Word problem solving",
            "Percentage calculations",
            "Area and geometry calculations",
            "Natural language math queries"
        ],
        "📅 Calendar Agent": [
            "Reminder creation and management",
            "Event scheduling",
            "Natural language time parsing",
            "Calendar integration"
        ],
        "📧 Gmail Agent": [
            "Email sending via Gmail SMTP",
            "Professional email templates",
            "Automated email generation",
            "Workflow-based email automation"
        ],
        "📄 Document Processor": [
            "PDF text extraction",
            "Document analysis",
            "Key point extraction",
            "Summary generation"
        ]
    }
    
    for agent, caps in capabilities.items():
        print(f"\n{agent}:")
        for cap in caps:
            print(f"  • {cap}")

def main():
    """Main function."""
    print("🔍 MCP AGENT INVENTORY CHECK")
    print("=" * 80)
    
    # Check loaded agents
    loaded_agents = check_loaded_agents()
    
    # Check agent files
    agent_files = check_agent_files()
    
    # Categorize agents
    categorize_agents()
    
    # Show capabilities
    show_agent_capabilities()
    
    # Summary
    print("\n📊 FINAL SUMMARY:")
    print("=" * 50)
    print(f"🤖 Agents loaded by server: {len(loaded_agents)}")
    print(f"📁 Agent files in filesystem: {len(agent_files)}")
    
    # Production agents count
    production_agents = [
        "realtime_weather_agent",
        "math_agent", 
        "calendar_agent",
        "real_gmail_agent",
        "document_processor"
    ]
    
    active_production = [name for name in production_agents if name in loaded_agents]
    
    print(f"🚀 Production agents active: {len(active_production)}/{len(production_agents)}")
    print(f"✅ Production agents: {', '.join(active_production)}")
    
    if len(active_production) == len(production_agents):
        print("\n🎉 ALL PRODUCTION AGENTS ARE ACTIVE!")
    else:
        missing = [name for name in production_agents if name not in loaded_agents]
        print(f"\n⚠️ Missing production agents: {', '.join(missing)}")

if __name__ == "__main__":
    main()
