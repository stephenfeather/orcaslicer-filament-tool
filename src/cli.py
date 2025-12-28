"""Command-line interface for OrcaSlicer filament tool."""

from pathlib import Path

import click

from src.config import ProfileType
from src.config import create_config
from src.config import resolve_profile_path


@click.command()
@click.argument("profile")
@click.option(
    "--config-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="OrcaSlicer configuration directory (auto-detected if not provided)",
)
@click.option(
    "--user-profile",
    default="default",
    help="User profile name (default: 'default')",
)
@click.option(
    "--output",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="Output directory for exported profile",
)
def export_filament(
    profile: str,
    config_dir: Path | None,
    user_profile: str,
    _output: Path,
) -> None:
    """
    Export a flattened filament profile without inheritance dependencies.

    PROFILE: Name of the filament profile to export (e.g., "Generic PLA.json")
    """
    try:
        # Get project samples directory
        project_root = Path(__file__).parent.parent
        samples_dir = project_root / "samples"

        # Create config
        config = create_config(
            config_dir=config_dir,
            user_profile=user_profile,
            samples_dir=samples_dir if samples_dir.exists() else None,
        )

        # Resolve profile path
        profile_path = resolve_profile_path(profile, config, ProfileType.FILAMENT)
        click.echo(f"Found profile: {profile_path}")

        # TODO: Continue with parsing and export
        # This will be integrated with parser.py and exporter.py

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@click.command()
@click.argument("profile")
@click.option(
    "--config-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="OrcaSlicer configuration directory (auto-detected if not provided)",
)
@click.option(
    "--user-profile",
    default="default",
    help="User profile name (default: 'default')",
)
@click.option(
    "--output",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="Output directory for exported profile",
)
def export_machine(
    profile: str,
    config_dir: Path | None,
    user_profile: str,
    _output: Path,
) -> None:
    """
    Export a flattened machine profile without inheritance dependencies.

    PROFILE: Name of the machine profile to export (e.g., "Creality Ender 3.json")
    """
    try:
        # Get project samples directory
        project_root = Path(__file__).parent.parent
        samples_dir = project_root / "samples"

        # Create config
        config = create_config(
            config_dir=config_dir,
            user_profile=user_profile,
            samples_dir=samples_dir if samples_dir.exists() else None,
        )

        # Resolve profile path
        profile_path = resolve_profile_path(profile, config, ProfileType.MACHINE)
        click.echo(f"Found profile: {profile_path}")

        # TODO: Continue with parsing and export

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@click.command()
@click.argument("profile")
@click.option(
    "--config-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="OrcaSlicer configuration directory (auto-detected if not provided)",
)
@click.option(
    "--user-profile",
    default="default",
    help="User profile name (default: 'default')",
)
@click.option(
    "--output",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="Output directory for exported profile",
)
def export_process(
    profile: str,
    config_dir: Path | None,
    user_profile: str,
    _output: Path,
) -> None:
    """
    Export a flattened process profile without inheritance dependencies.

    PROFILE: Name of the process profile to export (e.g., "0.2mm Standard.json")
    """
    try:
        # Get project samples directory
        project_root = Path(__file__).parent.parent
        samples_dir = project_root / "samples"

        # Create config
        config = create_config(
            config_dir=config_dir,
            user_profile=user_profile,
            samples_dir=samples_dir if samples_dir.exists() else None,
        )

        # Resolve profile path
        profile_path = resolve_profile_path(profile, config, ProfileType.PROCESS)
        click.echo(f"Found profile: {profile_path}")

        # TODO: Continue with parsing and export

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@click.group()
def cli() -> None:
    """OrcaSlicer Filament Tool - Export profiles without inheritance dependencies."""


cli.add_command(export_filament)
cli.add_command(export_machine)
cli.add_command(export_process)


if __name__ == "__main__":
    cli()
