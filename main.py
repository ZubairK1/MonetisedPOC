"""Tiny text‑UI orchestrator for the whole flow."""
import subprocess
from rich.console import Console
from rich.table import Table

console = Console()

MENU = {
    "1": ("Deploy tokens", "python deploy.py"),
    "2": ("Swap 50 HAPD ⇄ 75 HBTD", "python swap.py"),
    "3": ("Show analytics for diabetes - without HE", "python aggregate_query.py diabetes"),
    "4": ("Show analytics for diabetes - with HE", "python aggregate_query_he.py diabetes"),
    "5": ("Show balances", "python check_balances.py"),
    "q": ("Quit", None),
}

def main():
    while True:
        table = Table(title="Hospital‑to‑Hospital Exchange POC")
        table.add_column("Key")
        table.add_column("Action")
        for k, (desc, _) in MENU.items():
            table.add_row(k, desc)
        console.print(table)
        choice = console.input("Select › ").strip()
        if choice == "q":
            break
        if choice in MENU:
            cmd = MENU[choice][1]
            console.rule(f"[yellow] Running: {cmd}")
            if cmd:
                subprocess.run(cmd.split())
            console.rule()
        else:
            console.print("[red]Invalid choice!")

if __name__ == "__main__":
    main()
