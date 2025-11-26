import os

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.shortcuts import print_formatted_text

import doi

# Build the directory tree from DOI
fs = doi.fsspec.filesystem("doi", doi=input("Please enter the DOI: "))


class DOICompleter(Completer):
    def __init__(self, fs, cwd_ref):
        self.fs = fs
        self.cwd_ref = cwd_ref

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.strip()
        parts = text.split()
        if not parts:
            return

        cmd = parts[0]
        arg = parts[-1] if len(parts) > 1 else ""

        # Only complete on commands that expect paths
        if cmd in ("ls", "cd", "cat", "head", "info", "get"):
            cwd = self.cwd_ref[0]  # current working directory
            base_dir = cwd

            if "/" in arg:
                base_dir, prefix = arg.rsplit("/", 1)
                base_dir = base_dir.strip("/")
            else:
                prefix = arg

            try:
                items = self.fs.ls(base_dir)
            except Exception:
                return

            for item in items:
                name = item["name"].split("/")[-1]
                if name.startswith(prefix):
                    yield Completion(name, start_position=-len(prefix))


def doi_shell(fs):
    cwd = [""]
    session = PromptSession(completer=DOICompleter(fs, cwd))

    while True:
        try:
            cmdline = session.prompt(f"doi:/{cwd[0] or ''}$ ")
            parts = cmdline.strip().split()
            if not parts:
                continue
            cmd, *args = parts

            if cmd in ("exit", "quit"):
                break

            elif cmd == "pwd":
                print("/" + cwd[0] if cwd[0] else "/")

            elif cmd == "ls":
                path = args[0] if args else cwd[0]
                try:
                    items = fs.ls(path)
                    for item in items:
                        name = item["name"].split("/")[-1]
                        if item["type"] == "directory":
                            text = FormattedText([("ansiblue", name)])
                        else:
                            text = FormattedText([("ansigreen", name)])
                        print_formatted_text(text)
                except Exception as e:
                    print("Error:", e)

            elif cmd == "cd":
                if not args:
                    cwd[0] = ""
                else:
                    new_path = (
                        args[0]
                        if args[0].startswith("/")
                        else f"{cwd[0]}/{args[0]}".strip("/")
                    )
                    try:
                        info = fs.info(new_path)
                        if info["type"] == "directory":
                            cwd[0] = new_path
                        else:
                            print("Not a directory:", new_path)
                    except Exception as e:
                        print("Error:", e)

            elif cmd == "cat":
                if not args:
                    print("Usage: cat <filename>")
                else:
                    path = (
                        args[0]
                        if args[0].startswith("/")
                        else f"{cwd[0]}/{args[0]}".strip("/")
                    )
                    try:
                        with fs.open(path, "rb") as f:
                            print(f.read().decode(errors="replace"))
                    except Exception as e:
                        print("Error:", e)

            elif cmd == "head":
                if not args or info["type"] == "file":
                    print("Usage: head <filename>")
                else:
                    path = (
                        args[0]
                        if args[0].startswith("/")
                        else f"{cwd[0]}/{args[0]}".strip("/")
                    )
                    try:
                        with fs.open(path, "rb") as f:
                            print(f.read(500).decode(errors="replace"))
                    except Exception as e:
                        print("Error:", e)

            elif cmd == "info":
                if not args:
                    print("Usage: info <path>")
                else:
                    path = (
                        args[0]
                        if args[0].startswith("/")
                        else f"{cwd[0]}/{args[0]}".strip("/")
                    )
                    try:
                        info = fs.info(path)
                        print(f"Path: {path}")
                        print(f"Type: {info['type']}")
                        print(f"Size: {info['size']} bytes")
                    except Exception as e:
                        print("Error:", e)

            elif cmd == "get":
                if not args:
                    print("Usage: get <remote-path> [local-path]")
                else:
                    remote_path = (
                        args[0]
                        if args[0].startswith("/")
                        else f"{cwd[0]}/{args[0]}".strip("/")
                    )
                    local_path = (
                        args[1] if len(args) > 1
                        else os.path.basename(remote_path)
                    )
                    try:
                        with fs.open(remote_path, "rb") as fsrc, open(
                            local_path, "wb"
                        ) as fdst:
                            fdst.write(fsrc.read())
                        print(f"Downloaded {remote_path} → {local_path}")
                    except Exception as e:
                        print("Error:", e)

            elif cmd == "cache":
                if not args:
                    print("Usage: cache <info|list|clear>")
                else:
                    subcmd = args[0]
                    if subcmd == "info":
                        print(f"Cache dir: {fs.cache_dir}")
                        print(f"Cache size: {fs.cache_size()} bytes")
                    elif subcmd == "list":
                        print("Cached files:")
                        for f in fs.list_cache():
                            print(" ", f)
                    elif subcmd == "clear":
                        fs.clear_cache()
                        print("Cache cleared")
                    else:
                        print("Unknown cache subcommand")

            else:
                print("Commands: ls, cd, pwd, cat,\
                        head, info, get, cache, exit")

        except (KeyboardInterrupt, EOFError):
            print()
            break


doi_shell(fs)
