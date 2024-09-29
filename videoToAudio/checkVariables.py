import os
import sys
import subprocess

def check_command_in_shell(command):
    """
    Check if a command exists in the shell (works on both Unix and Windows).
    Uses 'which' for Unix-based systems and 'where' for Windows.
    """
    try:
        # Use 'which' on Unix-like systems and 'where' on Windows to check if the command exists
        if os.name == 'nt':  # Windows
            subprocess.run(['where', command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        else:  # Unix-like (Linux, macOS)
            subprocess.run(['which', command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True  # Command found
    except subprocess.CalledProcessError:
        return False  # Command not found

def check_env_and_shell(command_words):
    shell_missing = []

    for word in command_words:
        # Check if the command exists in the shell using 'which' or 'where'
        if not check_command_in_shell(word):
            shell_missing.append(word)

    print()  # Blank line to separate sections

    # Show missing shell commands
    if shell_missing:
        print("Missing shell commands:")
        for command in shell_missing:
            print(command)
        print("\nExiting program due to missing shell commands.")
        sys.exit(1)  # Exit if any command is missing from the shell
    else:
        print("All shell commands are available.")

def main():
    if len(sys.argv) > 1:
        # Pass all command words to the check function
        command_words = sys.argv[1:]
        check_env_and_shell(command_words)
    else:
        print("Error: No command words provided.")
        sys.exit(1)

if __name__ == "__main__":
    main()
