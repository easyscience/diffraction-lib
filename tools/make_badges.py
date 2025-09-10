from pathlib import Path
import argparse
from typing import List, Tuple, Dict


"""
This script generates a markdown table of status badges for the EasyScience diffraction-lib repository,
covering code quality, test coverage, security scans, documentation builds, and package publishing.
The badges reflect statuses on master, develop, and the current feature branch.
"""


REPO = "easyscience/diffraction-lib"
SHIELDS = "https://img.shields.io"
GITHUB_WORKFLOWS = "https://github.com/easyscience/diffraction-lib/actions/workflows"
CODEFACTOR = "https://www.codefactor.io/repository/github/easyscience/diffraction-lib"
CODECOV = "https://codecov.io/gh/EasyScience/diffraction-lib"
STYLE = "style=for-the-badge"
LABEL = "label="


class BadgeGenerator:
    def __init__(self, repo: str = REPO, shields: str = SHIELDS) -> None:
        self.repo = repo
        self.shields = shields

    def _badge(self, section: str, branch: str, extras: str = "") -> str:
        url = f"{self.shields}/{section}/github/{self.repo}/{branch}?{LABEL}&{STYLE}"
        if extras:
            url += f"&{extras}"
        return url

    def codecov_badge(self, branch: str = "master") -> str:
        token = "token=qtsB5Q5BXO"
        flag = "flag=unittests"
        extras = f"{token}&{flag}"
        return self._badge("codecov/c", branch, extras)

    def codefactor_badge(self, branch: str = "master") -> str:
        return self._badge("codefactor/grade", branch)

    def docstring_badge(self, coverage: str) -> str:
        if not coverage:
            coverage = "0%"
        value_str = coverage.strip().rstrip('%')
        try:
            value = float(value_str)
        except ValueError:
            value = 0.0
        value_int = round(value)
        if value_int < 50:
            color = "red"
        elif value_int < 70:
            color = "orange"
        elif value_int < 90:
            color = "yellow"
        else:
            color = "brightgreen"
        coverage_rounded = f"{value_int}%"
        coverage_encoded = coverage_rounded.replace("%", "%25")
        label = ""
        url = f"{self.shields}/badge/{label}-{coverage_encoded}-{color}?{STYLE}"
        return url

    def github_badge(self, workflow: str, branch: str = "") -> str:
        section = "github/actions/workflow/status"
        url = f"{self.shields}/{section}/{self.repo}/{workflow}?{LABEL}&{STYLE}"
        if branch:
            url += f"&branch={branch}"
        return url

    def github_badge_set(self, workflow: str, feature_branch: str) -> Dict[str, str]:
        return {
            "master": self.github_badge(workflow),
            "master_url": f"{GITHUB_WORKFLOWS}/{workflow}",
            "develop": self.github_badge(workflow, "develop"),
            "develop_url": f"{GITHUB_WORKFLOWS}/{workflow}",
            "feature": self.github_badge(workflow, feature_branch),
            "feature_url": f"{GITHUB_WORKFLOWS}/{workflow}",
        }


def make_codefactor_refs(badge_gen: BadgeGenerator, feature: str) -> str:
    return f"""
[codefactor-master]: {badge_gen.codefactor_badge('master')}
[codefactor-master-url]: {CODEFACTOR}/overview
[codefactor-develop]: {badge_gen.codefactor_badge('develop')}
[codefactor-develop-url]: {CODEFACTOR}/overview/develop
[codefactor-feature]: {badge_gen.codefactor_badge(feature)}
[codefactor-feature-url]: {CODEFACTOR}/overview/{feature}
""".strip()


def make_codecov_refs(badge_gen: BadgeGenerator, feature: str) -> str:
    return f"""
[codecov-master]: {badge_gen.codecov_badge('master')}
[codecov-master-url]: {CODECOV}
[codecov-develop]: {badge_gen.codecov_badge('develop')}
[codecov-develop-url]: {CODECOV}/branch/develop
[codecov-feature]: {badge_gen.codecov_badge(feature)}
[codecov-feature-url]: {CODECOV}/branch/{feature}
""".strip()


