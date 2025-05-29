#!/usr/bin/env python3
"""
Activate Production Agents
Ensures all production agents are properly loaded and configured
"""

import os
import sys
import importlib.util
from pathlib import Path

def ensure_agent_registration():
    """Ensure all production agents are properly registered."""
    print("🔧 ACTIVATING PRODUCTION AGENTS")
    print("=" * 50)
    
    # Production agents that should be active
    production_agents = {
        "realtime_weather_agent": "agents/data/realtime_weather_agent.py",
        "math_agent": "agents/specialized/math_agent.py", 
        "calendar_agent": "agents/specialized/calendar_agent.py",
        "real_gmail_agent": "agents/communication/real_gmail_agent.py",
        "document_processor": "agents/core/document_processor.py"
    }
    
    print(f"🎯 Target production agents: {len(production_agents)}")
    print()
    
    activated_count = 0
    
    for agent_name, agent_path in production_agents.items():
        print(f"🔍 Checking {agent_name}...")
        
        # Check if file exists
        if Path(agent_path).exists():
            print(f"   ✅ File found: {agent_path}")
            
            # Try to import and validate
            try:
                spec = importlib.util.spec_from_file_location(agent_name, agent_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check if it has required functions
                if hasattr(module, 'create_agent') and hasattr(module, 'get_agent_info'):
                    print(f"   ✅ Agent structure valid")
                    
                    # Get agent info
                    agent_info = module.get_agent_info()
                    print(f"   📝 Description: {agent_info.get('description', 'No description')}")
                    
                    activated_count += 1
                    print(f"   🎉 {agent_name} ACTIVATED")
                    
                else:
                    print(f"   ❌ Missing required functions (create_agent, get_agent_info)")
                    
            except Exception as e:
                print(f"   ❌ Import error: {e}")
                
        else:
            print(f"   ❌ File not found: {agent_path}")
        
        print()
    
    print("=" * 50)
    print(f"📊 ACTIVATION SUMMARY:")
    print(f"✅ Activated agents: {activated_count}/{len(production_agents)}")
    print(f"📈 Success rate: {(activated_count/len(production_agents))*100:.1f}%")
    
    if activated_count == len(production_agents):
        print("\n🎉 ALL PRODUCTION AGENTS ACTIVATED!")
        print("🚀 Ready for full MCP functionality")
    else:
        missing = len(production_agents) - activated_count
        print(f"\n⚠️ {missing} agents need attention")
    
    return activated_count == len(production_agents)

def update_agent_init():
    """Update agents/__init__.py to ensure proper discovery."""
    print("\n🔧 UPDATING AGENT DISCOVERY")
    print("=" * 50)
    
    init_file = Path("agents/__init__.py")
    
    # Content for __init__.py
    init_content = '''"""
MCP Agents Package
Production agents for the Model Context Protocol system
"""

# Production agents auto-discovery
PRODUCTION_AGENTS = [
    "realtime_weather_agent",
    "math_agent", 
    "calendar_agent",
    "real_gmail_agent",
    "document_processor"
]

def get_production_agents():
    """Get list of production agent names."""
    return PRODUCTION_AGENTS

def is_production_agent(agent_name):
    """Check if an agent is a production agent."""
    return agent_name in PRODUCTION_AGENTS
'''
    
    try:
        with open(init_file, 'w') as f:
            f.write(init_content)
        
        print(f"✅ Updated {init_file}")
        print("📋 Production agents registered for auto-discovery")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {init_file}: {e}")
        return False

def clean_cache():
    """Clean Python cache files."""
    print("\n🧹 CLEANING CACHE FILES")
    print("=" * 50)
    
    cache_dirs = []
    
    # Find all __pycache__ directories
    for cache_dir in Path("agents").rglob("__pycache__"):
        cache_dirs.append(cache_dir)
    
    print(f"🔍 Found {len(cache_dirs)} cache directories")
    
    cleaned = 0
    for cache_dir in cache_dirs:
        try:
            import shutil
            shutil.rmtree(cache_dir)
            print(f"   ✅ Cleaned: {cache_dir}")
            cleaned += 1
        except Exception as e:
            print(f"   ❌ Error cleaning {cache_dir}: {e}")
    
    print(f"🧹 Cleaned {cleaned}/{len(cache_dirs)} cache directories")
    return cleaned == len(cache_dirs)

def verify_gmail_config():
    """Verify Gmail configuration."""
    print("\n📧 CHECKING GMAIL CONFIGURATION")
    print("=" * 50)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    gmail_email = os.getenv('GMAIL_EMAIL', '').strip()
    gmail_password = os.getenv('GMAIL_APP_PASSWORD', '').strip()
    
    if gmail_email and gmail_password:
        if gmail_email != 'your-email@gmail.com' and gmail_password != 'your-app-password':
            print(f"✅ Gmail email configured: {gmail_email}")
            print(f"✅ Gmail app password configured: {'*' * len(gmail_password)}")
            print("🎉 Gmail integration ready!")
            return True
        else:
            print("⚠️ Gmail credentials are placeholder values")
            print("🔧 Please update .env file with real Gmail credentials")
            return False
    else:
        print("❌ Gmail credentials not found in .env file")
        print("💡 Add GMAIL_EMAIL and GMAIL_APP_PASSWORD to .env")
        return False

def test_agent_loading():
    """Test if agents can be loaded by the system."""
    print("\n🧪 TESTING AGENT LOADING")
    print("=" * 50)
    
    try:
        # Import the agent loader
        sys.path.append('.')
        from agents.agent_loader import MCPAgentLoader
        
        # Create loader and load agents
        loader = MCPAgentLoader()
        loaded_agents = loader.load_all_agents()
        
        print(f"📊 Loaded agents: {len(loaded_agents)}")
        
        production_agents = ["realtime_weather_agent", "math_agent", "calendar_agent", "real_gmail_agent", "document_processor"]
        loaded_production = [name for name in production_agents if name in loaded_agents]
        
        print(f"🚀 Production agents loaded: {len(loaded_production)}/{len(production_agents)}")
        
        for agent_name in loaded_production:
            print(f"   ✅ {agent_name}")
        
        missing = [name for name in production_agents if name not in loaded_agents]
        for agent_name in missing:
            print(f"   ❌ {agent_name} (not loaded)")
        
        return len(loaded_production) == len(production_agents)
        
    except Exception as e:
        print(f"❌ Error testing agent loading: {e}")
        return False

def main():
    """Main activation function."""
    print("🚀 MCP PRODUCTION AGENT ACTIVATION")
    print("=" * 80)
    
    success_count = 0
    total_steps = 5
    
    # Step 1: Clean cache
    if clean_cache():
        success_count += 1
        print("✅ Step 1: Cache cleaned")
    else:
        print("❌ Step 1: Cache cleaning failed")
    
    # Step 2: Update agent discovery
    if update_agent_init():
        success_count += 1
        print("✅ Step 2: Agent discovery updated")
    else:
        print("❌ Step 2: Agent discovery update failed")
    
    # Step 3: Ensure agent registration
    if ensure_agent_registration():
        success_count += 1
        print("✅ Step 3: All agents registered")
    else:
        print("❌ Step 3: Some agents failed registration")
    
    # Step 4: Verify Gmail config
    if verify_gmail_config():
        success_count += 1
        print("✅ Step 4: Gmail configuration verified")
    else:
        print("⚠️ Step 4: Gmail configuration needs attention")
    
    # Step 5: Test agent loading
    if test_agent_loading():
        success_count += 1
        print("✅ Step 5: Agent loading test passed")
    else:
        print("❌ Step 5: Agent loading test failed")
    
    print("\n" + "=" * 80)
    print("📊 ACTIVATION RESULTS")
    print("=" * 80)
    print(f"✅ Successful steps: {success_count}/{total_steps}")
    print(f"📈 Success rate: {(success_count/total_steps)*100:.1f}%")
    
    if success_count == total_steps:
        print("\n🎉 PRODUCTION AGENTS FULLY ACTIVATED!")
        print("🚀 MCP system ready for production use")
        print("\n💡 NEXT STEPS:")
        print("   1. Start MCP server: python start_mcp.py")
        print("   2. Test commands: python mcp_client.py")
        print("   3. Use web interface: http://localhost:8000")
        
    elif success_count >= 3:
        print("\n🎯 MOSTLY SUCCESSFUL!")
        print("🔧 Minor issues need attention")
        print("💡 System should work with current configuration")
        
    else:
        print("\n⚠️ ACTIVATION INCOMPLETE")
        print("🔧 Several issues need to be resolved")
        print("💡 Check error messages above and fix issues")
    
    return success_count >= 3

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Activation completed successfully!")
        else:
            print("\n🔧 Activation needs attention. Check errors above.")
    except Exception as e:
        print(f"\n❌ Activation failed: {e}")
        sys.exit(1)
