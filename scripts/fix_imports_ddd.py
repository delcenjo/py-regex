import os
import re

mapping = {
    r"from pyregex\.builders": "from pyregex.domain.builders",
    r"import pyregex\.builders": "import pyregex.domain.builders",
    r"from pyregex\.core\.explain": "from pyregex.domain.explain",
    r"from pyregex\.audit": "from pyregex.application.services.audit",
    r"from pyregex\.mask": "from pyregex.application.services.mask",
    r"from pyregex\.validate": "from pyregex.application.services.validate",
    r"from pyregex\.persistence": "from pyregex.infrastructure.persistence",
    r"from pyregex\.core\.registry": "from pyregex.infrastructure.registry",
    r"from pyregex\.core\.execution": "from pyregex.infrastructure.execution",
    r"from pyregex\.config": "from pyregex.infrastructure.config",
    r"from pyregex\.commands": "from pyregex.presentation.cli",
    r"from pyregex\.ui\.assistant": "from pyregex.presentation.assistant",
    r"from pyregex\.ui\.shell": "from pyregex.presentation.shell",
    r"from pyregex\.core\.builder_registry": "from pyregex.infrastructure.registry.builder_registry",
    r"from pyregex\.core\.worker": "from pyregex.application.services.execution.worker",
    r"from pyregex\.infrastructure\.execution\.worker": "from pyregex.application.services.execution.worker",
    r"from pyregex\.core\.transform_service": "from pyregex.application.services.transform_service",
    r"from pyregex\.core\.quick": "from pyregex.application.services.quick",
    r"from pyregex\.core\.testing": "from pyregex.application.services.testing",
    r"from pyregex\.core\.intent_service": "from pyregex.application.services.intent_service",
    r"from pyregex\.core\.explainer": "from pyregex.domain.explain.explainer",
    r"from pyregex\.domain\.explainer": "from pyregex.domain.explain.explainer",
    r"from pyregex\.core\.regex_service": "from pyregex.application.services.regex_service",
    r"from pyregex\.core\.performance_service": "from pyregex.application.services.performance_service",
    r"from pyregex\.core\.merge_service": "from pyregex.application.services.merge_service",
    r"from pyregex\.core\.editor_service": "from pyregex.application.services.editor_service",
    r"from pyregex\.core\.security_service": "from pyregex.application.security.security_service",
    r"from pyregex\.core\.context": "from pyregex.application.services.context",
    r"from pyregex\.core\.shared\.context": "from pyregex.application.services.context",
    r"from pyregex\.core\.shared\.engine": "from pyregex.application.services.engine",
    r"from pyregex\.core\.shared\.parser": "from pyregex.application.services.parser",
    r"from pyregex\.core\.shared\.registry": "from pyregex.application.services.registry",
    r"from pyregex\.core\.shared\.task_manager": "from pyregex.application.services.task_manager",
    r"from pyregex\.infrastructure\.registry\.controller\.registry_controller": "from pyregex.application.services.registry_controller",
    r"from pyregex\.domain\.explain\.controller\.explain_controller": "from pyregex.application.services.explain_controller",
    r"from pyregex\.infrastructure\.execution\.controller\.execution_controller": "from pyregex.application.services.execution.execution_controller",
    r"from pyregex\.infrastructure\.registry\.list": "from pyregex.infrastructure.registry.commands.list",
    r"from pyregex\.infrastructure\.registry\.delete": "from pyregex.infrastructure.registry.commands.delete",
    r"from pyregex\.core\.regex_builder": "from pyregex.domain.builders.base",
}

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for old, new in mapping.items():
        new_content = re.sub(old, new, new_content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    count = 0
    for root, dirs, files in os.walk('src/pyregex'):
        for file in files:
            if file.endswith('.py'):
                if update_file(os.path.join(root, file)):
                    count += 1
    print(f"Updated {count} files.")

if __name__ == "__main__":
    main()
