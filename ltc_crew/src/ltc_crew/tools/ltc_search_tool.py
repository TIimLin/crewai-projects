from crewai.tools import BaseTool
import os
import requests

# It's recommended to set the Serper API key as an environment variable
# os.environ["SERPER_API_KEY"] = "Your Key"

class TaiwanLTCProviderSearchTool(BaseTool):
    name: str = "Taiwan Long-Term Care Provider Search Tool"
    description: str = (
        "A specialized tool to search for long-term care institutions in a specific administrative district in Taiwan. "
        "Input should be a string containing the institution type and the district, for example: '台北市內湖區 護理之家'."
    )

    def _run(self, query: str) -> str:
        """
        Uses the Serper API to perform a targeted search for long-term care providers in Taiwan.
        Prioritizes government websites for higher information reliability.
        """
        # Construct a query that prioritizes government websites
        # .gov.tw is the top-level domain for Taiwanese government sites
        search_query = f"site:.gov.tw {query}"
        
        url = "https://google.serper.dev/search"
        payload = {"q": search_query}
        headers = {
            'X-API-KEY': os.environ.get("SERPER_API_KEY"),
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for bad requests
            search_results = response.json()

            if "organic" in search_results and search_results["organic"]:
                # Extract and format the results
                output = f"Search results for '{query}':\n\n"
                for result in search_results["organic"][:5]: # Get top 5 results
                    output += f"Title: {result.get('title', 'N/A')}\n"
                    output += f"Link: {result.get('link', 'N/A')}\n"
                    output += f"Snippet: {result.get('snippet', 'N/A')}\n---\n"
                return output
            else:
                return f"No relevant government or official results found for '{query}'. Consider a broader search."
        except requests.exceptions.RequestException as e:
            return f"An error occurred during the search: {e}" 