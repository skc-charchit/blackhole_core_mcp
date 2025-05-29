#!/usr/bin/env python3
"""
Complete Agent Inventory
Comprehensive list of all available agents in your MCP system
"""

import os
from pathlib import Path
from typing import Dict, List, Any

def get_complete_agent_inventory() -> Dict[str, Any]:
    """Get complete inventory of all agents in the system."""
    
    inventory = {
        "production_agents": {
            "🌤️ Live Data Agents": {
                "realtime_weather_agent": {
                    "path": "agents/data/realtime_weather_agent.py",
                    "status": "✅ Active",
                    "capabilities": ["live_weather", "api_integration", "location_parsing"],
                    "description": "Real-time weather data from OpenWeatherMap API",
                    "priority": 1,
                    "integration_ready": True
                },
                "live_data_agent": {
                    "path": "agents/live_data/live_data_agent.js",
                    "status": "🔧 Available",
                    "capabilities": ["live_data_fetching", "api_calls", "data_processing"],
                    "description": "General live data fetching agent",
                    "priority": 3,
                    "integration_ready": True
                }
            },
            
            "🔢 Processing Agents": {
                "math_agent": {
                    "path": "agents/specialized/math_agent.py",
                    "status": "✅ Active",
                    "capabilities": ["calculations", "mathematical_analysis", "formulas"],
                    "description": "Mathematical calculations and analysis",
                    "priority": 1,
                    "integration_ready": True
                },
                "document_processor": {
                    "path": "agents/core/document_processor.py",
                    "status": "✅ Active",
                    "capabilities": ["document_analysis", "text_extraction", "summarization"],
                    "description": "Document analysis and processing",
                    "priority": 1,
                    "integration_ready": True
                },
                "image_ocr_agent": {
                    "path": "agents/image/image_ocr_agent.js",
                    "status": "🔧 Available",
                    "capabilities": ["text_extraction", "image_processing", "ocr"],
                    "description": "Image text extraction using OCR",
                    "priority": 2,
                    "integration_ready": True
                },
                "pdf_extractor_agent": {
                    "path": "agents/pdf/pdf_extractor_agent.js",
                    "status": "🔧 Available",
                    "capabilities": ["pdf_processing", "text_extraction", "metadata"],
                    "description": "PDF text extraction and processing",
                    "priority": 2,
                    "integration_ready": True
                }
            },
            
            "📧 Communication Agents": {
                "real_gmail_agent": {
                    "path": "agents/communication/real_gmail_agent.py",
                    "status": "✅ Active",
                    "capabilities": ["email_sending", "gmail_integration", "smtp"],
                    "description": "Real Gmail integration for email automation",
                    "priority": 1,
                    "integration_ready": True
                },
                "gmail_agent": {
                    "path": "agents/specialized/gmail_agent.py",
                    "status": "🔧 Available",
                    "capabilities": ["email_sending", "notifications", "communication"],
                    "description": "General Gmail agent",
                    "priority": 2,
                    "integration_ready": True
                }
            },
            
            "📅 Scheduling Agents": {
                "calendar_agent": {
                    "path": "agents/specialized/calendar_agent.py",
                    "status": "✅ Active",
                    "capabilities": ["scheduling", "reminders", "time_management"],
                    "description": "Calendar management and scheduling",
                    "priority": 1,
                    "integration_ready": True
                }
            },
            
            "🔍 Search & Data Agents": {
                "search_agent": {
                    "path": "agents/search/search_agent.js",
                    "status": "🔧 Available",
                    "capabilities": ["search", "data_retrieval", "indexing"],
                    "description": "Search and data retrieval agent",
                    "priority": 2,
                    "integration_ready": True
                },
                "archive_search_agent": {
                    "path": "blackhole_core/agents/archive_search_agent.py",
                    "status": "🔧 Available",
                    "capabilities": ["archive_search", "historical_data", "document_search"],
                    "description": "Archive and historical data search",
                    "priority": 3,
                    "integration_ready": True
                }
            }
        },
        
        "blackhole_core_agents": {
            "🧠 Core Intelligence Agents": {
                "document_processor_agent": {
                    "path": "blackhole_core/agents/document_processor_agent.py",
                    "status": "🔧 Available",
                    "capabilities": ["document_processing", "analysis", "blackhole_integration"],
                    "description": "BlackHole core document processor",
                    "priority": 2,
                    "integration_ready": True
                },
                "live_data_agent": {
                    "path": "blackhole_core/agents/live_data_agent.py",
                    "status": "🔧 Available",
                    "capabilities": ["live_data", "real_time_processing", "blackhole_integration"],
                    "description": "BlackHole core live data agent",
                    "priority": 2,
                    "integration_ready": True
                },
                "archive_search_agent": {
                    "path": "blackhole_core/agents/archive_search_agent.py",
                    "status": "🔧 Available",
                    "capabilities": ["archive_search", "blackhole_perspective", "data_mining"],
                    "description": "BlackHole core archive search agent",
                    "priority": 2,
                    "integration_ready": True
                }
            }
        },
        
        "template_agents": {
            "🛠️ Development Templates": {
                "research_agent": {
                    "path": "agent_configs/research_agent.json",
                    "status": "📋 Template",
                    "capabilities": ["research", "information_gathering", "analysis"],
                    "description": "Research and investigation template",
                    "priority": 4,
                    "integration_ready": False
                },
                "summary_agent": {
                    "path": "agent_configs/summary_agent.json",
                    "status": "📋 Template",
                    "capabilities": ["summarization", "key_points", "insights"],
                    "description": "Summary and insight generation template",
                    "priority": 4,
                    "integration_ready": False
                },
                "validation_agent": {
                    "path": "agent_configs/validation_agent.json",
                    "status": "📋 Template",
                    "capabilities": ["validation", "verification", "quality_assurance"],
                    "description": "Data validation and verification template",
                    "priority": 4,
                    "integration_ready": False
                }
            }
        },
        
        "database_agents": {
            "💾 Database Integration": {
                "mongodb_connection": {
                    "path": "agents/db/mongodb_connection.js",
                    "status": "🔧 Available",
                    "capabilities": ["database_connection", "mongodb", "data_storage"],
                    "description": "MongoDB connection and operations",
                    "priority": 2,
                    "integration_ready": True
                },
                "mongodb_schema": {
                    "path": "agents/db/mongodb_schema.js",
                    "status": "🔧 Available",
                    "capabilities": ["schema_management", "data_modeling", "mongodb"],
                    "description": "MongoDB schema management",
                    "priority": 3,
                    "integration_ready": True
                }
            }
        }
    }
    
    return inventory

