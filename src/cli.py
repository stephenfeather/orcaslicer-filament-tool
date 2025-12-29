"""Command-line interface for OrcaSlicer profile exporter."""

from pathlib import Path

import click

from src import __version__
from src.config import create_config
from src.constants import TEMPLATE_VERSION
from src.exporter import ExportError
from src.exporter import ProfileExporter
from src.resolver import CircularInheritanceError
from src.resolver import InvalidProfileError
from src.resolver import ProfileNotFoundError
from src.resolver import ProfileResolver


def _show_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Display tool version and template version."""
    if value:
        click.echo(f"orcaslicer-export, version {__version__}")
        click.echo(f"Templates: {TEMPLATE_VERSION}")
        ctx.exit()


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    epilog="\b\nEXAMPLES:\n  orcaslicer-export \"Generic PLA.json\"\n  orcaslicer-export \"/path/to/profile.json\" --output ./exports",
)
@click.option(
    "--version",
    is_flag=True,
    callback=_show_version,
    expose_value=False,
    is_eager=True,
    help="Show version information and exit.",
)
def cli() -> None:
    """Export OrcaSlicer profiles as self-contained JSON files.

    This tool resolves OrcaSlicer profile inheritance chains and exports
    profiles as standalone JSON files without dependencies on parent
    templates.
    """


@cli.command()
@click.argument(
    "profile",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Output directory for exported profiles (default: current directory)",
)
@click.option(
    "--output-name",
    type=str,
    help="Custom filename for exported profile (default: auto-generated)",
)
@click.option(
    "--validate",
    is_flag=True,
    help="Validate profile before exporting",
)
@click.option(
    "--config-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Override OrcaSlicer configuration directory",
)
def export(
    profile: str,
    output: str | None,
    output_name: str | None,
    validate: bool,
    config_dir: str | None,
) -> None:
    """Export a profile with inheritance resolution.

    PROFILE is the path to the profile JSON file to export. The profile
    can be from any OrcaSlicer location (user, system, or samples).

    Examples:

        # Export with auto-detected settings
        orcaslicer-export "Generic PLA.json"

        # Export with custom output directory
        orcaslicer-export "/path/to/profile.json" --output ./exports

        # Export with custom filename and validation
        orcaslicer-export "/path/to/profile.json" -o exports --output-name
        custom.json --validate
    """
    try:
        profile_path = Path(profile).resolve()

        if not profile_path.exists():
            raise click.ClickException(
                f"Profile not found: {profile_path}"
            )

        click.echo(f"Loading profile: {profile_path.name}")

        # Create config
        if config_dir:
            config = create_config(
                config_dir=Path(config_dir),
            )
        else:
            config = create_config()

        # Create resolver
        resolver = ProfileResolver(config)

        # Resolve profile
        click.echo("Resolving inheritance chain...")
        resolved_profile = resolver.resolve_profile(profile_path)

        # Create exporter
        output_dir = Path(output) if output else Path.cwd()
        exporter = ProfileExporter(output_dir=output_dir, validate=validate)

        # Export profile
        click.echo("Exporting profile...")
        output_path = exporter.export_profile(
            resolved_profile,
            filename=output_name,
            source_path=profile_path,
        )

        click.echo()
        click.secho("✓ Profile exported successfully!", fg="green")
        click.echo(f"  Output: {output_path}")

        # Show profile information
        click.echo()
        click.echo("Profile Information:")
        click.echo(f"  Name: {resolved_profile.get('name', 'Unknown')}")
        click.echo(f"  Type: {resolved_profile.get('type', 'unknown')}")
        click.echo(f"  Keys: {len(resolved_profile)}")

    except ProfileNotFoundError as e:
        raise click.ClickException(f"Parent profile not found: {e}")
    except CircularInheritanceError as e:
        raise click.ClickException(f"Circular inheritance detected: {e}")
    except InvalidProfileError as e:
        raise click.ClickException(f"Invalid profile: {e}")
    except ExportError as e:
        raise click.ClickException(f"Export failed: {e}")
    except Exception as e:
        raise click.ClickException(
            f"Unexpected error: {type(e).__name__}: {e}"
        )


if __name__ == "__main__":
    cli()


__all__ = ["cli", "export"]
