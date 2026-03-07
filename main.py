#!/usr/bin/env python3
"""ClaudeEye — Claude Code with screen vision."""
import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from screenshot import capture_screen
from claude_client import ClaudeEyeClient

load_dotenv()
console = Console()

COMMANDS = {
    "/help": "Show this help",
    "/clear": "Clear conversation history",
    "/noscreen": "Send next message WITHOUT screenshot",
    "/screen": "Capture and show what Claude sees",
    "/quit": "Exit ClaudeEye",
    "/exit": "Exit ClaudeEye",
}

def print_banner():
    console.print(Panel.fit(
        "[bold cyan]👁️  ClaudeEye[/bold cyan]\n"
        "[dim]Claude Code with screen vision[/dim]\n\n"
        "[green]Auto-captures your screen with every message[/green]\n"
        "[dim]Type /help for commands[/dim]",
        border_style="cyan"
    ))

def print_help():
    console.print("\n[bold]Commands:[/bold]")
    for cmd, desc in COMMANDS.items():
        console.print(f"  [cyan]{cmd}[/cyan] — {desc}")
    console.print()

def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not set in .env[/red]")
        console.print("Copy .env.example to .env and add your API key")
        sys.exit(1)

    client = ClaudeEyeClient(api_key=api_key)
    print_banner()

    skip_screenshot = False

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()

            if not user_input:
                continue

            if user_input in ("/quit", "/exit"):
                console.print("[dim]Goodbye! 👋[/dim]")
                break
            elif user_input == "/help":
                print_help()
                continue
            elif user_input == "/clear":
                client.clear_history()
                console.print("[green]✓ Conversation history cleared[/green]")
                continue
            elif user_input == "/noscreen":
                skip_screenshot = True
                console.print("[yellow]Next message will be sent WITHOUT screenshot[/yellow]")
                continue
            elif user_input == "/screen":
                console.print("[dim]Capturing screen...[/dim]")
                try:
                    screenshot = capture_screen()
                    size_kb = len(screenshot) * 3 / 4 / 1024
                    console.print(f"[green]✓ Screenshot captured[/green] [dim]~{size_kb:.0f}KB[/dim]")
                except Exception as e:
                    console.print(f"[red]Screenshot failed: {e}[/red]")
                continue

            screenshot = None
            if not skip_screenshot:
                try:
                    console.print("[dim]📸 Capturing screen...[/dim]", end="")
                    screenshot = capture_screen()
                    console.print(" [green]✓[/green]")
                except Exception as e:
                    console.print(f" [yellow]⚠ Screenshot failed: {e}[/yellow]")
            else:
                skip_screenshot = False
                console.print("[dim](No screenshot)[/dim]")

            console.print("[dim]Thinking...[/dim]")
            try:
                response = client.send_message(user_input, screenshot)
                console.print(Panel(
                    Markdown(response),
                    title="[bold green]ClaudeEye[/bold green]",
                    border_style="green"
                ))
            except Exception as e:
                console.print(f"[red]API Error: {e}[/red]")

        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye! 👋[/dim]")
            break
        except EOFError:
            break

if __name__ == "__main__":
    main()
