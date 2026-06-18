#!/usr/bin/env python3
"""
Job Tracking Agent - CLI Interface
Usage: python agent.py <command> [options]
"""

import argparse
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import print as rprint

from sheets import SheetsClient
from ai_parser import AIParser
from config import STATUS_OPTIONS
from gmail import GmailClient, parse_email_status

console = Console()


def cmd_add(args, sheets: SheetsClient, parser: AIParser):
    """Manually add a job application."""
    console.print("\n[bold cyan]➕ Add New Job Application[/bold cyan]\n")

    company   = Prompt.ask("[yellow]Company name[/yellow]")
    role      = Prompt.ask("[yellow]Job title / role[/yellow]")
    url       = Prompt.ask("[yellow]Job posting URL[/yellow] (optional)", default="")
    location  = Prompt.ask("[yellow]Location[/yellow] (e.g. Lahore / Remote)", default="")
    salary    = Prompt.ask("[yellow]Salary / package[/yellow] (optional)", default="")
    notes     = Prompt.ask("[yellow]Notes[/yellow] (optional)", default="")

    # Optionally paste a JD and let AI parse it
    parse_jd = Confirm.ask("\n[cyan]Paste a job description for AI parsing?[/cyan]", default=False)
    skills_required = ""
    if parse_jd:
        console.print("[dim]Paste the JD below, then press Enter twice:[/dim]")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        jd_text = "\n".join(lines)
        if jd_text.strip():
            with console.status("[bold green]Parsing JD with AI..."):
                parsed = parser.parse_jd(jd_text)
            if parsed:
                role      = role or parsed.get("title", role)
                location  = location or parsed.get("location", location)
                salary    = salary or parsed.get("salary", salary)
                skills_required = ", ".join(parsed.get("skills", []))
                notes     = notes or parsed.get("summary", notes)
                console.print(f"\n[green]✔ AI extracted:[/green] {skills_required or 'see summary'}")

    job = {
        "company":          company,
        "role":             role,
        "url":              url,
        "location":         location,
        "salary":           salary,
        "skills_required":  skills_required,
        "status":           "Applied",
        "date_applied":     datetime.now().strftime("%Y-%m-%d"),
        "last_follow_up":   "",
        "next_follow_up":   "",
        "notes":            notes,
    }

    with console.status("[bold green]Saving to Google Sheets..."):
        added = sheets.add_job(job)

    if not added:
        console.print(f"\n[yellow]⚠ Duplicate — already exists:[/yellow] {role} @ {company}")
        return

    console.print(f"\n[bold green]✅ Added:[/bold green] {role} @ {company}")


def cmd_list(args, sheets: SheetsClient):
    """List all tracked applications."""
    console.print("\n[bold cyan]📋 Your Applications[/bold cyan]\n")

    status_filter = args.status if hasattr(args, "status") and args.status else None

    with console.status("[bold green]Loading from Sheets..."):
        jobs = sheets.get_all_jobs()

    if status_filter:
        jobs = [j for j in jobs if j.get("status", "").lower() == status_filter.lower()]

    if not jobs:
        console.print("[yellow]No applications found.[/yellow]")
        return

    table = Table(show_lines=True, expand=True)
    table.add_column("#",             style="dim",    width=4)
    table.add_column("Company",       style="cyan",   width=18)
    table.add_column("Role",          style="white",  width=22)
    table.add_column("Status",        style="bold",   width=14)
    table.add_column("Applied",       style="dim",    width=12)
    table.add_column("Next Follow-Up",style="yellow", width=14)
    table.add_column("Notes",         style="dim",    width=28)

    STATUS_COLORS = {
        "applied":    "blue",
        "interviewing": "yellow",
        "offered":    "green",
        "rejected":   "red",
        "ghosted":    "dim",
        "saved":      "magenta",
    }

    for i, j in enumerate(jobs, 1):
        st    = j.get("status", "Applied")
        color = STATUS_COLORS.get(st.lower(), "white")
        table.add_row(
            str(i),
            j.get("company", ""),
            j.get("role", ""),
            f"[{color}]{st}[/{color}]",
            j.get("date_applied", ""),
            j.get("next_follow_up", ""),
            (j.get("notes", "") or "")[:40],
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(jobs)} applications[/dim]")