def read_coverage(path: str) -> str:
    if path and Path(path).exists():
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        for line in lines:
            if line.startswith("| TOTAL"):
                parts = line.split("|")
                if len(parts) >= 3:
                    percent = parts[-2].strip()
                    return percent
        # fallback: scan lines in reverse for "actual:"
        for line in reversed(lines):
            if "actual:" in line:
                # extract percentage value after "actual:"
                after_actual = line.split("actual:")[-1].strip()
                # extract percentage number from after_actual (e.g. " 85.0%")
                percent = after_actual.split()[0]
                return percent
    return ""


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a markdown table of status badges for diffraction-lib.")
    parser.add_argument("--output", default="BADGES.md", help="Output markdown file (default: BADGES.md)")
    parser.add_argument("--branch", default="unknown", help="Feature branch name (default: unknown)")
    parser.add_argument("--coverage-docstring-master", help="Path to docstring coverage file for master branch")
    parser.add_argument("--coverage-docstring-develop", help="Path to docstring coverage file for develop branch")
    parser.add_argument("--coverage-docstring-feature", help="Path to docstring coverage file for feature branch")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    feature = args.branch
    badge_gen = BadgeGenerator()

    doc_cov_master = read_coverage(args.coverage_docstring_master)
    doc_cov_develop = read_coverage(args.coverage_docstring_develop)
    doc_cov_feature = read_coverage(args.coverage_docstring_feature)

    header = f"| | master | develop | {feature} |\n|---|:---:|:---:|:---:|"

    rows: List[Tuple[str, str, str, str]] = [
        (
            "Code quality from CodeFactor.io",
            "[![codefactor-master]][codefactor-master-url]",
            "[![codefactor-develop]][codefactor-develop-url]",
            "[![codefactor-feature]][codefactor-feature-url]",
        ),
        (
            "Unit test coverage from Codecov.io",
            "[![codecov-master]][codecov-master-url]",
            "[![codecov-develop]][codecov-develop-url]",
            "[![codecov-feature]][codecov-feature-url]",
        ),
        (
            "Scan security",
            "[![scan-security-master]][scan-security-master-url]",
            "[![scan-security-develop]][scan-security-develop-url]",
            "[![scan-security-feature]][scan-security-feature-url]",
        ),
        (
            "Test code and package",
            "[![test-code-master]][test-code-master-url]",
            "[![test-code-develop]][test-code-develop-url]",
            "[![test-code-feature]][test-code-feature-url]",
        ),
        (
            "Test tutorials",
            "[![test-tutorials-master]][test-tutorials-master-url]",
            "[![test-tutorials-develop]][test-tutorials-develop-url]",
            "[![test-tutorials-feature]][test-tutorials-feature-url]",
        ),
        (
            "Docstring coverage with interrogate",
            f"![Docstring coverage]({badge_gen.docstring_badge(doc_cov_master)})",
            f"![Docstring coverage]({badge_gen.docstring_badge(doc_cov_develop)})",
            f"![Docstring coverage]({badge_gen.docstring_badge(doc_cov_feature)})",
        ),
        (
            "Build and deploy docs",
            "[![build-docs-master]][build-docs-master-url]",
            "[![build-docs-develop]][build-docs-develop-url]",
            "[![build-docs-feature]][build-docs-feature-url]",
        ),
        (
            "Publish to PyPI",
            "[![publish-pypi-master]][publish-pypi-master-url]",
            "",
            "",
        ),
        (
            "Test unpinned PyPI package",
            "[![test-package-pypi-master]][test-package-pypi-master-url]",
            "",
            "",
        ),
    ]

    badge_table_lines = [header]
    for label, master_badge, develop_badge, branch_badge in rows:
        badge_table_lines.append(f"| {label} | {master_badge} | {develop_badge} | {branch_badge} |")

    badge_table = "\n".join(badge_table_lines)

    # Build badge sets for workflows
    badge_sets = {
        "scan-security": badge_gen.github_badge_set("scan-security.yml", feature),
        "test-code": badge_gen.github_badge_set("test-code.yaml", feature),
        "test-tutorials": badge_gen.github_badge_set("test-tutorials.yaml", feature),
        "build-docs": badge_gen.github_badge_set("build-docs.yml", feature),
        "publish-pypi": badge_gen.github_badge_set("publish-pypi.yml", feature),
        "test-package-pypi": badge_gen.github_badge_set("test-package-pypi.yaml", feature),
    }

    references_lines = []

    # Add CodeFactor references
    references_lines.append(make_codefactor_refs(badge_gen, feature))
    references_lines.append("")
    # Add Codecov references
    references_lines.append(make_codecov_refs(badge_gen, feature))
    references_lines.append("")

    # Add GitHub workflow badge references
    for key, refs in badge_sets.items():
        references_lines.append(f"[{key}-master]: {refs['master']}")
        references_lines.append(f"[{key}-master-url]: {refs['master_url']}")
        references_lines.append(f"[{key}-develop]: {refs['develop']}")
        references_lines.append(f"[{key}-develop-url]: {refs['develop_url']}")
        references_lines.append(f"[{key}-feature]: {refs['feature']}")
        references_lines.append(f"[{key}-feature-url]: {refs['feature_url']}")
        references_lines.append("")

    references = "\n".join(line for line in references_lines if line.strip())

    content = f"{badge_table}\n\n{references}\n"

    Path(args.output).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()