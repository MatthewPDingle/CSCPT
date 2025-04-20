"""
Stub module to allow mocking of openai SDK in tests.
"""
class OpenAI:
    """Stub for openai client"""
    def __init__(self, api_key: str, organization: str = None):
        self.api_key = api_key
        self.organization = organization
    # responses attribute stub for new Responses API
    class responses:
        @staticmethod
        def create(*args, **kwargs):
            return None
    # chat attribute stub for older Completions API
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                return None