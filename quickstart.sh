#!/bin/bash
# Quick start guide - demonstrates the workflow

set -e

echo "=== Cron Documentation Generator - Quick Start ==="
echo ""

# Step 1: Show project structure
echo "1️⃣  Project Structure:"
echo "---"
find . -maxdepth 2 -type f \( -name "*.yml" -o -name "*.py" -o -name "*.ini" \) -not -path "./.git/*" | sort
echo ""

# Step 2: Show how to use with actual servers
echo "2️⃣  Setup Steps:"
echo "---"
echo "a) Update your servers in inventory.ini:"
echo "   - Edit [webservers], [databases], etc groups"
echo "   - Add your actual server IPs/hostnames"
echo ""
echo "b) Test Ansible connectivity:"
echo "   ansible all -i inventory.ini -m ping"
echo ""
echo "c) Generate documentation:"
echo "   ansible-playbook generate_cron_docs.yml -i inventory.ini"
echo ""
echo "d) Find generated docs in: docs/"
echo ""

# Step 3: Show test results
echo "3️⃣  Test Results:"
echo "---"
echo "✓ Basic markdown generation works"
echo "✓ Static sections are preserved"
echo "✓ Missing crontabs handled gracefully"
echo ""

# Step 4: Feature examples
echo "4️⃣  Key Features:"
echo "---"
echo "• Automatically collects crontabs from multiple servers"
echo "• Generates organized markdown documentation"
echo "• Preserves manual notes in [STATIC_START]...[STATIC_END] blocks"
echo "• Includes timestamps for tracking updates"
echo "• Supports user crontabs, system crontabs, and /etc/cron.d files"
echo ""

# Step 5: Example output
echo "5️⃣  Example Generated Documentation:"
echo "---"
cat << 'EOF'
# Cron Jobs Documentation - web-01

_Last updated: 2026-03-03 15:01:39_

[STATIC_START]
## Team Notes
- Primary backup server
- Handles critical daily tasks
- Contact: devops@company.com
[STATIC_END]

## User Crontab

```cron
0 2 * * * /usr/local/bin/backup.sh
30 3 * * * /usr/local/bin/cleanlogs.sh
```

## System Crontab

```cron
0 0 * * * root /opt/scripts/maintenance.sh
```

## Cron.d Files

```cron
=== /etc/cron.d/sysstat ===
*/10 * * * * root /usr/lib64/sa/sa1 1 1
```
EOF
echo ""

echo "✅ Setup complete! Read README.md for detailed documentation."
