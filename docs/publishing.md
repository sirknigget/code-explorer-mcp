# Publishing

This repository is set up for PyPI publishing through GitHub Actions trusted publishing.

## One-time setup

1. Push this repository to GitHub.
2. Create the package on PyPI if you have not published it before.
3. In PyPI, configure a trusted publisher for this repository:
   - owner: your GitHub owner or organization
   - repository: this repository name
   - workflow: `.github/workflows/publish-pypi.yml`
   - environment: `pypi`
4. In GitHub, create an environment named `pypi`.

## Release flow

1. Update the version in `pyproject.toml`.
2. Commit and push the change.
3. Create a GitHub release.
4. The `Publish to PyPI` workflow builds the sdist and wheel and publishes them to PyPI.

## Manual trigger

You can also run the workflow manually from the GitHub Actions tab with `workflow_dispatch`.

## Notes

- TypeScript parsing still requires users to install Node.js and run `code-explorer-node-setup` after package installation.
- The workflow uses PyPI trusted publishing via GitHub's OIDC token, so no long-lived PyPI API token is needed in GitHub secrets.
