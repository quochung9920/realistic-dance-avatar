param(
    [Parameter(Mandatory=$true)]
    [string]$RepoUrl
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path .git)) {
    git init -b main
}

git add -- .github .gitignore LICENSE README.md app.py blender config input models output pyproject.toml realistic_dance_avatar requirements-dev.txt requirements.txt scripts tests

$changes = git status --porcelain
if ($changes) {
    git commit -m "Initial realistic dance avatar MVP"
}

$remote = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    git remote add origin $RepoUrl
} elseif ($remote -ne $RepoUrl) {
    git remote set-url origin $RepoUrl
}

git push -u origin main
