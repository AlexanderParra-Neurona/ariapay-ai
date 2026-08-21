---
name: changelog
description: Generate or update CHANGELOG.md from git history following the Keep a Changelog 1.1.0 format (https://keepachangelog.com/en/1.1.0/). Use when the user asks to create/update a changelog, "write CHANGELOG.md", "log these changes", or invokes /changelog.
---

# Changelog Skill

Generate or update `CHANGELOG.md` at the repo root, following [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## Format reference

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 2026-08-20

#### Added
#### Changed
#### Fixed

## [1.1.0] - 2023-03-05

### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

[unreleased]: https://github.com/owner/repo/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/owner/repo/compare/v1.0.0...v1.1.0
```

Rules from the spec:
- Section order per version: Added, Changed, Deprecated, Removed, Fixed, Security. Omit empty sections — never print a heading with nothing under it.
- Newest version on top; within a version, sections in the fixed order above.
- Version headings: `## [x.y.z] - YYYY-MM-DD`. Keep an `## [Unreleased]` section at the top (may be empty) for merged-but-unreleased work.
- Dates in `YYYY-MM-DD`.
- One sub-bullet per entry, human-readable, describing impact not implementation ("Fixed crash when X" not "Fixed null check in Y.ts:42").
- Yanked releases: `## [x.y.z] - YYYY-MM-DD [YANKED]`.
- Compare-link reference list at the bottom, one per version, if the repo has a recognizable remote (GitHub/GitLab compare URLs). Skip this if there's no remote or the user doesn't want it.
- Not a git-log dump: filter to changes that matter to consumers of the project (users/API consumers), not every commit.

### Project extension: dated grouping inside Unreleased

Not part of the base spec — added per this project's preference so day-to-day work stays legible before a release cuts a version.

- Inside `## [Unreleased]`, group entries under a `### YYYY-MM-DD` sub-heading per day (date only, no time-of-day — Keep a Changelog doesn't track commit time, only release date).
- Under each date sub-heading, use `####` category headings (Added/Changed/Deprecated/Removed/Fixed/Security), same rules as version-level sections — omit empty ones.
- Newest date on top, same as version ordering.
- When a release is cut, these dated sub-headings inside Unreleased are collapsed away: their bullets merge into the flat Added/Changed/.../Security sections under the new `## [x.y.z] - YYYY-MM-DD` heading (a released version does NOT keep per-day sub-headings — only Unreleased does).

## Steps

1. Check for an existing `CHANGELOG.md` at repo root. Read it if present — preserve its existing entries and any custom preamble.
2. Determine the range to summarize:
   - If `CHANGELOG.md` exists with version headings, find the last released version's git tag (e.g. `v1.1.0`) and diff from there to `HEAD`.
   - If no changelog exists, ask the user whether to cover the full history or a specific range (e.g. since a given tag/date) — full history on an old repo can be huge.
3. Gather commits: `git log <range> --oneline --no-merges` (add `--merges` back in only if merge commits carry meaningful squashed context in this repo). For richer context on ambiguous commits, `git show <sha> --stat` as needed.
4. Classify each notable commit into Added / Changed / Deprecated / Removed / Fixed / Security based on its actual effect, not its commit-message prefix — a `fix:` commit that removes a feature belongs under Removed, not Fixed. Drop noise: formatting-only, CI config, test-only, chore/lint commits with no user-facing effect.
5. Determine target version:
   - If commits are already tagged/released, use the existing tag/version and its tag date.
   - If summarizing uncommitted/untagged work, put entries under `## [Unreleased]`, grouped by today's date (`### YYYY-MM-DD`, from `date +%Y-%m-%d`) per the dated-grouping extension above — do not invent a version number.
   - If the user gives an explicit version to cut, use that and today's date, and collapse any existing dated sub-headings under Unreleased into the new flat version section.
6. Write/merge into `CHANGELOG.md`: new/updated version block inserted in the right position (newest first), `[Unreleased]` kept at top. If today's date sub-heading already exists under Unreleased, append new entries into its existing category — don't create a duplicate date heading. Update compare links at the bottom if the file already uses them.
7. Show the user the new/changed section (not the whole file) and confirm before treating the task as done.

## Rules

- Never overwrite unrelated existing entries — only add/update the versions in scope.
- Don't fabricate a semantic version bump; ask if unclear whether a change is major/minor/patch.
- If the repo has no git history in range, say so rather than inventing entries.
- Group by effect on the consumer, not by file or by author.
- Keep entries terse — one line each, no commit hashes or file paths inline.
