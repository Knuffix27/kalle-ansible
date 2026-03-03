#!/usr/bin/env python3
"""
Script to process cron jobs and update markdown documentation.
Preserves static sections marked with [STATIC_START] and [STATIC_END].
"""

import re
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime


class CronMarkdownProcessor:
    """Process cron data and update markdown files with static section preservation."""

    STATIC_START_MARKER = "[STATIC_START]"
    STATIC_END_MARKER = "[STATIC_END]"

    def __init__(self, output_file: str):
        """Initialize the processor."""
        self.output_file = Path(output_file)

    def extract_static_section(self) -> Optional[str]:
        """
        Extract the static section from existing markdown file.

        Returns:
            The content between markers, or None if file doesn't exist.
        """
        if not self.output_file.exists():
            return None

        with open(self.output_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find static section with regex
        pattern = rf"{re.escape(self.STATIC_START_MARKER)}(.*?){re.escape(self.STATIC_END_MARKER)}"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            return match.group(1)
        return None

    def format_crontab(self, crontab: str, indent: int = 0) -> str:
        """
        Format crontab content as code block.

        Args:
            crontab: The crontab content
            indent: Number of spaces for indentation

        Returns:
            Formatted crontab as markdown code block
        """
        indent_str = " " * indent
        lines = [f"{indent_str}```cron"]
        lines.append(crontab)
        lines.append(f"{indent_str}```")
        return "\n".join(lines)

    def generate_markdown(
        self,
        hostname: str,
        user_crontab: str,
        system_crontab: str,
        cron_d_files: str,
        static_section: Optional[str] = None,
    ) -> str:
        """
        Generate markdown content with cron information.

        Args:
            hostname: Server hostname
            user_crontab: Content of user crontab
            system_crontab: Content of system crontab
            cron_d_files: Content of /etc/cron.d files
            static_section: Optional static section to preserve

        Returns:
            Generated markdown content
        """
        lines = []

        # Add header with timestamp
        lines.append(f"# Cron Jobs Documentation - {hostname}")
        lines.append(f"\n_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n")

        # Add static section if present
        if static_section:
            lines.append(self.STATIC_START_MARKER)
            lines.append(static_section)
            lines.append(self.STATIC_END_MARKER)
            lines.append("")

        # User crontab section
        lines.append("## User Crontab\n")
        if user_crontab.strip() and user_crontab != "No crontab entries":
            lines.append(self.format_crontab(user_crontab))
        else:
            lines.append("_No user crontab entries found._\n")

        # System crontab section
        lines.append("\n## System Crontab\n")
        if system_crontab.strip() and system_crontab != "No system crontab":
            lines.append(self.format_crontab(system_crontab))
        else:
            lines.append("_No system crontab found._\n")

        # Cron.d files section
        lines.append("\n## Cron.d Files\n")
        if cron_d_files.strip():
            lines.append(self.format_crontab(cron_d_files))
        else:
            lines.append("_No cron.d files found._\n")

        return "\n".join(lines)

    def update_markdown(
        self,
        cron_data: dict,
    ) -> None:
        """
        Update markdown file with cron data while preserving static sections.

        Args:
            cron_data: Dictionary with keys:
                - hostname: Server hostname
                - user_crontab: User crontab content
                - system_crontab: System crontab content
                - cron_d_files: Content of /etc/cron.d files
        """
        # Extract existing static section
        static_section = self.extract_static_section()

        # Generate new markdown
        markdown_content = self.generate_markdown(
            hostname=cron_data["hostname"],
            user_crontab=cron_data["user_crontab"],
            system_crontab=cron_data["system_crontab"],
            cron_d_files=cron_data["cron_d_files"],
            static_section=static_section,
        )

        # Write to file
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"✓ Updated {self.output_file}")


def main():
    """Example usage of the processor."""
    processor = CronMarkdownProcessor("docs/cron_documentation.md")

    # Example cron data (this would come from Ansible)
    example_data = {
        "hostname": "web-server-01",
        "user_crontab": "0 2 * * * /usr/local/bin/backup.sh",
        "system_crontab": "SHELL=/bin/bash\nPATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin\n0 0 * * * root /opt/scripts/maintenance.sh",
        "cron_d_files": "=== /etc/cron.d/sysstat ===\n*/10 * * * * root /usr/lib64/sa/sa1 1 1",
    }

    processor.update_markdown(example_data)


if __name__ == "__main__":
    main()