def cmd_update(args, sheets: SheetsClient):
    """Update status or notes for an application."""
    console.print("\n[bold cyan]✏️  Update Application[/bold cyan]\n")

    with console.status("[bold green]Loading applications..."):
        jobs = sheets.get_all_jobs()

    if not jobs:
        console.print("[yellow]No applications found.[/yellow]")
        return

    # Quick list
    for i, j in enumerate(jobs, 1):
        console.print(f"  [dim]{i}.[/dim] [cyan]{j.get('company')}[/cyan] — {j.get('role')} [{j.get('status')}]")

    idx = Prompt.ask("\n[yellow]Enter # to update[/yellow]")
    try:
        job = jobs[int(idx) - 1]
    except (ValueError, IndexError):
        console.print("[red]Invalid number.[/red]")
        return

    console.print(f"\nUpdating: [bold]{job.get('role')} @ {job.get('company')}[/bold]")

    new_status = Prompt.ask(
        "[yellow]New status[/yellow]",
        choices=STATUS_OPTIONS,
        default=job.get("status", "Applied")
    )
    new_notes       = Prompt.ask("[yellow]Notes[/yellow]", default=job.get("notes", ""))
    next_follow_up  = Prompt.ask("[yellow]Next follow-up date[/yellow] (YYYY-MM-DD)", default=job.get("next_follow_up", ""))

    with console.status("[bold green]Saving..."):
        sheets.update_job(
            job["_row"],
            status          = new_status,
            notes           = new_notes,
            last_follow_up  = datetime.now().strftime("%Y-%m-%d"),
            next_follow_up  = next_follow_up,
        )

    console.print(f"[bold green]✅ Updated to '{new_status}'[/bold green]")


def cmd_remove(args, sheets: SheetsClient):
    """Remove an application from the sheet."""
    console.print("\n[bold cyan]🗑 Remove Application[/bold cyan]\n")

    with console.status("[bold green]Loading applications..."):
        jobs = sheets.get_all_jobs()

    if not jobs:
        console.print("[yellow]No applications found.[/yellow]")
        return

    for i, j in enumerate(jobs, 1):
        console.print(f"  [dim]{i}.[/dim] [cyan]{j.get('company')}[/cyan] — {j.get('role')} [{j.get('status')}]")

    idx = Prompt.ask("\n[yellow]Enter # to remove[/yellow]")
    try:
        job = jobs[int(idx) - 1]
    except (ValueError, IndexError):
        console.print("[red]Invalid number.[/red]")
        return

    console.print(f"\n[red]Removing:[/red] [bold]{job.get('role')} @ {job.get('company')}[/bold]")
    confirm = Confirm.ask("[yellow]Are you sure?[/yellow]", default=False)
    if not confirm:
        console.print("[dim]Cancelled.[/dim]")
        return

    with console.status("[bold red]Deleting from Google Sheets..."):
        sheets.delete_job(job["_row"])

    console.print(f"[bold green]🗑 Removed:[/bold green] {job.get('role')} @ {job.get('company')}")


def cmd_followup(args, sheets: SheetsClient):
    """Show applications that need a follow-up today or are overdue."""
    console.print("\n[bold cyan]🔔 Follow-Up Reminders[/bold cyan]\n")

    today = datetime.now().strftime("%Y-%m-%d")

    with console.status("[bold green]Checking Sheets..."):
        jobs = sheets.get_all_jobs()

    due = [
        j for j in jobs
        if j.get("next_follow_up") and j["next_follow_up"] <= today
        and j.get("status", "").lower() not in ("offered", "rejected", "ghosted")
    ]

    if not due:
        console.print("[green]✅ No follow-ups due today![/green]")
        return

    console.print(f"[yellow]⚠ {len(due)} follow-up(s) due:[/yellow]\n")

    table = Table(show_lines=True)
    table.add_column("Company",        style="cyan",   width=20)
    table.add_column("Role",           style="white",  width=24)
    table.add_column("Status",         width=14)
    table.add_column("Due Date",       style="red",    width=12)
    table.add_column("Last Follow-Up", style="dim",    width=14)

    for j in due:
        table.add_row(
            j.get("company", ""),
            j.get("role", ""),
            j.get("status", ""),
            j.get("next_follow_up", ""),
            j.get("last_follow_up", ""),
        )

    console.print(table)