def print_agent_inventory():
    """Print formatted agent inventory."""
    inventory = get_complete_agent_inventory()
    
    print("📊 COMPLETE AGENT INVENTORY")
    print("=" * 80)
    print("🎯 All available agents in your MCP system")
    print("=" * 80)
    
    total_agents = 0
    active_agents = 0
    integration_ready = 0
    
    for category_name, category in inventory.items():
        print(f"\n📂 {category_name.upper().replace('_', ' ')}")
        print("-" * 60)
        
        for subcategory_name, agents in category.items():
            print(f"\n{subcategory_name}")
            
            for agent_name, agent_info in agents.items():
                total_agents += 1
                
                status = agent_info["status"]
                if "✅" in status:
                    active_agents += 1
                
                if agent_info["integration_ready"]:
                    integration_ready += 1
                
                print(f"   • {agent_name}")
                print(f"     Status: {status}")
                print(f"     Path: {agent_info['path']}")
                print(f"     Description: {agent_info['description']}")
                print(f"     Capabilities: {', '.join(agent_info['capabilities'])}")
                print(f"     Priority: {agent_info['priority']}")
                print(f"     Integration Ready: {'✅' if agent_info['integration_ready'] else '❌'}")
                print()
    
    print("=" * 80)
    print("📈 INVENTORY SUMMARY")
    print("=" * 80)
    print(f"📊 Total Agents: {total_agents}")
    print(f"✅ Active Agents: {active_agents}")
    print(f"🔧 Available Agents: {total_agents - active_agents}")
    print(f"🔗 Integration Ready: {integration_ready}")
    print(f"📈 Integration Rate: {(integration_ready/total_agents)*100:.1f}%")
    
    return inventory

def get_recommended_agents():
    """Get recommended agents for integration."""
    inventory = get_complete_agent_inventory()
    
    recommended = {
        "high_priority": [],
        "medium_priority": [],
        "low_priority": []
    }
    
    for category in inventory.values():
        for subcategory in category.values():
            for agent_name, agent_info in subcategory.items():
                if agent_info["integration_ready"]:
                    priority = agent_info["priority"]
                    
                    agent_entry = {
                        "name": agent_name,
                        "path": agent_info["path"],
                        "status": agent_info["status"],
                        "capabilities": agent_info["capabilities"],
                        "description": agent_info["description"]
                    }
                    
                    if priority == 1:
                        recommended["high_priority"].append(agent_entry)
                    elif priority == 2:
                        recommended["medium_priority"].append(agent_entry)
                    else:
                        recommended["low_priority"].append(agent_entry)
    
    return recommended

def print_integration_recommendations():
    """Print integration recommendations."""
    recommended = get_recommended_agents()
    
    print("\n🎯 INTEGRATION RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n🔥 HIGH PRIORITY (Integrate First):")
    for agent in recommended["high_priority"]:
        print(f"   ✅ {agent['name']}")
        print(f"      {agent['description']}")
        print(f"      Status: {agent['status']}")
        print()
    
    print("\n⚡ MEDIUM PRIORITY (Integrate Second):")
    for agent in recommended["medium_priority"]:
        print(f"   🔧 {agent['name']}")
        print(f"      {agent['description']}")
        print(f"      Status: {agent['status']}")
        print()
    
    print("\n📋 LOW PRIORITY (Optional):")
    for agent in recommended["low_priority"]:
        print(f"   📝 {agent['name']}")
        print(f"      {agent['description']}")
        print(f"      Status: {agent['status']}")
        print()

if __name__ == "__main__":
    print_agent_inventory()
    print_integration_recommendations()
