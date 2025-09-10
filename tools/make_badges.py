import os

def main():
    feature = os.getenv("CI_BRANCH", "unknown")

    header = "| | master | develop | {} |\n|---|:---:|:---:|:---:|".format(feature)

    rows = [
        ("Code quality from CodeFactor",
         "[![codefactor-master]][codefactor-master-url]",
         "[![codefactor-develop]][codefactor-develop-url]",
         "[![codefactor-feature]][codefactor-feature-url]"),
        ("Unit test coverage from Codecov",
         "[![codecov-master]][codecov-master-url]",
         "[![codecov-develop]][codecov-develop-url]",
         "[![codecov-feature]][codecov-feature-url]"),
        ("Scan security",
         "[![scan-security-master]][scan-security-master-url]",
         "[![scan-security-develop]][scan-security-develop-url]",
         "[![scan-security-feature]][scan-security-feature-url]"),
        ("Test code and package",
         "[![test-code-master]][test-code-master-url]",
         "[![test-code-develop]][test-code-develop-url]",
         "[![test-code-feature]][test-code-feature-url]"),
        ("Test tutorials",
         "[![test-tutorials-master]][test-tutorials-master-url]",
         "[![test-tutorials-develop]][test-tutorials-develop-url]",
         "[![test-tutorials-feature]][test-tutorials-feature-url]"),
        ("Build and deploy docs",
         "[![build-docs-master]][build-docs-master-url]",
         "[![build-docs-develop]][build-docs-develop-url]",
         "[![build-docs-feature]][build-docs-feature-url]"),
        ("Publish to PyPI",
         "[![publish-pypi]][publish-pypi-url]",
         "",
         ""),
        ("Test unpinned PyPI package",
         "[![test-package-pypi]][test-package-pypi-url]",
         "",
         ""),
    ]

    badge_table_lines = [header]
    for label, master_badge, develop_badge, branch_badge in rows:
        badge_table_lines.append(f"| {label} | {master_badge} | {develop_badge} | {branch_badge} |")

    badge_table = "\n".join(badge_table_lines)

    github_workflows = 'https://github.com/easyscience/diffraction-lib/actions/workflows'
    codefactor = 'https://www.codefactor.io/repository/github/easyscience/diffraction-lib'
    codecov = 'https://codecov.io/gh/EasyScience/diffraction-lib'

    shields = 'https://img.shields.io'
    repo = 'easyscience/diffraction-lib'
    style = 'style=for-the-badge'
    label = 'label='

    def badge(section, branch, extras=''):
        vsc_type = 'github'
        url = f'{shields}/{section}/{vsc_type}/{repo}/{branch}?{label}&{style}'
        if extras:
            url += f'&{extras}'
        return url

    def codecov_badge(branch='master'):
        section = 'codecov/c'
        token = 'token=qtsB5Q5BXO'
        flag = 'flag=unittests'
        extras = f'{token}&{flag}'
        url = badge(section, branch, extras)
        return url

    def codefactor_badge(branch='master'):
        section = 'codefactor/grade'
        url = badge(section, branch)
        return url

    def github_badge(workflow, branch='master'):
        section = 'github/actions/workflow/status'
        url = f'{shields}/{section}/{repo}/{workflow}?branch={branch}&{label}&{style}'
        return url



    references = f"""
[codefactor-master]: {codefactor_badge('master')}
[codefactor-master-url]: {codefactor}/overview
[codefactor-develop]: {codefactor_badge('develop')}
[codefactor-develop-url]: {codefactor}/overview/develop
[codefactor-feature]: {codefactor_badge(feature)}
[codefactor-feature-url]: {codefactor}/overview/{feature}

[codecov-master]: {codecov_badge('master')}
[codecov-master-url]: {codecov}
[codecov-develop]: {codecov_badge('develop')}
[codecov-develop-url]: {codecov}/branch/develop
[codecov-feature]: {codecov_badge(feature)}
[codecov-feature-url]: {codecov}/branch/{feature}

[scan-security-master]: {github_badge('scan-security.yml', 'master')}
[scan-security-master-url]: {github_workflows}/scan-security.yml
[scan-security-develop]: {github_badge('scan-security.yml', 'develop')}
[scan-security-develop-url]: {github_workflows}/scan-security.yml
[scan-security-feature]: {github_badge('scan-security.yml', feature)}
[scan-security-feature-url]: {github_workflows}/scan-security.yml

[test-code-master]: {github_badge('test-code.yaml', 'master')}
[test-code-master-url]: {github_workflows}/test-code.yaml
[test-code-develop]: {github_badge('test-code.yaml', 'develop')}
[test-code-develop-url]: {github_workflows}/test-code.yaml
[test-code-feature]: {github_badge('test-code.yaml', feature)}
[test-code-feature-url]: {github_workflows}/test-code.yaml

[test-tutorials-master]: {github_badge('test-tutorials.yaml', 'master')}
[test-tutorials-master-url]: {github_workflows}/test-tutorials.yaml
[test-tutorials-develop]: {github_badge('test-tutorials.yaml', 'develop')}
[test-tutorials-develop-url]: {github_workflows}/test-tutorials.yaml
[test-tutorials-feature]: {github_badge('test-tutorials.yaml', feature)}
[test-tutorials-feature-url]: {github_workflows}/test-tutorials.yaml

[build-docs-master]: {github_badge('build-docs.yml', 'master')}
[build-docs-master-url]: {github_workflows}/build-docs.yml
[build-docs-develop]: {github_badge('build-docs.yml', 'develop')}
[build-docs-develop-url]: {github_workflows}/build-docs.yml
[build-docs-feature]: {github_badge('build-docs.yml', feature)}
[build-docs-feature-url]: {github_workflows}/build-docs.yml

[publish-pypi]: {github_badge('publish-pypi.yml', 'master')}
[publish-pypi-url]: {github_workflows}/publish-pypi.yml

[test-package-pypi]: {github_badge('test-package-pypi.yaml', 'master')}
[test-package-pypi-url]: {github_workflows}/test-package-pypi.yaml
""".strip()

    content = f"{badge_table}\n\n{references}\n"

    with open("BADGES.md", "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()