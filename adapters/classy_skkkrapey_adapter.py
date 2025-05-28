from pathlib import Path
from typing import Dict, List, Any
import os

from .base_adapter import ScraperAdapter

class ClassySkkkrapeyAdapter(ScraperAdapter):
    """
    Adapter for the classy_skkkrapey.py multi-site scraper.
    """

    def __init__(self):
        # Assuming classy_skkkrapey.py is in the root of the repository
        super().__init__(scraper_name="classy_skkkrapey", script_path="classy_skkkrapey.py")

    def run_scraper(self, action: str, params: Dict[str, Any], temp_output_dir: Path, local_http_server_url: str) -> Dict[str, Any]:
        if action == "help":
            command = ["python3", str(self.script_path.resolve()), "--help"]
            repo_root = self.script_path.parent
            result = self._execute_command(command, cwd=str(repo_root))
            result["output_files"] = []
            return result

        if action not in ["scrape", "crawl"]:
            return {
                "stdout": "", "stderr": f"Action '{action}' not supported by {self.scraper_name}. Only 'scrape', 'crawl', or 'help' is supported.",
                "exit_code": -1, "output_files": [], "success": False
            }
        # ... (rest of the existing scrape/crawl logic) ...
        command = ["python3", str(self.script_path.resolve())]

        target_url = params.get("url")
        if not target_url:
            return {
                "stdout": "", "stderr": "Missing 'url' in params for scrape/crawl action.", "exit_code": -1, "output_files": [], "success": False
            }

        if params.get("target_url_is_local_file", False):
            file_path = Path(target_url)
            command.extend([f"{local_http_server_url.rstrip('/')}/{file_path.name}"])
        else:
            command.extend([target_url])
            
        command.append(action) # "scrape" or "crawl"

        if params.get("headless", True) is False:
            command.append("--no-headless")
        else:
            # classy_skkkrapey.py defaults to headless if --no-headless is not present,
            # but it also has a --headless argument. To be explicit for testing:
            command.append("--headless")


        # classy_skkkrapey.py uses --output_dir
        command.extend(["--output_dir", str(temp_output_dir.resolve())])
        
        # For classy_skkkrapey.py, CWD should be the repository root.
        repo_root = self.script_path.parent 
        result = self._execute_command(command, cwd=str(repo_root))

        output_files = []
        if result["success"]:
            # Find generated files (JSON and Markdown)
            # The script names them like: events_HOSTNAME_TIMESTAMP.json/md or events_HOSTNAME_ACTION_TIMESTAMP.json/md
            # For testing, we assume only one set of files will be generated per run in the temp_output_dir.
            for extension in [".json", ".md"]:
                # Search for files matching the pattern
                # Since timestamp makes it hard, we just list files with the extension.
                # This assumes the temp_output_dir is clean for each specific test run of this adapter.
                found = list(temp_output_dir.glob(f"events_*{extension}"))
                if found:
                    output_files.extend(found)
            
            if not output_files:
                # This can happen if the scraper ran successfully but didn't find/process any events (e.g. crawl found no links)
                # Or if the output naming convention changed or was not matched by the glob.
                # Check stderr for clues if this is unexpected.
                pass


        result["output_files"] = output_files
        return result

    def get_capabilities(self) -> List[str]:
        """
        Returns capabilities for classy_skkkrapey.py.
        """
        return [
            "scrape_single_url",
            "crawl_listing",
            "uses_playwright", # It uses Playwright for IbizaSpotlightScraper
            "outputs_json",
            "outputs_markdown",
            "handles_ticketsibiza", # Based on its internal factory
            "handles_ibiza_spotlight" # Based on its internal factory
        ]
