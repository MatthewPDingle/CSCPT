"""
Stub module to allow mocking of anthropic SDK in tests.
"""
class Anthropic:
    """Stub for anthropic client"""
    def __init__(self, api_key: str):
        self.api_key = api_key
    # messages attribute stub
    class messages:
        @staticmethod
        def create(*args, **kwargs):
            return None