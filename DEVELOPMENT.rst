Development Workflow
====================

This document outlines the development workflow for this project, which involves

- Git for version control
- The `Git Flow model`<https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow> as a development philosophy.
- Pytest for unit testing
- PyPI for package distribution
- GitHub Actions for continuous integration and deployment

Git Flow
--------

The Git Flow model is a branching strategy for Git, designed to facilitate
parallel development and collaboration. It defines a strict branching model that
includes two main branches with infinite lifetimes: `master` and `develop`. The
`master` branch contains production-ready code, while the `develop` branch
serves as an integration branch for features.

Feature (`feature/xyz`) branches are created from `develop` and are merged back
into `develop` when complete. Release (`release/1.0.2`) branches are created
from `develop` when preparing for a new production release, allowing for final
bug fixes and preparation. Once a release branch is ready, it tagged (`v1.0.2`)
with the appropriate semantic versioning system then it is merged into both
`master` and `develop`.

Hotfix branches are created from `master` to address critical issues in
production and are merged back into both `master` and `develop` after the fix.

This model provides a robust framework for managing larger projects
with multiple developers, ensuring a clean and organized workflow.

.. image:: https://wac-cdn.atlassian.com/dam/jcr:cc0b526e-adb7-4d45-874e-9bcea9898b4a/04%20Hotfix%20branches.svg?cdnVersion=2493

1. **Initialize Git Flow**:
    Initialize Git Flow in your repository if you haven't already:
    ```
    git flow init
    ```
    Select the following settings:

    Branch name for production releases: [master]               // Enter - (default)
    Branch name for "next release" development: [develop]       // Enter - (default)
    Feature branches? [feature/]                                // Enter - (default)
    Bugfix branches? [bugfix/]                                  // Enter - (default)
    Release branches? [release/]                                // Enter - (default)
    Hotfix branches? [hotfix/]                                  // Enter - (default)
    Support branches? [support/]                                // Enter - (default)
    Version tag prefix? []                                      // Use 'v' then Enter
    Hooks and filters directory? [C:/Users/username/.git/hooks] // Enter - (default)

    Git Flow should now be initialized on your PC.

2. **Feature Branches**:

    Feature branches should have a descriptive name that reflects the feature
    being added, e.g., `feature/new-feature`. Branches are created from
    `develop` and merged back into `develop` when a feature is complete. Below a
    short tutorial.

    - Create a new feature branch from `develop`:
      ```
      git flow feature start <feature-name>
      ```
    - Work on your feature and commit changes:
      ```
      git add .
      git commit -m "Add new feature"
      ```
    - When the feature is complete, finish the feature branch:
      ```
      git flow feature finish <feature-name>
      ```
      This will automatically merge it into `develop` and remove the feature branch.

3. **Release Branches**:

    A release branch is created when a new production release is being prepared.
    The branch name contains the release version, e.g., `release/1.0.0`. A
    release branch is created from the `develop` branch and upon completion will
    get tagged, and merged to both the `master` and `develop` branches. The only
    way to push to `master` is through a release branch, except if a `hotfix` if
    needed.

    - Create a release branch from `develop`:
      ```
      git flow release start <release-version>
      ```
    - Prepare the release (update version number, changelog, etc.):
      ```
      git add .
      git commit -m "Prepare release <release-version>"
      ```
    - Finish the release branch, which tags it and merges it into `master` and `develop`:
      ```
      git flow release finish <release-version>
      ```

4. **Hotfix Branches**:

    Hotfix branches are used to address critical issues in production. They are
    not usually planned and are created from the `master` branch such as
    `hotfix/1.0.1`. Once complete, they are merged back into both `master` and
    `develop`. Hotfix branches are also tagged, e.g. `v1.0.1`.

    - Create a hotfix branch from `master`:
      ```
      git flow hotfix start <hotfix-name>
      ```
    - Apply the hotfix and commit changes:
      ```
      git add .
      git commit -m "Fix critical issue"
      ```
    - Finish the hotfix branch, which merges it into `master` and `develop`:
      ```
      git flow hotfix finish <hotfix-name>
      ```

Testing, Continuous Integration and PyPI Deployment
---------------------------------------------------

All code is be tested using the `pytest` framework and should and have a minimum
test coverage of 80%. Continuous integration (CI) is set up using GitHub Actions
to run tests on every push to the repository. The CI workflow is defined in
`.github/workflows/CI-CD.yaml`. The workflow runs the tests using multiple Python
versions and reports the global test coverage using `codecov`. The testing also
includes a linting step using `flake8` to ensure code consistency and `isort` to
ensure import order consistency.

The workflow also includes deployment to PyPI, which is triggered when a new
tagged release or hotfix is created. Deployment will NOT occur if on a
non-tagged push, if the tests fail, or if the version number is not updated.

An example workflow for creating a new feature followed by a new release would look
as follows:

- Create a new feature branch: `git flow feature start new-feature`
- Write the feature then finalize the feature branch: `git flow feature finish new-feature`
- Create a new release branch: `git flow release start 1.1.0`. The current
  package version can be checked by using `pip show adsorption_file_parser`.
- Finalize any last modifications and solve any CI issues. There is no need to
  manually update the version number - it will be determined from the tag name.
  WARNING: release will fail if all CI tests do not pass.
- Finish the release `git flow release finish 1.1.0`. Push everything to GH,
  also specifying tags `git push && git push --tags`.
- Check that the CI/CD process has finished on GH.

By following this workflow, you can ensure a structured development process and
a smooth deployment to PyPI.
