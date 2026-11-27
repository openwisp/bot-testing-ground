"""Restrict a reviewer process and its children to designated writable paths."""

import ctypes
import os
import platform
import sys

# Linux UAPI numbers are shared by the 64-bit Ubuntu runner architectures.
CREATE_RULESET, ADD_RULE, RESTRICT_SELF = 444, 445, 446
RULESET_VERSION = 1
RULE_PATH_BENEATH = 1
PR_SET_NO_NEW_PRIVS = 38

# Handle file changes without restricting the reads needed by runtimes and tests.
# REFER covers cross-directory moves and hard links; ABI 3 adds TRUNCATE.
WRITE_FILE = 1 << 1
TRUNCATE = 1 << 14
WRITE_TREE = WRITE_FILE | TRUNCATE | sum(1 << bit for bit in range(4, 14))


class Ruleset(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]


class PathRule(ctypes.Structure):
    # The Linux UAPI declares this struct packed. ctypes uses this layout with _pack_.
    _layout_ = "ms"
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]


def check(result):
    if result < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    return result


def restrict(paths):
    """Install the policy before launching any installer or test code."""
    if sys.platform != "linux" or platform.machine() not in ("x86_64", "aarch64"):
        raise ValueError("Unsupported reviewer platform")
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    if check(libc.syscall(CREATE_RULESET, None, 0, RULESET_VERSION)) < 3:
        raise ValueError("Landlock ABI 3 or newer is required")
    rules = Ruleset(WRITE_TREE)
    ruleset = check(
        libc.syscall(CREATE_RULESET, ctypes.byref(rules), ctypes.sizeof(rules), 0)
    )
    try:
        for path, rights in [(path, WRITE_TREE) for path in paths] + [
            ("/dev/null", WRITE_FILE)
        ]:
            flags = os.O_DIRECTORY if rights == WRITE_TREE else 0
            fd = os.open(path, os.O_PATH | os.O_CLOEXEC | os.O_NOFOLLOW | flags)
            try:
                rule = PathRule(rights, fd)
                check(
                    libc.syscall(
                        ADD_RULE, ruleset, RULE_PATH_BENEATH, ctypes.byref(rule), 0
                    )
                )
            finally:
                os.close(fd)
        check(libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0))
        check(libc.syscall(RESTRICT_SELF, ruleset, 0))
    finally:
        os.close(ruleset)


def main():
    try:
        separator = sys.argv.index("--", 1)
        command_start = separator + 1
        paths, command = sys.argv[1:separator], sys.argv[command_start:]
        if not paths or not command:
            raise ValueError("Specify writable directories and a command")
        restrict(paths)
    except (OSError, ValueError) as error:
        print(f"Could not restrict reviewer writes: {error}", file=sys.stderr)
        return 1
    os.execvp(command[0], command)


if __name__ == "__main__":
    sys.exit(main())
