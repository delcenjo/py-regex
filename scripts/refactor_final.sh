#!/bin/bash
set -e

echo "🚀 Starting 10/10 DDD Refactor..."

# --- Stage 1: Minimalist CORE ---
echo "📦 Cleaning core/..."
# 1. Ensure core/shared/ exists
mkdir -p src/pyregex/core/shared/
# 2. Move items that should be in services (if they are still in core)
[ -f src/pyregex/core/shared/engine.py ] && mv src/pyregex/core/shared/engine.py src/pyregex/application/services/ || true
[ -f src/pyregex/core/shared/parser.py ] && mv src/pyregex/core/shared/parser.py src/pyregex/application/services/ || true
[ -f src/pyregex/core/shared/registry.py ] && mv src/pyregex/core/shared/registry.py src/pyregex/application/services/ || true
[ -f src/pyregex/core/shared/task_manager.py ] && mv src/pyregex/core/shared/task_manager.py src/pyregex/application/services/ || true

# 3. Delete leftover migrated files from core root (safety check)
rm -f src/pyregex/core/*.py 2>/dev/null || true
touch src/pyregex/core/__init__.py

# --- Stage 2: Unified Execution ---
echo "⚙️  Unifying Execution logic..."
mkdir -p src/pyregex/application/services/execution/
# Move worker to application (it's the service manager)
[ -f src/pyregex/infrastructure/execution/worker.py ] && mv src/pyregex/infrastructure/execution/worker.py src/pyregex/application/services/execution/ || true
# Remove duplicated execution logs/controllers
rm -rf src/pyregex/infrastructure/execution/audit/ 2>/dev/null || true
[ -f src/pyregex/infrastructure/execution/controller/execution_controller.py ] && rm -f src/pyregex/infrastructure/execution/controller/execution_controller.py || true

# --- Stage 3: Aplanando Registry ---
echo "📂 Flattening Infrastructure/Registry..."
mkdir -p src/pyregex/infrastructure/registry/commands/
# Move nested list/delete to a flatter structure
[ -d src/pyregex/infrastructure/registry/list ] && mv src/pyregex/infrastructure/registry/list src/pyregex/infrastructure/registry/commands/ || true
[ -d src/pyregex/infrastructure/registry/delete ] && mv src/pyregex/infrastructure/registry/delete src/pyregex/infrastructure/registry/commands/ || true

# Move registry controller to application services (where it belong)
[ -f src/pyregex/infrastructure/registry/controller/registry_controller.py ] && mv src/pyregex/infrastructure/registry/controller/registry_controller.py src/pyregex/application/services/ || true

# --- Stage 4: Domain Purity (Explain & Registry Schemas) ---
echo "🧠 Improving Domain Purity..."
# Move explain controller to presentation (or application)
[ -f src/pyregex/domain/explain/controller/explain_controller.py ] && mv src/pyregex/domain/explain/controller/explain_controller.py src/pyregex/application/services/explain_controller.py || true

# --- Stage 5: Final Cleanup ---
echo "🧹 Final Cleanup..."
find src -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "✅ Refactor commands executed. Now running import fix..."
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 scripts/fix_imports_ddd.py

echo "✨ 10/10 Refactor COMPLETE."
