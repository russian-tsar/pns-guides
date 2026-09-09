# Issue tracker: Local Markdown

Issues and specs for this repo live as Markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The spec is `.scratch/<feature-slug>/spec.md`
- Implementation issues are separate files at
  `.scratch/<feature-slug>/issues/<NN>-<slug>.md`
- Ticket numbering starts at `01`
- Triage state is recorded as a `Status:` line near the top
- Comments are appended under a `## Comments` heading

## Publishing and fetching

When a skill says “publish to the issue tracker”, create a file under the
appropriate `.scratch/<feature-slug>/` directory.

When a skill says “fetch the relevant ticket”, read the referenced Markdown
file directly.
