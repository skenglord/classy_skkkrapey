import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any

class ScraperAdapter(ABC):
    """
    Abstract Base Class for scraper-specific adapters.
    Defines the interface for the testing tool to interact with different scrapers.
    """

    def __init__(self, scraper_name: str, script_path: str):
        self.scraper_name = scraper_name
        # Resolve the script path relative to a potential root directory if necessary,
        # or assume it's directly runnable. For now, let's assume it's a path
        # that subprocess can use.
        self.script_path = Path(script_path)

    def setup_test_environment(self, test_data_path: Path, temp_output_dir: Path) -> None:
        """
        Prepare anything needed before a test run (e.g., copy specific test files).
        Default implementation does nothing.
        """
        pass

    @abstractmethod
    def run_scraper(self, action: str, params: Dict[str, Any], temp_output_dir: Path, local_http_server_url: str) -> Dict[str, Any]:
        """
        Executes the scraper script with the given action and parameters.

        Args:
            action (str): The action for the scraper (e.g., "scrape", "crawl", "help").
            params (Dict[str, Any]): Dictionary of parameters for the scraper,
                                     e.g., {"url": "...", "output_format": "json"}.
            temp_output_dir (Path): A temporary directory for the scraper to write its output files.
            local_http_server_url (str): The base URL of the local HTTP server for test files.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - "stdout": Standard output string.
                - "stderr": Standard error string.
                - "exit_code": Exit code of the script.
                - "output_files": A list of Paths to generated output files in temp_output_dir.
                - "success": A boolean indicating if the run was generally successful (e.g., exit code 0)
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Returns a list of capabilities for this scraper.
        e.g., ["scrape_single_url", "crawl_listing", "outputs_json", "uses_playwright"]
        """
        pass

    def cleanup_test_environment(self, temp_output_dir: Path) -> None:
        """
        Clean up after a test run (e.g., remove temporary files if not handled by temp dir itself).
        Default implementation does nothing.
        """
        pass

    def _execute_command(self, command: List[str], cwd: str = None) -> Dict[str, Any]:
        """
        Helper method to run a command using subprocess.
        """
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd or str(self.script_path.parent) # Default CWD to script's directory
            )
            stdout, stderr = process.communicate(timeout=120) # 2 minute timeout
            exit_code = process.returncode
            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "success": exit_code == 0
            }
        except FileNotFoundError:
            return {
                "stdout": "",
                "stderr": f"Error: Script not found at {command[0]}",
                "exit_code": -1,
                "success": False
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Error: Scraper execution timed out.",
                "exit_code": -1,
                "success": False
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Error during scraper execution: {e}",
                "exit_code": -1,
                "success": False
            }
