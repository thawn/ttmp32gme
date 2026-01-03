# GitHub Actions Workflows

This directory contains the CI/CD workflows for the ttmp32gme project.

## Docker Workflows

The Docker deployment workflows are designed to build, test, and deploy Docker containers efficiently with minimal duplication.

### Workflow Structure

The Docker workflows use a **reusable workflow pattern** to avoid duplication:

1. **`docker-build-test.yml`** (Reusable Workflow)
   - Contains all the common logic for building and testing Docker images
   - Can be called from other workflows
   - Optionally pushes to Docker Hub when `push_to_registry: true`

2. **`docker-pr.yml`** (Pull Request Workflow)
   - Triggered on pull requests that modify Docker-related files
   - Calls `docker-build-test.yml` with `push_to_registry: false`
   - Only builds and tests the image, does not push to registry

3. **`docker-release.yml`** (Release Workflow)
   - Triggered when a new release is published
   - Can also be manually triggered via workflow_dispatch
   - Calls `docker-build-test.yml` with `push_to_registry: true`
   - Builds, tests, and pushes the image to Docker Hub

### Docker Hub Credentials

For the release workflow to push images to Docker Hub, you need to configure the following secrets in your repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add the following secrets:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username
   - `DOCKERHUB_TOKEN`: Your Docker Hub access token (create at https://hub.docker.com/settings/security)

### Testing Strategy

The Dockerfile uses a **multi-stage build** with a dedicated test stage:

1. **Test Stage**: Runs unit tests during the Docker build process
   - Installs test dependencies
   - Runs pytest unit tests (`tests/unit/`)
   - Build fails if tests fail

2. **Production Stage**: Creates the final production image
   - Does not include test dependencies
   - Smaller final image size

The workflows perform the following tests:

1. **Build and Test**: Builds the test stage which runs unit tests
2. **Build Production**: Builds the production stage for the final image
3. **Container Start Test**: Verifies the container starts without errors
4. **Health Check**: Confirms the web application responds on port 8080
5. **Basic Functionality**: Tests that the main page loads with expected content

### Triggering Workflows

#### Automatic Triggers

- **PR Workflow**: Automatically runs when you create or update a PR that modifies:
  - Files in `resources/build/docker/`
  - `Dockerfile`, `docker-compose.yml`, or `build-docker.sh`
  - Source code in `src/`
  - `pyproject.toml` or Docker workflow files

- **Release Workflow**: Automatically runs when you publish a new release on GitHub

#### Manual Triggers

You can manually trigger the release workflow:

1. Go to **Actions** → **Docker Release**
2. Click **Run workflow**
3. Specify the tag name (e.g., `v1.2.3` or `latest`)

### Image Tagging Strategy

The workflows use the following tagging strategy:

- **PR builds**: `pr-{PR_NUMBER}` (not pushed to registry)
- **Release builds**:
  - Main tag: The release tag name (e.g., `v1.2.3`)
  - Semantic version tags: `1.2.3`, `1.2`, `1`
  - Git SHA tag: `git-{SHORT_SHA}`
  - `latest` tag (if releasing from main branch)

### Local Testing

To test the Docker build locally before pushing:

```bash
# Build the image
./build-docker.sh

# Run the container
docker run -d -p 8080:8080 --name ttmp32gme-test ttmp32gme

# Test it
curl http://localhost:8080/

# Clean up
docker stop ttmp32gme-test
docker rm ttmp32gme-test
```

## Other Workflows

- **`python-tests.yml`**: Unit and integration tests for Python code
- **`javascript-tests.yml`**: Frontend JavaScript tests
- **`e2e-tests.yml`**: End-to-end Selenium tests (manual trigger)
- **`docs.yml`**: Documentation building and deployment
- **`pre-commit.yml`**: Pre-commit hook validations
- **`copilot-setup-steps.yml`**: GitHub Copilot setup automation
