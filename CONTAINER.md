# AgentReady Container

Size-optimized container (683 MB) for headless environments and CI/CD.

## Quick Start

```bash
# Pull latest
podman pull ghcr.io/ambient-code/agentready:latest

# Create output directory
mkdir -p ~/agentready-reports

# Assess repository
podman run --rm \
  -v /path/to/repo:/repo:ro \
  -v ~/agentready-reports:/reports \
  ghcr.io/ambient-code/agentready:latest \
  assess /repo --output-dir /reports

# Open reports
open ~/agentready-reports/report-latest.html
```

## Usage

### Assess AgentReady Itself

```bash
# Clone AgentReady
git clone https://github.com/ambient-code/agentready /tmp/agentready

# Create output directory
mkdir -p ~/agentready-reports

# Run assessment
podman run --rm \
  -v /tmp/agentready:/repo:ro \
  -v ~/agentready-reports:/reports \
  ghcr.io/ambient-code/agentready:latest \
  assess /repo --output-dir /reports

# Open reports
open ~/agentready-reports/report-latest.html
```

### Assess Your Repository

```bash
# Create output directory
mkdir -p ./agentready-reports

# Local repository
podman run --rm \
  -v $(pwd):/repo:ro \
  -v $(pwd)/agentready-reports:/reports \
  ghcr.io/ambient-code/agentready:latest \
  assess /repo --output-dir /reports

# With additional options
podman run --rm \
  -v $(pwd):/repo:ro \
  -v $(pwd)/agentready-reports:/reports \
  ghcr.io/ambient-code/agentready:latest \
  assess /repo --output-dir /reports --verbose

# Exclude specific assessors
podman run --rm \
  -v $(pwd):/repo:ro \
  -v $(pwd)/agentready-reports:/reports \
  ghcr.io/ambient-code/agentready:latest \
  assess /repo --output-dir /reports -e type_annotations -e test_coverage
```

### Save Output Files

```bash
# Mount writable output directory
podman run --rm \
  -v /path/to/repo:/repo:ro \
  -v $(pwd)/reports:/reports \
  ghcr.io/ambient-code/agentready:latest \
  assess /repo --output-dir /reports

# Reports saved: report-*.html, report-*.md, assessment-*.json
```

## Available Tags

- `latest` - Latest stable release
- `2.13.0` - Specific version
- `2.13` - Major.minor version
- `2` - Major version

```bash
# Pin to specific version
podman pull ghcr.io/ambient-code/agentready:2.13.0
```

## Multi-Architecture Support

Supports both amd64 and arm64:

```bash
# Automatically pulls correct architecture
podman pull ghcr.io/ambient-code/agentready:latest
```

## Docker Compatibility

Replace `podman` with `docker`:

```bash
docker pull ghcr.io/ambient-code/agentready:latest
docker run --rm \
  -v $(pwd):/repo:ro \
  -v $(pwd)/agentready-reports:/reports \
  ghcr.io/ambient-code/agentready:latest \
  assess /repo --output-dir /reports
```

## Podman Rootless Mode

On **rootless Podman** (common on Fedora, RHEL, CentOS), additional flags are required to handle SELinux labeling, UID mapping, and Git security checks.

### Complete Command

```bash
podman run --rm -it \
  --user $(id -u):$(id -g) \
  --userns=keep-id \
  -e GIT_CONFIG_COUNT=1 \
  -e GIT_CONFIG_KEY_0=safe.directory \
  -e GIT_CONFIG_VALUE_0=/repo \
  -v /path/to/repo:/repo:ro,z \
  -v /path/to/reports:/reports:z \
  ghcr.io/ambient-code/agentready:latest \
  assess /repo --output-dir /reports
```

### Why These Flags?

