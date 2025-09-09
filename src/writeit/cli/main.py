# ABOUTME: WriteIt main CLI entry point
# ABOUTME: Handles command parsing and dispatches to appropriate modules
import argparse
import sys
from writeit import __version__


def main():
    """Main CLI entry point for WriteIt."""
    parser = argparse.ArgumentParser(
        prog="writeit",
        description="LLM-powered writing pipeline tool with terminal UI"
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"writeit {__version__}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize workspace")
    init_parser.add_argument("workspace", help="Workspace directory name")
    
    # list-pipelines command
    subparsers.add_parser("list-pipelines", help="List available pipelines")
    
    # run command
    run_parser = subparsers.add_parser("run", help="Start TUI pipeline execution")
    run_parser.add_argument("pipeline", help="Pipeline configuration file (.yaml)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
        
    if args.command == "init":
        print(f"Initializing workspace: {args.workspace}")
        # TODO: Implement workspace initialization
        return 0
    elif args.command == "list-pipelines":
        print("Available pipelines:")
        print("  (No pipelines configured yet)")
        # TODO: Implement pipeline listing
        return 0
    elif args.command == "run":
        print(f"Running pipeline: {args.pipeline}")
        # TODO: Implement TUI pipeline execution
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())