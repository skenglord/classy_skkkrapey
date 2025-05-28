from pathlib import Path
from typing import Dict, List, Any
import os

from .base_adapter import ScraperAdapter

class MonoBasicAdapter(ScraperAdapter):
    """
    Adapter for the mono_basic_html.py scraper.
    """

    def __init__(self):
        # Assuming mono_basic_html.py is in the root of the repository
        # Adjust the path if it's located elsewhere.
        super().__init__(scraper_name="mono_basic_html", script_path="mono_basic_html.py")

    def run_scraper(self, action: str, params: Dict[str, Any], temp_output_dir: Path, local_http_server_url: str) -> Dict[str, Any]:
        if action == "help":
            command = ["python3", str(self.script_path.resolve()), "--help"]
            # CWD for --help should also be repo_root or script_path.parent
            repo_root = self.script_path.parent
            result = self._execute_command(command, cwd=str(repo_root))
            # --help usually exits 0 on success.
            result["output_files"] = [] 
            return result

        if action != "scrape":
            return {
                "stdout": "",
                "stderr": f"Action '{action}' not supported by {self.scraper_name}. Only 'scrape' or 'help' is supported.",
                "exit_code": -1,
                "output_files": [],
                "success": False
            }
        # ... (rest of the existing scrape logic) ...
        # Ensure the existing scrape logic is still there
        command = ["python3", str(self.script_path.resolve())]
        
        target_url = params.get("url")
        if not target_url:
            return {
                "stdout": "", "stderr": "Missing 'url' in params for scrape action.", "exit_code": -1, "output_files": [], "success": False
            }

        if params.get("target_url_is_local_file", False):
            # Make it a URL pointing to the local server
            # Assuming the file is at the root of the test_data served by the local server
            file_path = Path(target_url)
            command.extend(["--url", f"{local_http_server_url.rstrip('/')}/{file_path.name}"])
        else:
            command.extend(["--url", target_url])

        if "selectors" in params:
            for selector in params["selectors"]:
                command.extend(["--selector", selector])
        
        if "xpaths" in params:
            for xpath in params["xpaths"]:
                command.extend(["--xpath", xpath])

        output_files = []
        if "output_filename" in params:
            output_file_path = temp_output_dir / params["output_filename"]
            command.extend(["--output", str(output_file_path)])
            output_files.append(output_file_path)
        
        # For mono_basic_html.py, CWD should be the repository root if it needs to find utils or other files.
        # However, this script seems self-contained.
        # If scripts are in subdirectories like project_root/scrapers/mono_basic_html.py,
        # self.script_path.parent would be project_root/scrapers.
        # For now, let's assume the script can be run from anywhere if paths are absolute,
        # or from the repo root if paths are relative.
        # The _execute_command defaults cwd to script_path.parent.
        # If mono_basic_html.py is in the root, parent is also root.
        
        # Determine the root of the repository if the script is not in the root
        # This is a common pattern. For now, we assume the script is at the root
        # or its paths are handled correctly by being absolute or discoverable from its location.
        repo_root = self.script_path.parent # If script is at root, this is root.
        # If script is in a subdir, and it needs to run from repo root:
        # repo_root = Path(os.getcwd()) # Or a more robust way to find repo root

        result = self._execute_command(command, cwd=str(repo_root))
        result["output_files"] = output_files if result["success"] else []
        
        return result

    def get_capabilities(self) -> List[str]:
        """
        Returns a list of capabilities for mono_basic_html.py.
        """
        return [
            "scrape_single_url",
            "handles_css_selectors",
            "handles_xpath",
            "outputs_text_to_file",
            "outputs_text_to_stdout"
        ]
