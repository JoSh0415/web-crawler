"""Simple command-line shell for the coursework search tool.

This file only provides the shell structure and placeholder handlers.
The crawler/indexing/search logic can be added later.
"""


def handle_build() -> None:
    """Placeholder for the build command."""
    print("[build] Placeholder: this will crawl the site, build the index, and save it.")


def handle_load() -> None:
    """Placeholder for the load command."""
    print("[load] Placeholder: this will load a saved index from disk.")


def handle_print(word: str) -> None:
    """Placeholder for the print command."""
    print(f"[print] Placeholder: this will print the inverted index entry for '{word}'.")


def handle_find(query: str) -> None:
    """Placeholder for the find command."""
    print(f"[find] Placeholder: this will search the index for '{query}'.")


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
        print("Available commands: build, load, print <word>, find <query>, exit")

    return True


def run_shell() -> None:
    """Start the interactive shell."""
    print("Search tool shell")
    print("Type a command: build, load, print <word>, find <query>")
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


if __name__ == "__main__":
    run_shell()