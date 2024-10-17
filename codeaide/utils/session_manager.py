import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from codeaide.utils.logging_config import get_logger
from codeaide.utils.file_handler import FileHandler
from codeaide.utils.general_utils import generate_session_id


class SessionManager:
    def __init__(self, base_dir: str, file_handler: FileHandler):
        self.base_dir = base_dir
        self.sessions_dir = file_handler.output_dir
        self.logger = get_logger()
        self.current_session_id = None
        self.file_handler = file_handler

    def create_new_session(self, based_on: Optional[str] = None) -> str:
        """Create a new session, optionally based on an existing one."""
        new_session_id = generate_session_id()
        new_session_dir = os.path.join(self.sessions_dir, new_session_id)
        os.makedirs(new_session_dir, exist_ok=True)

        self.file_handler.set_session_id(new_session_id)
        self.current_session_id = new_session_id

        if based_on:
            self._copy_session_contents(based_on, new_session_id)
            default_summary = f"Continued from session {based_on}"
        else:
            default_summary = "New empty session"

        self._update_session_metadata(
            new_session_id, summary=default_summary, based_on=based_on
        )
        return new_session_id

    def load_session(self, session_id: str) -> None:
        """Load an existing session."""
        session_dir = os.path.join(self.sessions_dir, session_id)
        if not os.path.exists(session_dir):
            raise ValueError(f"Session {session_id} does not exist.")

        self.file_handler.set_session_id(session_id)
        self.current_session_id = session_id

    def get_all_sessions(self) -> List[Dict[str, str]]:
        """Get a list of all non-empty sessions, sorted by most recent first."""
        sessions = []
        for session_id in os.listdir(self.sessions_dir):
            metadata = self._load_session_metadata(session_id)
            if metadata and metadata.get("summary") not in [
                "New session",
                "New empty session",
            ]:
                sessions.append(
                    {
                        "id": session_id,
                        "summary": metadata.get("summary", "No summary"),
                        "last_modified": metadata.get("last_modified", "Unknown"),
                    }
                )
        return sorted(sessions, key=lambda x: x["last_modified"], reverse=True)

    def update_session_summary(self, summary: str) -> None:
        """Update the summary for the current session."""
        if not self.current_session_id:
            raise ValueError("No current session.")
        self._update_session_metadata(self.current_session_id, summary=summary)

    def _copy_session_contents(self, source_id: str, target_id: str) -> None:
        """Copy contents from one session to another."""
        source_dir = os.path.join(self.sessions_dir, source_id)
        target_dir = os.path.join(self.sessions_dir, target_id)

        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(target_dir, item)
            if os.path.isfile(s):
                with open(s, "rb") as src, open(d, "wb") as dst:
                    dst.write(src.read())

    def _update_session_metadata(
        self,
        session_id: str,
        summary: Optional[str] = None,
        based_on: Optional[str] = None,
    ) -> None:
        """Update or create metadata for a session."""
        metadata_file = os.path.join(self.sessions_dir, session_id, "metadata.json")
        metadata = self._load_session_metadata(session_id) or {}

        metadata.update(
            {
                "last_modified": datetime.now().isoformat(),
                "summary": summary or metadata.get("summary", "New session"),
            }
        )

        if based_on:
            metadata["based_on"] = based_on

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def _load_session_metadata(self, session_id: str) -> Optional[Dict]:
        """Load metadata for a session."""
        metadata_file = os.path.join(self.sessions_dir, session_id, "metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, "r") as f:
                return json.load(f)
        return None

    def get_current_session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self.current_session_id

    def get_file_handler(self) -> FileHandler:
        """Get the current FileHandler instance."""
        return self.file_handler

    def load_previous_session(self, previous_session_id: str) -> str:
        """Load a previous session by creating a new session based on it."""
        new_session_id = self.create_new_session(based_on=previous_session_id)
        self._copy_session_contents(previous_session_id, new_session_id)
        self._update_session_metadata(new_session_id, based_on=previous_session_id)
        return new_session_id

    def get_session_summary(self, session_id: str) -> Optional[str]:
        """Get the summary for a specific session."""
        metadata = self._load_session_metadata(session_id)
        return metadata.get("summary") if metadata else None
