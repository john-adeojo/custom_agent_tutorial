import requests
from bs4 import BeautifulSoup
import json
import yaml
from termcolor import colored
import os

def load_config(file_path):
    """
    Load a configuration file and set environment variables based on its contents.

    Args:
        file_path (str): The path to the configuration file.

    Returns:
        None

    Raises:
        FileNotFoundError: If the specified file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML file.

    This function reads the contents of a YAML configuration file and sets environment variables based on its contents.
    The file should be a dictionary where each key-value pair represents an environment variable name and its value.
    The function uses the `yaml` module to parse the YAML file and the `os` module to set the environment variables.
    """
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
        for key, value in config.items():
            os.environ[key] = value

class WebSearcher:

    """
    A class that encapsulates methods for generating search queries, fetching search results,
    determining the best search pages, and scraping web content using the OpenAI API and other web services.

    This class is designed to interact with the OpenAI API to leverage its capabilities for generating
    search queries based on a provided plan and query. It integrates with the serper.dev API to fetch
    search results and then uses a combination of these results and additional OpenAI API calls to determine
    the most relevant web pages. Finally, it scrapes the content of the determined best page.

    Methods:
        __init__(self): Initializes the WebSearcher instance, loads API keys from a configuration file,
                       and sets up headers for HTTP requests.
        generate_searches(self, plan: str, query: str) -> str: Generates search queries based on provided plan and query.
        get_search_page(self, search_results: str, plan: str, query: str) -> str: Determines the best search page URLs
                                                                               based on the results and context.
        format_results(self, organic_results: list) -> str: Formats the search results to a more readable format.
        fetch_search_results(self, search_queries: str) -> str: Fetches detailed search results from serper.dev API.
        scrape_website_content(self, website_url: str) -> dict: Scrapes and returns the content of the given website URL.
        use_tool(self, verbose: bool = False, plan: str = None, query: str = None) -> dict: Orchestrates the use of other methods
                                                                                          to perform a complete search-and-retrieve
                                                                                          operation based on the specified plan and query.

    Usage Example:
        searcher = WebSearcher()
        results_dict = searcher.use_tool(verbose=True, plan="Research new AI techniques", query="Latest trends in AI")
        results_dict will contain the URL as a key and the scraped content from that URL as the value.
    """
    def __init__(self, model, verbose=False):
        """
        Initializes the WebSearcher instance with the provided model and verbosity level.
        
        :param model: The model to use for generating search queries and fetching search results.
        :type model: str
        :param verbose: Whether to print additional information during the search process. Defaults to False.
        :type verbose: bool
        :return: None
        """
        load_config('config.yaml')
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.url = 'https://api.openai.com/v1/chat/completions'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        self.model = model
        self.verbose = verbose

    def generate_searches(self, plan, query):
        """
        Generates search queries based on the provided plan and query.

        :param plan: The plan for which search queries need to be generated.
        :type plan: str
        :param query: The query for which search queries need to be generated.
        :type query: str
        :return: The generated search queries.
        :rtype: str
        """

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "fetch_search_results",
                    "description": "Fetch search results based on the search query",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_engine_queries": {
                                "type": "string",
                                "description": "The most suitable search query for the plan"
                            },
                        },
                        "required": ["search_engine_queries"]
                    }
                }
            }
        ]

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": f"Query:{query}\n\n Plan:{plan}"}],
            "temperature": 0,
            "tools": tools,
            "tool_choice": "required"
        }

        json_data = json.dumps(data)
        response = requests.post(self.url, headers=self.headers, data=json_data)
        response_dict = response.json()

        tool_calls = response_dict['choices'][0]['message']['tool_calls'][0]
        arguments_json = json.loads(tool_calls['function']['arguments'])
        search_queries = arguments_json['search_engine_queries']
        print(colored(f"Search Engine Queries:, {search_queries}", 'yellow'))

        return search_queries
    
    def get_search_page(self, search_results, plan, query):
        """
        Get the best search page based on the search results, plan, and query.

        :param search_results: The search results to consider.
        :type search_results: str
        :param plan: The plan for which search queries need to be generated.
        :type plan: str
        :param query: The query for which search queries need to be generated.
        :type query: str
        :return: The URL link of the best search page based on the search results, plan, and query.
                 Do not select pdf files.
        :rtype: str
        """

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "decide_best_pages",
                    "description": "Decide the best pages to visit based on the search results",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "best_search_page": {
                                "type": "string",
                                "description": "The URL link of best search page based on the Search Results, Plan and Query. Do not select pdf files."
                            },
                        },
                        "required": ["best_search_page"]
                    }
                }
            }
        ]

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": f"Query:{query}\n\n Plan:{plan} \n\n Search Results:{search_results}"}],
            "temperature": 0,
            "tools": tools,
            "tool_choice": "required"
        }

        json_data = json.dumps(data)
        response = requests.post(self.url, headers=self.headers, data=json_data)
        response_dict = response.json()

        tool_calls = response_dict['choices'][0]['message']['tool_calls'][0]
        arguments_json = json.loads(tool_calls['function']['arguments'])
        search_queries = arguments_json['best_search_page']
        print(colored(f"Best Pages:, {search_queries}", 'yellow'))

        return search_queries
    
    def format_results(self, organic_results):
        """
        Formats the given organic search results into a list of strings, each representing a search result.

        Args:
            organic_results (list): A list of dictionaries, where each dictionary represents an organic search result.
                Each dictionary should have the following keys: 'title', 'link', and 'snippet'.

        Returns:
            str: A string containing the formatted search results. Each search result is represented by a block of text
                with the following format: "Title: {title}\nLink: {link}\nSnippet: {snippet}\n---".

        Note:
            If a search result does not have a 'title', 'link', or 'snippet', the corresponding field will be replaced
            with the default value 'No Title', '#', and 'No snippet available.' respectively.
        """

        result_strings = []
        for result in organic_results:
            title = result.get('title', 'No Title')
            link = result.get('link', '#')
            snippet = result.get('snippet', 'No snippet available.')
            result_strings.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n---")
        
        return '\n'.join(result_strings)
    
    def fetch_search_results(self, search_queries: str):
        """
        Fetches search results from the serper.dev API based on the given search queries.

        Args:
            search_queries (str): A string of search queries separated by spaces.

        Returns:
            str or list: If 'organic' results are found in the response, returns the formatted organic results.
                         If no 'organic' results are found, returns a string indicating no organic results were found.
                         If an HTTP error or request exception occurs, returns a string indicating the error.
                         If a key error occurs in handling the response, returns a string indicating the error.

        Raises:
            requests.exceptions.HTTPError: If a bad HTTP response (4XX, 5XX) is received.
            requests.exceptions.RequestException: If an exception occurs during the request.
            KeyError: If a key error occurs in handling the response.

        """

        search_url = "https://google.serper.dev/search"
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': os.environ['SERPER_DEV_API_KEY']  # Ensure this environment variable is set with your API key
        }
        payload = json.dumps({"q": search_queries})
        
        # Attempt to make the HTTP POST request
        try:
            response = requests.post(search_url, headers=headers, data=payload)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4XX, 5XX)
            results = response.json()
            
            # Check if 'organic' results are in the response
            if 'organic' in results:
                return self.format_results(results['organic'])
            else:
                return "No organic results found."

        except requests.exceptions.HTTPError as http_err:
            return f"HTTP error occurred: {http_err}"
        except requests.exceptions.RequestException as req_err:
            return f"Request exception occurred: {req_err}"
        except KeyError as key_err:
            return f"Key error in handling response: {key_err}"
        
    def scrape_website_content(self, website_url):
        """
        Scrapes the content of a given website URL.

        Args:
            website_url (str): The URL of the website to scrape.

        Returns:
            dict: A dictionary containing the URL of the website as the key and the scraped content as the value.

        Raises:
            requests.exceptions.RequestException: If an exception occurs during the request.

        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        
        try:
            # Making a GET request to the website
            response = requests.get(website_url, headers=headers, timeout=15)
            response.raise_for_status()  # This will raise an exception for HTTP errors

            # Parsing the page content using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text(separator='\n')
            # Cleaning up the text: removing excess whitespace
            clean_text = '\n'.join([line.strip() for line in text.splitlines() if line.strip()])

            return {website_url: clean_text}

        except requests.exceptions.RequestException as e:
            print(f"Error retrieving content from {website_url}: {e}")
            return {website_url: f"Failed to retrieve content due to an error: {e}"}
    
    def use_tool(self, plan=None, query=None):
        """
        Executes a search tool to retrieve website content based on a given plan and query.

        Args:
            plan (str, optional): The plan for which search queries need to be generated. Defaults to None.
            query (str, optional): The query for which search queries need to be generated. Defaults to None.

        Returns:
            dict: A dictionary containing the URL of the best search page as the key and the scraped content as the value.
        """

        search = WebSearcher(self.model)
        # plan = "Find the best way to cook a turkey"
        # query = "How long should I cook a turkey for?"

        search_queries = search.generate_searches(plan, query)
        search_results = search.fetch_search_results(search_queries)
        best_page = search.get_search_page(search_results, plan, query)
        results_dict = search.scrape_website_content(best_page)

        if self.verbose:
            print(colored(f"SEARCH RESULTS {search_results}", 'yellow'))
            print(colored(f"RESULTS DICT {results_dict}", 'yellow'))

        return results_dict
        

if __name__ == '__main__':

    search = WebSearcher()
    search.use_tool()