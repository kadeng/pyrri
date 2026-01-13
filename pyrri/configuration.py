import json
import re
import urllib.request
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Pattern
from pathlib import Path

from pyrri.weekly_timespans import WeeklyTimespans


class RestrictionAction(Enum):
    MINIMIZE = "minimize"
    TERMINATE = "terminate"
    FORCE_NAVIGATION = "force_navigation"
    IGNORE = "ignore"


@dataclass
class ProcessRule:
    process_regex: Optional[Pattern]
    title_regex: Optional[Pattern]
    action: RestrictionAction


class Configuration:
    def __init__(
        self,
        unrestricted_times: WeeklyTimespans,
        rules: List[ProcessRule],
        enabled: bool,
    ):
        self.unrestricted_times = unrestricted_times
        self.rules = rules
        self.enabled = enabled

    @classmethod
    def from_json(cls, json_data: dict) -> "Configuration":
        # Parse timespans
        # JSON format: [[[d, h, m], [d, h, m]], ...]
        enabled = json_data.get("enabled", True)
        raw_times = json_data.get("unrestricted_times", [])
        # WeeklyTimespans expects iterables of start/end points.
        # Lists work fine with the * unpacking in WeeklyTimespans.__init__

        unrestricted = WeeklyTimespans(raw_times)

        # Parse rules
        rules = []
        for rule_data in json_data.get("rules", []):
            proc_pat = rule_data.get("process_regex")
            title_pat = rule_data.get("title_regex")
            action_str = rule_data.get("action")

            if not action_str:
                continue

            try:
                action = RestrictionAction(action_str)
            except ValueError:
                # Ignore unknown actions or log them
                continue

            rules.append(
                ProcessRule(
                    process_regex=re.compile(proc_pat, re.IGNORECASE)
                    if proc_pat
                    else None,
                    title_regex=re.compile(title_pat, re.IGNORECASE)
                    if title_pat
                    else None,
                    action=action,
                )
            )

        return cls(unrestricted, rules, enabled)

    @classmethod
    def load_from_url(cls, url: str) -> "Configuration":
        # Set a timeout and user agent to be polite/safe
        headers = {"User-Agent": "Pyrri/0.1.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return cls.from_json(data)

    @classmethod
    def load_from_file(cls, path: Path) -> "Configuration":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return cls.from_json(data)
