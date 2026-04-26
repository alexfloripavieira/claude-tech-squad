from __future__ import annotations

import json
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict


ROUTING_TABLE: dict[str, dict[str, str]] = {
    "django": {
        "pm_agent": "django-pm",
        "techlead_agent": "django-tech-lead",
        "backend_agent": "django-backend",
        "frontend_agent": "django-frontend",
        "reviewer_agent": "code-reviewer",
        "qa_agent": "qa-tester",
    },
    "react": {
        "pm_agent": "pm",
        "techlead_agent": "techlead",
        "backend_agent": "backend-dev",
        "frontend_agent": "react-developer",
        "reviewer_agent": "reviewer",
        "qa_agent": "qa-tester",
    },
    "vue": {
        "pm_agent": "pm",
        "techlead_agent": "techlead",
        "backend_agent": "backend-dev",
        "frontend_agent": "vue-developer",
        "reviewer_agent": "reviewer",
        "qa_agent": "qa-tester",
    },
    "typescript": {
        "pm_agent": "pm",
        "techlead_agent": "techlead",
        "backend_agent": "backend-dev",
        "frontend_agent": "typescript-developer",
        "reviewer_agent": "reviewer",
        "qa_agent": "qa-tester",
    },
    "javascript": {
        "pm_agent": "pm",
        "techlead_agent": "techlead",
        "backend_agent": "backend-dev",
        "frontend_agent": "javascript-developer",
        "reviewer_agent": "reviewer",
        "qa_agent": "qa-tester",
    },
    "python": {
        "pm_agent": "pm",
        "techlead_agent": "techlead",
        "backend_agent": "python-developer",
        "frontend_agent": "frontend-dev",
        "reviewer_agent": "reviewer",
        "qa_agent": "qa",
    },
    "go": {
        "pm_agent": "pm",
        "techlead_agent": "techlead",
        "backend_agent": "backend-dev",
        "frontend_agent": "frontend-dev",
        "reviewer_agent": "reviewer",
        "qa_agent": "qa",
    },
    "rust": {
        "pm_agent": "pm",
        "techlead_agent": "techlead",
        "backend_agent": "backend-dev",
        "frontend_agent": "frontend-dev",
        "reviewer_agent": "reviewer",
        "qa_agent": "qa",
    },
    "java": {
        "pm_agent": "pm",
        "techlead_agent": "techlead",
        "backend_agent": "backend-dev",
        "frontend_agent": "frontend-dev",
        "reviewer_agent": "reviewer",
        "qa_agent": "qa",
    },
    "ruby": {
        "pm_agent": "pm",
        "techlead_agent": "techlead",
        "backend_agent": "backend-dev",
        "frontend_agent": "frontend-dev",
        "reviewer_agent": "reviewer",
        "qa_agent": "qa",
    },
    "php": {
        "pm_agent": "pm",
        "techlead_agent": "techlead",
        "backend_agent": "backend-dev",
        "frontend_agent": "frontend-dev",
        "reviewer_agent": "reviewer",
        "qa_agent": "qa",
    },
    "dotnet": {
        "pm_agent": "pm",
        "techlead_agent": "techlead",
        "backend_agent": "backend-dev",
        "frontend_agent": "frontend-dev",
        "reviewer_agent": "reviewer",
        "qa_agent": "qa",
    },
    "elixir": {
        "pm_agent": "pm",
        "techlead_agent": "techlead",
        "backend_agent": "backend-dev",
        "frontend_agent": "frontend-dev",
        "reviewer_agent": "reviewer",
        "qa_agent": "qa",
    },
    "generic": {
        "pm_agent": "pm",
        "techlead_agent": "techlead",
        "backend_agent": "backend-dev",
        "frontend_agent": "frontend-dev",
        "reviewer_agent": "reviewer",
        "qa_agent": "qa",
    },
}

EXCLUDE_DIRS = {
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    "vendor",
    "_build",
}

MAX_SCAN_DEPTH = 3
MAX_AI_FILES = 200


@dataclass
class StackResult:
    stack: str = "generic"
    ai_feature: bool = False
    routing: dict[str, str] = field(default_factory=dict)
    lint_profile: str = "none-detected"
    lint_tools: list[str] = field(default_factory=list)
    test_command: str = ""
    build_command: str = ""
    lint_command: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _find_file(root: Path, filename: str, max_depth: int = MAX_SCAN_DEPTH) -> Path | None:
    try:
        if (root / filename).exists():
            return root / filename
    except (PermissionError, OSError):
        pass

    for child in _iter_dirs(root, max_depth, current_depth=0):
        try:
            candidate = child / filename
            if candidate.exists():
                return candidate
        except (PermissionError, OSError):
            continue
    return None


def _find_all_files(root: Path, filename: str, max_depth: int = MAX_SCAN_DEPTH) -> list[Path]:
    found = []
    try:
        if (root / filename).exists():
            found.append(root / filename)
    except (PermissionError, OSError):
        pass

    for child in _iter_dirs(root, max_depth, current_depth=0):
        try:
            candidate = child / filename
            if candidate.exists():
                found.append(candidate)
        except (PermissionError, OSError):
            continue
    return found