def cmd_check_emails(args, sheets: SheetsClient, parser: AIParser):
    """Check Gmail for unread job-related emails and update application status."""
    console.print("\n[bold cyan]📧 Check Gmail for Job Updates[/bold cyan]\n")

    try:
        gmail = GmailClient()
    except Exception as e:
        console.print(f"[bold red]Gmail auth error:[/bold red] {e}")
        console.print("[dim]Run 'python -m gmail' first to authenticate.[/dim]")
        return

    with console.status("[bold green]Fetching unread job emails..."):
        emails = gmail.fetch_unread_job_emails()

    if not emails:
        console.print("[green]No unread job-related emails found.[/green]")
        return

    console.print(f"Found [yellow]{len(emails)}[/yellow] unread job-related email(s).\n")

    all_apps = sheets.get_all_records()

    for email in emails:
        console.print(f"[dim]Processing:[/dim] {email['subject']} (from: {email['from']})")
        parsed = parse_email_status(email, parser)
        
        if not parsed:
            console.print("  [dim]Not recognized as job-related, skipping.[/dim]")
            continue

        console.print(f"  [green]Parsed:[/green] {parsed['company']} — {parsed['role']} → [bold]{parsed['status']}[/bold] (confidence: {parsed['confidence']}%)")
        console.print(f"  [dim]Notes:[/dim] {parsed['notes']}")

        match = None
        for i, app in enumerate(all_apps):
            app_with_idx = {**app, '_row_index': i + 2}
            
            if parsed.get('email_thread_id') and app.get('email_thread_id') == parsed['email_thread_id']:
                match = app_with_idx
                break
            
            company_match = app.get('company', '').lower() == parsed['company'].lower()
            role_match = app.get('role', '').lower() == parsed['role'].lower()
            
            if company_match and role_match:
                match = app_with_idx
                break
                
            if company_match and parsed['role'].lower() in app.get('role', '').lower():
                match = app_with_idx
                break

        if match:
            row_idx = match['_row_index']
            updates = {
                'status': parsed['status'],
                'notes': f"{parsed['notes']}\n\n[Auto-updated from email: {email['subject']} ({email['date']})]",
                'email_thread_id': parsed['email_thread_id'],
            }
            
            if parsed['status'] in ['Interview Scheduled', 'Interview Completed']:
                updates['next_follow_up'] = ''
            
            sheets.update_row(row_idx, updates)
            console.print(f"  [bold green]✅ Updated existing application (row {row_idx})[/bold green]")
        else:
            console.print(f"  [yellow]No match found. Creating new entry...[/yellow]")
            new_row = {
                'company': parsed['company'],
                'role': parsed['role'],
                'url': '',
                'location': '',
                'salary': '',
                'skills_required': '',
                'status': parsed['status'],
                'date_applied': datetime.now().strftime('%Y-%m-%d'),
                'last_follow_up': '',
                'next_follow_up': '',
                'notes': f"[Auto-created from email: {email['subject']} ({email['date']})]\n{parsed['notes']}",
                'email_thread_id': parsed['email_thread_id'],
            }
            sheets.append_row(new_row)
            console.print(f"  [bold green]✅ Created new application[/bold green]")

        gmail.mark_as_read(email['id'])
        console.print("  [dim]Marked email as read.[/dim]\n")

    console.print("[bold green]✅ Email check complete![/bold green]")


def main():
    parser_cli = argparse.ArgumentParser(
        prog="agent",
        description="Job Tracking Agent — CLI",
    )
    sub = parser_cli.add_subparsers(dest="command", required=True)

    # add
    sub.add_parser("add",     help="Manually add a job application")

    # list
    p_list = sub.add_parser("list", help="List all tracked applications")
    p_list.add_argument("--status", help="Filter by status (e.g. Applied, Interviewing)")

    # remove
    sub.add_parser("remove",  help="Remove an application from the sheet")

    # update
    sub.add_parser("update",  help="Update status/notes for an application")

    # followup
    sub.add_parser("followup", help="Show applications needing follow-up")

    # check-emails
    sub.add_parser("check-emails", help="Check Gmail for unread job emails and update status")

    args = parser_cli.parse_args()

    # Init clients
    try:
        sheets  = SheetsClient()
        ai      = AIParser()
    except Exception as e:
        console.print(f"[bold red]Startup error:[/bold red] {e}")
        console.print("[dim]Check your config.py and credentials.[/dim]")
        sys.exit(1)

    dispatch = {
        "add":          lambda: cmd_add(args, sheets, ai),
        "list":         lambda: cmd_list(args, sheets),
        "remove":       lambda: cmd_remove(args, sheets),
        "update":       lambda: cmd_update(args, sheets),
        "followup":     lambda: cmd_followup(args, sheets),
        "check-emails": lambda: cmd_check_emails(args, sheets, ai),
    }

    dispatch[args.command]()


if __name__ == "__main__":
    main()
