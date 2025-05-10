from pathlib import Path
from dataclasses import asdict

class Logger:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self._get_next_log_file()

    def _get_next_log_file(self) -> Path:
        existing_logs = list(self.log_dir.glob("log*.txt"))
        numbers = []

        for log in existing_logs:
            stem = log.stem 
            num_part = stem.replace("log", "")
            if num_part.isdigit():
                numbers.append(int(num_part))
                
        next_number = max(numbers, default=-1) + 1
        return self.log_dir / f"log{next_number}.txt"

    def log(self, message):
        log_entry = self._format_log_entry(message)
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    def _format_log_entry(self, message) -> str:
        message_type = type(message).__name__  
        message_dict = asdict(message) 
        lines = [f"Message Type: {message_type}"]

        for key, value in message_dict.items():
            lines.append(f"{key}: {value}")

        return "\n".join(lines) + "\n" + "-" * 40