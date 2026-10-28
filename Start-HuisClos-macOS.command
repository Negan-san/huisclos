#!/bin/bash
cd -- "$(dirname -- "$0")" || exit 1
export PYTHONUTF8=1
if [ -x ".venv-toolkit/bin/python" ]; then
    ".venv-toolkit/bin/python" "scripts/toolkit_launcher.py" "$@"
    huisclos_exit=$?
else
    huisclos_python=""
    for candidate in python3.12 python3; do
        if "$candidate" -c 'import sys; assert sys.version_info[:2] == (3, 12)' >/dev/null 2>&1; then
            huisclos_python="$candidate"
            break
        fi
    done
    if [ -z "$huisclos_python" ]; then
        echo "Python 3.12 64-bit is required. Install it from https://www.python.org/downloads/"
        echo "See START_HERE.md, then reopen this file."
        read -r -p "Press Enter to close. "
        exit 1
    fi
    "$huisclos_python" "scripts/toolkit_launcher.py" "$@"
    huisclos_exit=$?
fi
if [ "$huisclos_exit" -ne 0 ]; then
    echo "HuisClos stopped with an error. See the message above and START_HERE.md."
    read -r -p "Press Enter to close. "
fi
exit "$huisclos_exit"
