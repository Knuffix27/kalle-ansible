#!/usr/bin/env python3
"""
Test script to demonstrate the CronMarkdownProcessor functionality.
"""

import sys
import tempfile
from pathlib import Path

# Add the script directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from process_crons import CronMarkdownProcessor


def test_basic_generation():
    """Test basic markdown generation."""
    print("=" * 60)
    print("TEST 1: Basic Markdown Generation")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test.md"

        processor = CronMarkdownProcessor(str(output_file))

        cron_data = {
            "hostname": "web-server-01",
            "user_crontab": "0 2 * * * /usr/local/bin/backup.sh\n30 3 * * * /usr/local/bin/cleanlogs.sh",
            "system_crontab": "SHELL=/bin/bash\nPATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin\n0 0 * * * root /opt/scripts/maintenance.sh",
            "cron_d_files": "=== /etc/cron.d/sysstat ===\n*/10 * * * * root /usr/lib64/sa/sa1 1 1\n\n=== /etc/cron.d/logrotate ===\n0 3 * * * root /usr/sbin/logrotate -f /etc/logrotate.conf",
        }

        processor.update_markdown(cron_data)

        # Verify file was created
        assert output_file.exists(), "Output file not created"
        print("✓ File created successfully")

        # Read and display content
        content = output_file.read_text()
        print("\nGenerated Markdown:\n")
        print(content)
        print()


def test_static_section_preservation():
    """Test preservation of static sections."""
    print("=" * 60)
    print("TEST 2: Static Section Preservation")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test.md"

        processor = CronMarkdownProcessor(str(output_file))

        # First generation with static section
        initial_data = {
            "hostname": "web-server-01",
            "user_crontab": "0 2 * * * /backup.sh",
            "system_crontab": "",
            "cron_d_files": "",
        }

        # Add manual static section
        static_section = """## Important Notes

This server is responsible for:
- Daily database backups
- Weekly maintenance tasks

**Contact:** devops@example.com"""

        processor.update_markdown(initial_data)

        # Manually add static section
        content = output_file.read_text()
        updated_content = (
            content.replace(
                "## User Crontab",
                f"[STATIC_START]\n{static_section}\n[STATIC_END]\n\n## User Crontab",
            )
        )
        output_file.write_text(updated_content)

        print("First version with static section:")
        print(output_file.read_text())
        print("\n")

        # Second generation - static section should be preserved
        updated_data = {
            "hostname": "web-server-01",
            "user_crontab": "0 2 * * * /backup.sh\n0 3 * * * /cleanup.sh",  # Added new cron
            "system_crontab": "0 0 * * * root /maintenance.sh",
            "cron_d_files": "",
        }

        processor.update_markdown(updated_data)

        # Check results
        new_content = output_file.read_text()
        assert "[STATIC_START]" in new_content, "Static section marker lost"
        assert "Important Notes" in new_content, "Static content lost"
        assert "devops@example.com" in new_content, "Static content modified"
        assert "/cleanup.sh" in new_content, "New cron not added"

        print("✓ Static section preserved!")
        print("\nUpdated version (static section preserved):")
        print(new_content)
        print()


def test_no_crontabs():
    """Test generation when no crontabs exist."""
    print("=" * 60)
    print("TEST 3: Handling Missing Crontabs")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test.md"

        processor = CronMarkdownProcessor(str(output_file))

        cron_data = {
            "hostname": "empty-server",
            "user_crontab": "No crontab entries",
            "system_crontab": "No system crontab",
            "cron_d_files": "",
        }

        processor.update_markdown(cron_data)

        content = output_file.read_text()
        assert "No user crontab entries found" in content
        assert "No system crontab found" in content

        print("✓ Handles missing crontabs gracefully")
        print("\nGenerated Markdown:\n")
        print(content)
        print()


if __name__ == "__main__":
    print("\n🧪 Running Cron Markdown Processor Tests\n")

    try:
        test_basic_generation()
        test_static_section_preservation()
        test_no_crontabs()

        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
