<div align="center">
  <img src="https://raw.githubusercontent.com/delcenjo/PyRegex/main/assets/logo.png" alt="PyRegex Logo" width="200"/>
  <h1>🔍 PyRegex</h1>
  <p><strong>The Ultimate Enterprise CLI Toolkit for Regex Engineering, Security & Data Privacy</strong></p>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![Architecture: DDD](https://img.shields.io/badge/Architecture-DDD-orange.svg)]()

  <p>PyRegex has evolved into a massive, production-grade Compiler and Architecture Toolkit. Designed with strict Domain-Driven Design (DDD), it empowers engineers, DevOps, and Security researchers to build, audit, compile, and visualize complex Regular Expressions with absolute precision.</p>
</div>

---

## 🚀 The PyRegex Ecosystem

PyRegex is no longer just a matching tool. It is an **orchestration engine**.

*   **🛡️ AST Compiler Engine**: We don't just "execute" strings. PyRegex compiles your regex into a deep Abstract Syntax Tree (AST).
*   **🩺 Deterministic ReDoS Detection**: Ditch unreliable regex heuristics. PyRegex builds a true NFA via Thompson Construction and analyzes AST overlaps via bitsets to deterministically detect O(N²), O(N³), and O(2^N) vulnerabilities—even generating synthetic *evil input* to prove it.
*   **🎮 Live Terminal Playground**: Drop into `px play` for a massive, full-screen Terminal UI. Edit regex and test data in real-time with instant AST, native syntax highlighting, and live backtracking profiling!
*   **🤖 Nebula Assistant**: Drop into `px assistant` to interactively build, merge, test, and manipulate regex patterns using a **Hybrid Adaptive Architecture (AHA)**. Featuring dynamic registry-driven discovery with **16+ specialized categories** and a growing library of hundreds of integrated wizards.
*   **🌐 Compliance & Privacy**: Multiprocessing engines (`audit` and `mask`) to parallel process GBs of logs, anonymizing emails, phones, and credit cards instantly.
*   **🏗️ Infinitely Scalable Builders**: A massive, plug-and-play catalog system. Add new regex logic by simply dropping a YAML file into the `/catalog` directory—no code changes required.
*   **📊 Visual Flowcharts**: Export any raw regex directly into an ASCII syntax tree or a **Mermaid State Diagram** natively from the CLI.
*   **💾 Registry & Versioning**: Securely save, tag, merge, and export your complex logic locally or across CI/CD pipelines.

---

## 🛠 Installation

Clone the repository and install it in your virtual environment:

```bash
git clone https://github.com/delcenjo/PyRegex.git
cd PyRegex
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

*Note: PyRegex registers the `pyregex` command. You can also use the shorthand alias `px`.*

---

## 📖 The "Killer Feature" Engines

### 1. 🎓 The AST Explainer & Compiler (`explain`)
Don't guess what a regex does. Let the PyRegex Lexer & Parser map it for you. 

```bash
# Get a Natural Language translation, Big-O Security Score, and an ASCII Tree
px explain "^(a|b)*[0-9]{2,4}(?i)$" --verbose

# Export the internal syntax logic directly into a Mermaid Chart!
px explain "^(a|b)*[0-9]{2,4}(?i)$" --mermaid
```
*(PyRegex builds a true AST, offering native Linter suggestions like detecting redundant `(a|a)` paths).*

### 2. 🎮 Live Regex Playground (`play`)
A massive, split-panel full-screen Terminal UI for real-time regex engineering.

```bash
px play
```
*   **Live Translation**: See the semantic meaning of your regex as you type.
*   **Real-time Syntax Tree**: Watch the AST update instantly on every keystroke.
*   **Live Evaluation**: See all matching groups and spans against multi-line test data in real-time.
*   **Instant Backtrack Detection**: Get immediate feedback if you introduce catastrophic ReDoS vulnerabilities (O(N²), O(2^N)).
*   **📂 100GB+ Big Data File Mode**: Run `px play --file <path>` to analyze massive logs. Powered by a custom **O(1) Memory Sparse-Indexing Architecture**, it opens 100GB+ files instantly (`<10ms`) with microsecond random-access rendering, consuming less than 1MB of RAM. Fully cross-platform (Windows/Linux/macOS).

### 3. 🏷️ The Smart Alias System (`@names`)
Standardize your regex library. Instead of re-typing complex patterns, use namespaces.

```bash
# Use pre-defined patterns directly in px play or any command
# typing '@' in the regex panel opens the autocompletion menu
Pattern: ^User: (@username) - IP: (@ipv4)$
```
*   **Intelligent Autocomplete**: Deep integration in `px play` with descriptive hints.
*   **Inline Expansion**: Press `Ctrl+E` to instantly expand an alias into its raw regex for fine-tuning.
*   **Registry Sync**: Aliases are pulled directly from your local PyRegex Registry (`px save`).
*   **🔥 Nivel Dios (Composition)**: Join multiple aliases with `+` (e.g., `@log + @ip + @status`) to build massive, modular patterns with zero cognitive overhead. PyRegex handles operator precedence and logical isolation automatically.

### 4. 🤖 Nebula: The Hybrid Adaptive Assistant (`assistant` & `create`)
A state-of-the-art **Hybrid Adaptive Architecture (AHA)** for regex engineering, featuring lightning-fast `<200ms` startup times via lazy-module loading and dynamic AST parsing bypasses.

```bash
# Launch the full interactive assistant
px assistant

# Drop directly into the infinite-depth hierarchical category browser
px create
```

| Category | Description | Examples |
|:---|:---|:---|
| 🧑 **Personal** | Identity & PII | Email, Phone, SSN, Passport, DNI |
| 🌐 **Web** | Networking & Protocols | URL, IP, Domain, UUID, MAC, Hash |
| 📊 **Data** | Formats & Science | Coordinates, Chemistry, Scientific |
| 🖥️ **Systems** | DevOps & Logs | AWS, Docker, K8s, Logs, SSH, DB |
| 🏦 **Finance** | Banking & Tax | IBAN, SWIFT, Tax ID, Currency |
| 🛡️ **Security** | Auth & Secrets | JWT, API Key, SSH Key, OAuth |
| ⚖️ **Compliance** | Legal & Medical | ICD-10, ISO, Legal Citations |
| ... and **8+ more** | Dynamically registered | I18n, DevOps, Tools, Utils, etc. |

*   **[Dynamic CLI]**: The CLI dynamically builds its subparser hierarchy from the `CatalogRegistry`. Run `px <category> <entry> --help` to see automatically generated arguments from the YAML `config_schema`.
*   **[Infinite Hierarchies]**: Complex regex logic is organized into deep, nested folder trees (e.g., `web/networking/ipv4`), allowing clean domain separation and nested interactive TUI menus.
*   **[Hybrid 90/10 Logic]**: Standard workflows are driven by declarative YAML (90%), while complex logic is dynamically delegated to custom Python handlers (10%) for maximum flexibility.
*   **[Edit/Merge/History]**: Full support for interactive manipulation, prefix-trie merging, and undo/redo history.

### 4. 🛡️ Audit & Mask (Parallel Processing)
Scan gigabytes of files efficiently. PyRegex automatically distributes the workload using `ProcessPoolExecutor`.

```bash
# Scan a directory for all PII and Secrets (Parallel execution)
px audit --all ./repo --parallel

# Anonymize emails and phones by replacing them with realistic fake data
px mask pii production.log --mode fake --inplace
# (Modes available: redact, hash, replace, fake)
```

### 5. 🛡️ Sentinel Engine: Mass Unit Testing (`test`)
A complete declarative testing framework (like `jest` or `pytest`) explicitly for Regular Expressions, featuring Faker-driven Fuzzing and AST Code Coverage!

```bash
# Run all *.regex.yaml Test Suites dynamically checking code coverage
px test ./tests/ --coverage
```
*   **YAML Declarative Suites:** Define lists of `passes` and `fails` cleanly.
*   **AST Code Coverage:** Find out which branches of an alternation `(a|b)` were never tested!
*   **Synthetic Fuzzing:** The Sentinel automatically spawns hundreds of `Faker` emails, IPs, or passwords to stress-test your regex against false positives.
*   **Terminal UI:** Rich, multi-column validation table summaries.

### 6. ⏱️ Warp Profiler: Dynamic Fuzzing (`bench`)
A true performance laboratory. Proves the computational Big-O complexity of a regex empirically by injecting mutating payloads and tracking physical RAM/CPU ticks.

```bash
# Fuzz test a regex, record Memory/Time footprints, and export to a Chart.js HTML Dashboard
px bench -p "([a-zA-Z]+)*$" --fuzz-redos --export-html report.html
```
*   **ReDoS Fuzzer:** Uses Thompson NFA construction to find topological 'pump paths' and exponentially scale malicious payloads.
*   **Mathematical R²:** Calculates Least Squares regressions to prove O(1), O(N), O(N²), or O(2^N) execution graphs.
*   **HTML Dossiers:** Outputs standalone HTML files with sleek `Chart.js` scatter plots documenting the vulnerability.

---

## 📚 Complete Command Reference

PyRegex features a robust, plugin-based architecture for its commands:

| Command | Description |
| :--- | :--- |
| **`px play`** | Launches the split-panel full-screen Regex Playground UI. |
| **`px assistant`** | Launches the hyper-interactive Regex REPL environment. |
| **`px explain`** | Runs the Lexer/Parser to build an AST, Linter, and Mermaid graph. |
| **`px create`** | Interactively build patterns for Web, Cloud, Logs, DB, Security. |
| **`px test`** | **Sentinel Engine**: AST-Coverage Unit Testing & Fuzzing Framework. |
| **`px bench`** | **Warp Profiler**: Dynamic performance fuzzing and HTML Dashboards. |
| **`px audit`** | Mass-directory scanning for PII and exposed Secrets. |
| **`px mask`** | Mass-data anonymization and hashing for compliance mapping. |
| **`px validate`** | Multi-file schema and format enforcement. |
| **`px extract`** | Plucks explicit regex captures securely from large datasets. |
| **`px replace`** | Context-aware sed-like system replacement. |
| **`px transform`** | Applies pipelines of logic sequentially over files. |
| **`px generate`** | Inverse-compiler: Generates synthetic text *from* a regex pattern! |
| **`px learn`** | (Experimental) Infers common structures logically from input lists. |
| **`px save`** | Safely serialize a pattern directly into the internal Registry. |
| **`px list`** | Rich table and detailed views of the local stored Registry. |
| **`px delete`** | Safely trims the Registry. |
| **`px run`** | Rapid sandbox execution terminal. |
| **`px history`** | Complete audit log of your command session usage. |
| **`px config`** | Local environment configuration and toggle UI. |

*Quick NLP Action*: You can also leverage natural language fallback. Run `px "give me an email"` and PyRegex will map the semantic intent to the `EmailRegexBuilder`.

---

### 🏛️ Hybrid Adaptive Architecture (AHA)
PyRegex features a pristine architectural design adhering strictly to Domain-Driven Design (DDD) and the new **Hybrid Adaptive Architecture (AHA)**.

*   **Dynamic Discovery**: Registry-driven system for dynamic catalog loading (Infinite Scalability).
-   **90/10 Hybrid Routing**: 90% YAML-driven standard flows, 10% Python-delegated complex logic.
-   **Dynamic CLI Mapping**: Automated subparser and argument generation from catalog schemas.

The internal layers are rigorously separated to guarantee zero cyclic-dependencies and ensure maximum testability:

*   `src/pyregex/domain/` - The pure core logic (Core Regex Builders, Lexer, Parser, AST Models, **Catalog Registry**).
*   `src/pyregex/application/` - Business logic coordination (Services, Execution Controllers, Linter Engines).
*   `src/pyregex/infrastructure/` - External interfaces (Pattern Registry, JSON Repositories, Config Handlers).
*   `src/pyregex/presentation/` - Front-end IO (Dynamic CLI mappings, Command plugins, **AHA Wizards**).

---

## 🌍 Internationalization (i18n)
Everything—from the AST Narratives to the Assistant Prompts—is flawlessly translated.
```bash
px config --set language=es
```

---

## ⚖️ License
MIT License.
**PyRegex 2026** - *The Global Standard for Regex Engineering.*
