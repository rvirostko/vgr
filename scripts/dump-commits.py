#!/usr/bin/env python3
"""
Dump commit history from a given tag to HEAD in an
LLM-friendly format, as raw material for release-note generation.

Usage:
    dump-commits.py TAG [--output FILE] [--no-stat] [--no-merges]

Example:
    dump-commits.py v1.1.10 --output notes_v1.1.10_to_head.md
"""

import argparse
import subprocess
import sys

FIELD_SEP = "\x1f"  # unit separator, unlikely to appear in commit text
RECORD_SEP = "\x1e"  # record separator


def run_git(args):
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        sys.exit(result.returncode)
    return result.stdout


def verify_tag(tag):
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", tag],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(f"error: tag '{tag}' not found\n")
        sys.exit(1)


def get_commits(tag, include_merges):
    fmt = FIELD_SEP.join(["%H", "%h", "%an", "%ae", "%ad", "%s", "%b"]) + RECORD_SEP
    args = [
        "log",
        f"{tag}..HEAD",
        f"--pretty=format:{fmt}",
        "--date=iso-strict",
    ]
    if not include_merges:
        args.append("--no-merges")
    raw = run_git(args)
    records = [r for r in raw.split(RECORD_SEP) if r.strip()]
    commits = []
    for r in records:
#        print("!!", r)
        parts = r.strip("\n").split(FIELD_SEP)
#        print ("!!", parts)
        if len(parts) != 7:
            continue  # skip malformed record rather than crash on odd content
        full_hash, short_hash, author_name, author_email, date, subject, body = parts
        commits.append({
            "hash": full_hash,
            "short_hash": short_hash,
#            "author": author_name,
#            "email": author_email,
            "date": date,
            "subject": subject,
            "body": body.strip(),
        })
    return commits


def get_stat(commit_hash):
    return run_git(["show", "--stat", "--format=", commit_hash]).strip()


def format_output(tag, commits, include_stat):
    head = run_git(["rev-parse", "--short", "HEAD"]).strip()
    lines = []
    lines.append(f"# Commit history: {tag} → HEAD ({head})")
    lines.append(f"# Total commits: {len(commits)}")
    lines.append("")

    if not commits:
        lines.append("(no commits found in this range)")
        return "\n".join(lines)

    for c in commits:
        lines.append("---")
        lines.append(f"commit: {c['short_hash']} ({c['hash']})")
#        lines.append(f"author: {c['author']} <{c['email']}>")
        lines.append(f"date: {c['date']}")
        lines.append(f"subject: {c['subject']}")
        if c["body"]:
            lines.append("body: |")
            for bline in c["body"].splitlines():
                lines.append(f"  {bline}")
        if include_stat:
            stat = get_stat(c["hash"])
            if stat:
                lines.append("files: |")
                for sline in stat.splitlines():
                    lines.append(f"  {sline}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="tag to diff from (e.g. v1.1.10)")
    parser.add_argument("--no-stat", action="store_true", help="omit per-commit file change stats")
    parser.add_argument("--no-merges", action="store_true", help="exclude merge commits")
    args = parser.parse_args()

    verify_tag(args.tag)
    commits = get_commits(args.tag, include_merges=not args.no_merges)
    print(format_output(args.tag, commits, include_stat=not args.no_stat))

if __name__ == "__main__":
    main()
