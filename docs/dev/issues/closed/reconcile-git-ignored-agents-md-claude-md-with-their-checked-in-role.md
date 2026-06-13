# 164. Reconcile Git-Ignored `AGENTS.md` / `CLAUDE.md` With Their Checked-In Role

Resolved by an explicit project-owner decision: `AGENTS.md` and
`CLAUDE.md` are **intentionally git-ignored** and kept local-only, not
committed repository artifacts. The `.gitignore` `# Agents` block keeps
both files ignored, and a note at the top of `AGENTS.md` (plus a clause
in §Change Discipline) records that they are deliberately local-only and
that their `AGENTS_review-N.md` / `AGENTS_reply-N.md` artifacts are
likewise untracked and may be cleaned up once a review cycle closes. This
removes the earlier contradiction (the document described itself as
checked-in while being ignored) by adopting the local-only branch rather
than committing the files.
