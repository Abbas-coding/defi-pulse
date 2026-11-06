# Repository Guidelines

## Project Structure & Module Organization

This repository is an initial scaffold for `defi-pulse`. Its only existing tracked project file is the root `README.md`; no application source, tests, or asset directories have been established.

When adding implementation, keep the structure explicit: use `src/` for application code, `tests/` for tests, and `assets/` for static resources where appropriate. Document the actual layout in `README.md` as it develops. These paths are proposed conventions, not existing directories.

## Build, Test, and Development Commands

No package manifest, build system, development server, or test runner is currently configured. Commands such as `npm test` or `pnpm build` are not available project workflows yet.

When introducing tooling, provide reproducible setup, development, build, and test commands in `README.md`. Commit the appropriate dependency manifest and lockfile together. Useful checks available now include:

- `git status --short`: review pending changes.
- `git diff --check`: detect whitespace errors in tracked changes.
- `git diff`: inspect changes before committing.

## Coding Style & Naming Conventions

No language, formatter, or linter has been selected. Keep Markdown readable with descriptive headings, short paragraphs, and fenced code blocks for commands. Follow nearby conventions when extending existing files.

When adding code, choose consistent indentation and naming for the selected language, and record those choices in the formatter or linter configuration. Avoid mixing unrelated formatting changes with functional work.

## Testing Guidelines

No tests, testing framework, or coverage threshold currently exists. Add a suitable test runner with the first testable implementation and document its invocation. Use descriptive test names that state the behavior being checked. Cover new behavior and include regression tests for bug fixes where practical.

## Commit & Pull Request Guidelines

Git history currently contains only `first commit`, so no established commit-message convention can be inferred. Use short, imperative subjects, such as `Add dashboard layout`, and keep commits focused.

Pull requests should explain the purpose, summarize changes, and state how they were validated. Link related issues when applicable; include screenshots for visible interface changes. Explicitly identify missing automated checks.

## Security & Configuration

Never commit credentials, private keys, or populated environment files. If configuration becomes necessary, document required variables and provide an example file containing placeholders only.
