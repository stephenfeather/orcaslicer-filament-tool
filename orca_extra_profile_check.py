"""CLI wrapper for OrcaSlicer profile validation."""

import sys
from pathlib import Path

import click

from src.validator import ProfileValidator


# Utility functions for printing messages in different colors.
def print_error(msg):
    print(f"\033[91m[ERROR]\033[0m {msg}")  # Red

def print_warning(msg):
    print(f"\033[93m[WARNING]\033[0m {msg}")  # Yellow

def print_info(msg):
    print(f"\033[94m[INFO]\033[0m {msg}")  # Blue

def print_success(msg):
    print(f"\033[92m[SUCCESS]\033[0m {msg}")  # Green





@click.group()
def cli() -> None:
    """Check OrcaSlicer profiles for common issues."""


@cli.command()
@click.option(
    "--vendor",
    type=str,
    help="Specify a single vendor to check",
)
@click.option(
    "--check-filaments",
    is_flag=True,
    help="Check compatible_printers in filament profiles",
)
@click.option(
    "--check-materials",
    is_flag=True,
    help="Check default materials in machine profiles",
)
@click.option(
    "--check-obsolete-keys",
    is_flag=True,
    help="Warn if obsolete keys are found",
)
@click.option(
    "--profiles-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Override profiles directory",
)
def check(
    vendor: str | None,
    check_filaments: bool,
    check_materials: bool,
    check_obsolete_keys: bool,
    profiles_dir: Path | None,
) -> None:
    """Check profiles for common issues."""
    if profiles_dir is None:
        script_dir = Path(__file__).resolve().parent
        profiles_dir = script_dir.parent / "resources" / "profiles"

    click.echo(click.style("Checking profiles ...", fg="blue"))

    validator = ProfileValidator(profiles_dir)
    checked_vendor_count = 0
    all_issues = []

    if vendor:
        result = validator.validate_all(
            vendor,
            check_filaments=check_filaments,
            check_materials=check_materials,
            check_obsolete=check_obsolete_keys,
        )
        all_issues.extend(result.issues)
        checked_vendor_count = 1
    else:
        for vendor_dir in profiles_dir.iterdir():
            if not vendor_dir.is_dir() or vendor_dir.name == "OrcaFilamentLibrary":
                continue
            result = validator.validate_all(
                vendor_dir.name,
                check_filaments=check_filaments,
                check_materials=check_materials,
                check_obsolete=check_obsolete_keys,
            )
            all_issues.extend(result.issues)
            checked_vendor_count += 1

    # Print issues
    for issue in all_issues:
        if issue.level == "error":
            click.echo(click.style(f"[ERROR] {issue.message}", fg="red"), err=True)
        else:
            click.echo(click.style(f"[WARNING] {issue.message}", fg="yellow"))

    # Print summary
    errors = [i for i in all_issues if i.level == "error"]
    warnings = [i for i in all_issues if i.level == "warning"]

    click.echo("\n" + "=" * 50)
    click.echo(click.style(f"Checked vendors     : {checked_vendor_count}", fg="blue"))

    if errors:
        click.echo(
            click.style(f"Files with errors   : {len(errors)}", fg="red"),
            err=True,
        )
    else:
        click.echo(click.style("Files with errors   : 0", fg="green"))

    if warnings:
        click.echo(click.style(f"Files with warnings : {len(warnings)}", fg="yellow"))
    else:
        click.echo(click.style("Files with warnings : 0", fg="green"))

    click.echo("=" * 50)

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    cli()
