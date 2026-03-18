from pathlib import Path
from typing import Optional

from src.crawler import crawl_all_pages
from src.indexer import InvertedIndex, load_index, save_index
from src.search import format_index_entry, format_search_results

INDEX_FILE = Path("data/index.json")
LOADED_INDEX: Optional[InvertedIndex] = None


def handle_build() -> None:
    """Crawl the site, build the index, save it, and keep it loaded in memory."""
    global LOADED_INDEX

    print("Building index...")
    print("This may take a while because the crawler respects the 6-second politeness delay.")

    try:
        index = crawl_all_pages()
        save_index(index, INDEX_FILE)
    except Exception as exc:
        print("Build failed.")
        print(f"Reason: {exc}")
        return

    LOADED_INDEX = index
    print(f"Index built and saved to {INDEX_FILE}")


def handle_load() -> None:
    """Load the saved index from disk into memory."""
    global LOADED_INDEX

    if not INDEX_FILE.exists():
        print(f"No saved index file found at {INDEX_FILE}")
        print("Run 'build' first to create the index.")
        return

    try:
        LOADED_INDEX = load_index(INDEX_FILE)
        print(f"Index loaded from {INDEX_FILE}")
    except Exception as exc:
        LOADED_INDEX = None
        print("Could not load the index file.")
        print(f"Reason: {exc}")


def handle_print(word: str) -> None:
    """Print the inverted index entry for one word."""
    if LOADED_INDEX is None:
        print("No index is loaded.")
        print("Use 'build' or 'load' before running 'print'.")
        return

    print(format_index_entry(LOADED_INDEX, word))


def handle_find(query: str) -> None:
    """Print search results for a single-word or multi-word query."""
    if LOADED_INDEX is None:
        print("No index is loaded.")
        print("Use 'build' or 'load' before running 'find'.")
        return

    print(format_search_results(LOADED_INDEX, query))


def print_help() -> None:
    """Print the list of supported commands."""
    print("Available commands:")
    print("  build              Crawl the site, build the index, and save it")
    print("  load               Load the saved index from disk")
    print("  print <word>       Print the inverted index entry for one word")
    print("  find <query>       Search for one or more words")
    print("  help               Show this help message")
    print("  exit / quit        Exit the program")


def process_command(user_input: str) -> bool:
    """Process one line of input.

    Returns True to keep the shell running.
    Returns False to exit the shell.
    """
    text = user_input.strip()

    if not text:
        return True

    if text.lower() in {"exit", "quit"}:
        print("Goodbye!")
        return False

    if text.lower() == "help":
        print_help()
        return True

    parts = text.split()
    command = parts[0].lower()
    args = parts[1:]

    if command == "build":
        if args:
            print("Usage: build")
        else:
            handle_build()

    elif command == "load":
        if args:
            print("Usage: load")
        else:
            handle_load()

    elif command == "print":
        if len(args) != 1:
            print("Usage: print <word>")
        else:
            handle_print(args[0])

    elif command == "find":
        if not args:
            print("Usage: find <query>")
        else:
            query = " ".join(args)
            handle_find(query)

    else:
        print(f"Unknown command: {command}")
        print("Available commands: build, load, print <word>, find <query>, help, exit")

    return True


def run_shell() -> None:
    """Start the interactive shell."""
    print("Search tool shell")
    print("Type a command: build, load, print <word>, find <query>")
    print("Type 'help' for more information.")
    print("Type 'exit' or 'quit' to leave.")

    running = True
    while running:
        try:
            user_input = input("> ")
            running = process_command(user_input)
        except KeyboardInterrupt:
            print("\nInterrupted. Type 'exit' to quit.")
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as exc:
            print("Unexpected error while processing command.")
            print(f"Reason: {exc}")


if __name__ == "__main__":
    run_shell()