def _iter_dirs(root: Path, max_depth: int, current_depth: int):
    if current_depth >= max_depth:
        return
    try:
        for entry in root.iterdir():
            if entry.is_dir() and entry.name not in EXCLUDE_DIRS and not entry.name.startswith("."):
                yield entry
                yield from _iter_dirs(entry, max_depth, current_depth + 1)
    except PermissionError:
        return


def _read_safe(path: Path) -> str:
    try:
        return path.read_text(errors="ignore")
    except OSError:
        return ""


def detect_stack(project_root: Path) -> StackResult:
    result = StackResult()

    manage_py = _find_file(project_root, "manage.py")
    package_json_path = _find_file(project_root, "package.json")
    tsconfig_path = _find_file(project_root, "tsconfig.json")
    pyproject_path = _find_file(project_root, "pyproject.toml")
    requirements_path = _find_file(project_root, "requirements.txt")
    go_mod_path = _find_file(project_root, "go.mod")
    cargo_toml_path = _find_file(project_root, "Cargo.toml")
    pom_xml_path = _find_file(project_root, "pom.xml")
    build_gradle_path = _find_file(project_root, "build.gradle")
    gemfile_path = _find_file(project_root, "Gemfile")
    composer_path = _find_file(project_root, "composer.json")
    mix_exs_path = _find_file(project_root, "mix.exs")

    csproj_files = list(project_root.glob("*.csproj")) + list(project_root.glob("*.sln"))
    if not csproj_files:
        for child in _iter_dirs(project_root, 2, 0):
            csproj_files.extend(child.glob("*.csproj"))
            csproj_files.extend(child.glob("*.sln"))
            if csproj_files:
                break

    package_json_data = {}
    if package_json_path:
        try:
            package_json_data = json.loads(package_json_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    deps = package_json_data.get("dependencies", {})
    dev_deps = package_json_data.get("devDependencies", {})
    all_deps = {**deps, **dev_deps}

    has_django = False
    for p in _find_all_files(project_root, "pyproject.toml", 2):
        has_django = has_django or "django" in _read_safe(p).lower()
    for p in _find_all_files(project_root, "requirements.txt", 2):
        has_django = has_django or "django" in _read_safe(p).lower()

    if manage_py and has_django:
        result.stack = "django"
    elif "react" in deps:
        result.stack = "react"
    elif "vue" in deps:
        result.stack = "vue"
    elif "next" in deps:
        result.stack = "react"
    elif "nuxt" in deps:
        result.stack = "vue"
    elif tsconfig_path or "typescript" in all_deps:
        result.stack = "typescript"
    elif package_json_path and package_json_data:
        result.stack = "javascript"
    elif go_mod_path:
        result.stack = "go"
    elif cargo_toml_path:
        result.stack = "rust"
    elif mix_exs_path:
        result.stack = "elixir"
    elif pom_xml_path or build_gradle_path:
        result.stack = "java"
    elif gemfile_path:
        result.stack = "ruby"
    elif composer_path:
        result.stack = "php"
    elif csproj_files:
        result.stack = "dotnet"
    elif pyproject_path or requirements_path:
        result.stack = "python"

    result.routing = ROUTING_TABLE.get(result.stack, ROUTING_TABLE["generic"])

    _detect_commands(
        project_root,
        result,
        package_json_data,
        go_mod_path,
        cargo_toml_path,
        pom_xml_path,
        build_gradle_path,
        gemfile_path,
        composer_path,
        csproj_files,
    )
    _detect_lint_profile(project_root, result)
    _detect_ai_feature(project_root, result)

    return result


def _detect_commands(
    root: Path,
    result: StackResult,
    pkg: dict,
    go_mod: Path | None,
    cargo: Path | None,
    pom: Path | None,
    gradle: Path | None,
    gemfile: Path | None,
    composer: Path | None,
    csproj: list[Path],
) -> None:
    makefile = _find_file(root, "Makefile", 1)
    if makefile:
        content = _read_safe(makefile)
        if re.search(r"^test\s*:", content, re.MULTILINE):
            result.test_command = "make test"
        if re.search(r"^build\s*:", content, re.MULTILINE):
            result.build_command = "make build"
        if re.search(r"^lint\s*:", content, re.MULTILINE):
            result.lint_command = "make lint"

    scripts = pkg.get("scripts", {})
    if not result.test_command and "test" in scripts:
        result.test_command = "npm test"
    if not result.build_command and "build" in scripts:
        result.build_command = "npm run build"
    if not result.lint_command and "lint" in scripts:
        result.lint_command = "npm run lint"

    if not result.test_command:
        if _find_file(root, "pyproject.toml", 2):
            content = _read_safe(_find_file(root, "pyproject.toml", 2))
            if "pytest" in content.lower():
                result.test_command = "pytest"
        if go_mod:
            result.test_command = result.test_command or "go test ./..."
        if cargo:
            result.test_command = result.test_command or "cargo test"
        if pom:
            result.test_command = result.test_command or "mvn test"
        if gradle:
            result.test_command = result.test_command or "./gradlew test"
        if gemfile:
            result.test_command = result.test_command or "bundle exec rspec"
        if composer:
            result.test_command = result.test_command or "vendor/bin/phpunit"
        if csproj:
            result.test_command = result.test_command or "dotnet test"

    if not result.build_command:
        if go_mod:
            result.build_command = "go build ./..."
        if cargo:
            result.build_command = result.build_command or "cargo build"
        if pom:
            result.build_command = result.build_command or "mvn package"
        if gradle:
            result.build_command = result.build_command or "./gradlew build"
        if csproj:
            result.build_command = result.build_command or "dotnet build"

    if not result.lint_command:
        if go_mod:
            result.lint_command = "golangci-lint run"
        if cargo:
            result.lint_command = result.lint_command or "cargo clippy --all-targets -- -D warnings"
        if pom:
            result.lint_command = result.lint_command or "mvn checkstyle:check"
        if csproj:
            result.lint_command = result.lint_command or "dotnet format --verify-no-changes"
        if gemfile:
            result.lint_command = result.lint_command or "bundle exec rubocop"
        if composer:
            result.lint_command = result.lint_command or "vendor/bin/phpstan analyse"


def _detect_lint_profile(root: Path, result: StackResult) -> None:
    tools = []

    ruff_toml = _find_file(root, "ruff.toml", 2)
    ruff_dot = _find_file(root, ".ruff.toml", 2)
    pyproject = _find_file(root, "pyproject.toml", 2)
    if ruff_toml or ruff_dot:
        tools.append("ruff")
    elif pyproject and "ruff" in _read_safe(pyproject).lower():
        tools.append("ruff")

    lint_signals = [
        (".eslintrc", "eslint"),
        (".eslintrc.js", "eslint"),
        (".eslintrc.json", "eslint"),
        ("eslint.config.js", "eslint"),
        ("eslint.config.mjs", "eslint"),
        ("eslint.config.ts", "eslint"),
        (".prettierrc", "prettier"),
        (".prettierrc.json", "prettier"),
        ("prettier.config.js", "prettier"),
        ("biome.json", "biome"),
        ("biome.jsonc", "biome"),
        (".flake8", "flake8"),
        ("mypy.ini", "mypy"),
        (".mypy.ini", "mypy"),
        (".golangci.yml", "golangci-lint"),
        (".golangci.yaml", "golangci-lint"),
        ("clippy.toml", "clippy"),
        (".clippy.toml", "clippy"),
        (".rubocop.yml", "rubocop"),
        ("phpstan.neon", "phpstan"),
        ("phpstan.neon.dist", "phpstan"),
        (".credo.exs", "credo"),
        (".editorconfig", "editorconfig"),
        ("checkstyle.xml", "checkstyle"),
        (".scalafmt.conf", "scalafmt"),
        (".ktlint", "ktlint"),
        ("swiftlint.yml", "swiftlint"),
        (".swiftlint.yml", "swiftlint"),
    ]

    for filename, tool in lint_signals:
        if tool not in tools and _find_file(root, filename, 2):
            tools.append(tool)

    if pyproject and "black" in _read_safe(pyproject).lower() and "black" not in tools:
        tools.append("black")
    if pyproject and "isort" in _read_safe(pyproject).lower() and "isort" not in tools:
        tools.append("isort")

    if tools:
        result.lint_tools = tools
        result.lint_profile = ", ".join(tools)


AI_PATTERNS = [
    "openai",
    "anthropic",
    "langchain",
    "llamaindex",
    "llama_index",
    "cohere",
    "huggingface",
    "transformers",
    "chromadb",
    "pinecone",
    "weaviate",
    "pgvector",
    "faiss",
    "qdrant",
    "ollama",
    "mistralai",
    "google.generativeai",
    "vertexai",
    "bedrock",
    "together_ai",
    "groq",
    "replicate",
    "vllm",
    "mlflow",
]

AI_SOURCE_EXTENSIONS = {"*.py", "*.ts", "*.js", "*.go", "*.rs", "*.java", "*.rb", "*.php", "*.ex", "*.exs", "*.cs"}


def _detect_ai_feature(root: Path, result: StackResult) -> None:
    files_checked = 0
    for ext in AI_SOURCE_EXTENSIONS:
        for path in root.rglob(ext):
            if files_checked >= MAX_AI_FILES:
                return
            if any(part in EXCLUDE_DIRS for part in path.parts):
                continue
            files_checked += 1
            content = _read_safe(path).lower()
            if not content:
                continue
            for pattern in AI_PATTERNS:
                if pattern in content:
                    result.ai_feature = True
                    return