| Flag | Purpose |
|------|---------|
| `--userns=keep-id` | Maps container UID to match your host UID, fixing permission mismatches |
| `--user $(id -u):$(id -g)` | Runs the container process as your host user |
| `GIT_CONFIG_*` | Tells Git to trust the mounted `/repo` directory (required for Git 2.35.2+) |
| `:z` (lowercase) | SELinux shared label - allows container access to mounted volumes |

### When Do I Need This?

Use the rootless Podman command if you encounter any of these errors:

- `Path '/repo' is not readable` (SELinux blocking access)
- `SHA is empty, possible dubious ownership` (Git security check)
- `PermissionError: [Errno 13] Permission denied` (UID mismatch)

### Note on SELinux Labels

- Use `:z` (lowercase) for shared volumes that multiple containers may access
- Use `:Z` (uppercase) for private volumes exclusive to one container
- Both options relabel the volume for SELinux access

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run AgentReady Assessment
  run: |
    mkdir -p reports
    docker pull ghcr.io/ambient-code/agentready:latest
    docker run --rm \
      -v ${{ github.workspace }}:/repo:ro \
      -v ${{ github.workspace }}/reports:/reports \
      ghcr.io/ambient-code/agentready:latest \
      assess /repo --output-dir /reports

- name: Upload reports
  uses: actions/upload-artifact@v4
  with:
    name: agentready-reports
    path: reports/
```

### GitLab CI

```yaml
agentready:
  image: ghcr.io/ambient-code/agentready:latest
  script:
    - mkdir -p reports
    - agentready assess . --output-dir reports
  artifacts:
    paths:
      - reports/
```

## Building Locally

```bash
# Clone repository
git clone https://github.com/ambient-code/agentready
cd agentready

# Build container
podman build -t agentready:local -f Containerfile.scratch .

# Test
podman run --rm agentready:local --version
```

## Technical Details

- **Base**: python:3.12-slim
- **Size**: 683 MB
- **User**: UID 1001 (non-root)
- **Source**: PyPI (always latest agentready release)
- **Output**: stdout/stderr (no volume mounts required)

## Troubleshooting

### Reports not accessible on host

Mount a writable output directory to save reports to your host filesystem:

```bash
mkdir -p ~/agentready-reports
podman run --rm \
  -v /repo:/repo:ro \
  -v ~/agentready-reports:/reports \
  ghcr.io/ambient-code/agentready:latest \
  assess /repo --output-dir /reports
```

Without the `-v ~/agentready-reports:/reports` mount, reports written to `/tmp` inside the container are destroyed when the container exits.

### Permission denied on mounted volumes

**On rootless Podman** (Fedora, RHEL, CentOS), see the [Podman Rootless Mode](#podman-rootless-mode) section for the complete solution.

**Quick fix for SELinux only** - add the `:z` label to volumes:

```bash
podman run --rm \
  -v $(pwd):/repo:ro,z \
  -v $(pwd)/agentready-reports:/reports:z \
  ghcr.io/ambient-code/agentready:latest \
  assess /repo --output-dir /reports
```

### Git "dubious ownership" error

If you see `SHA is empty, possible dubious ownership`, the container's Git doesn't trust the mounted repository. Add Git safe.directory configuration:

```bash
podman run --rm \
  -e GIT_CONFIG_COUNT=1 \
  -e GIT_CONFIG_KEY_0=safe.directory \
  -e GIT_CONFIG_VALUE_0=/repo \
  -v $(pwd):/repo:ro \
  -v $(pwd)/agentready-reports:/reports \
  ghcr.io/ambient-code/agentready:latest \
  assess /repo --output-dir /reports
```

For the complete solution addressing all rootless Podman issues, see [Podman Rootless Mode](#podman-rootless-mode).

## Links

- **Container Registry**: https://github.com/ambient-code/agentready/pkgs/container/agentready
- **Source Code**: https://github.com/ambient-code/agentready
- **PyPI Package**: https://pypi.org/project/agentready/
- **Documentation**: https://ambient-code.github.io/agentready/
