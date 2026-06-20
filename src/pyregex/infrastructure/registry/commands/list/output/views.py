from typing import Dict, Any
from pyregex.utils import ansi


class BaseView:
    def render(self, pagination_data: Dict[str, Any]) -> str:
        raise NotImplementedError()


class SimpleView(BaseView):
    def render(self, pagination_data: Dict[str, Any]) -> str:
        items = pagination_data.get("items", [])
        if not items:
            return ansi.info("No patterns found.")

        out = []
        for p in items:
            # simple format: name -> description
            desc = p.metadata.description if p.metadata.description else ""
            out.append(f"{ansi.label(p.name.ljust(15))} {ansi.dim(desc)}")
        return "\n".join(out)


class CompactView(BaseView):
    def render(self, pagination_data: Dict[str, Any]) -> str:
        items = pagination_data.get("items", [])
        if not items:
            return ansi.info("No patterns found.")

        out = []
        for p in items:
            out.append(f"{p.name}: {p.pattern}")
        return "\n".join(out)


class DetailedView(BaseView):
    def render(self, pagination_data: Dict[str, Any]) -> str:
        items = pagination_data.get("items", [])
        if not items:
            return ansi.info("No patterns found.")

        out = []
        for p in items:
            out.append(ansi.header(f"{p.name}"))
            out.append(f"  Regex:    {ansi.regex_display(p.pattern)}")
            out.append(f"  Desc:     {p.metadata.description or 'N/A'}")
            out.append(f"  Category: {p.metadata.category}")
            out.append(f"  Tags:     {', '.join(p.metadata.tags)}")
            out.append(f"  Origin:   {p.metadata.origin}")
            out.append(f"  Version:  v{p.metadata.version}")
            out.append("")
        return "\n".join(out)


class GroupedView(BaseView):
    def render(self, pagination_data: Dict[str, Any]) -> str:
        # For grouped view, items is expected to be a dict
        grouped_items = pagination_data.get("items", {})
        if not grouped_items:
            return ansi.info("No patterns found.")

        out = []
        for group_name, patterns in grouped_items.items():
            if not patterns:
                continue
            out.append(ansi.bold(f"[{group_name.upper()}]"))
            for p in patterns:
                desc = p.metadata.description if p.metadata.description else ""
                out.append(f"  - {ansi.label(p.name.ljust(15))} {ansi.dim(desc)}")
            out.append("")
        return "\n".join(out)
