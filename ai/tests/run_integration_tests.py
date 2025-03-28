"""
Integration test runner for AI providers.
This runs real API calls against all providers instead of using mocks.
"""

import os
import sys
import asyncio
import importlib.util
from dotenv import load_dotenv

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables
load_dotenv()

# We'll use the example scripts directly as they test actual API calls
async def run_all_provider_tests():
    """Run all provider integration tests"""
    print("Running integration tests with real API calls for all providers...")
    
    # Check if the example scripts exist and run them
    examples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
    
    # Anthropic tests
    anthropic_path = os.path.join(examples_dir, "anthropic_model_test.py")
    if os.path.exists(anthropic_path) and os.environ.get("ANTHROPIC_API_KEY"):
        print("\n=== Running Anthropic Provider Tests ===")
        spec = importlib.util.spec_from_file_location("anthropic_test", anthropic_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        await module.main()
    else:
        print("\n⚠️ Skipping Anthropic tests - API key not set or test file missing")
    
    # OpenAI tests
    openai_path = os.path.join(examples_dir, "openai_model_test.py")
    if os.path.exists(openai_path) and os.environ.get("OPENAI_API_KEY"):
        print("\n=== Running OpenAI Provider Tests ===")
        spec = importlib.util.spec_from_file_location("openai_test", openai_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        await module.main()
    else:
        print("\n⚠️ Skipping OpenAI tests - API key not set or test file missing")
    
    # Gemini tests
    gemini_path = os.path.join(examples_dir, "gemini_model_test.py")
    if os.path.exists(gemini_path) and os.environ.get("GEMINI_API_KEY"):
        print("\n=== Running Gemini Provider Tests ===")
        spec = importlib.util.spec_from_file_location("gemini_test", gemini_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        await module.main()
    else:
        print("\n⚠️ Skipping Gemini tests - API key not set or test file missing")
    
    print("\n=== Integration Tests Completed ===")

if __name__ == "__main__":
    asyncio.run(run_all_provider_tests())