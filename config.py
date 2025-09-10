import os

BASE_URL = "https://www.coursera.org/api/"
GRAPHQL_URL = "https://www.coursera.org/graphql-gateway"

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "sonar-pro"

HEADERS = {
    "user-agent": "Mozilla/5.0",
    "x-coursera-application": "ondemand",
    "x-coursera-version": "3bfd497de04ae0fef167b747fd85a6fbc8fb55df",
    "x-requested-with": "XMLHttpRequest",
}

# Cookies and API key now come from environment variables
# Streamlit will set them dynamically before running
COOKIES = os.getenv("SKIPERA_COOKIES", "{}")  # JSON string
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
