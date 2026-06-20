from __future__ import annotations
import re
from typing import Any, Pattern
from pyregex.domain.builders.base import RegexBuilder, BuilderMetadata


class LogRegexBuilder(RegexBuilder):
    """Base class for log builders with subtype support."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="log",
            category="sysadmin",
            description="Base builder for various log formats.",
            examples=[],
            non_examples=[],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build(self, config: dict[str, Any] | None = None) -> Pattern[str]:
        cfg = self.default_config()
        if config:
            cfg.update(config)

        self.subtype = cfg.get("subtype", "default")
        return re.compile(self.build_pattern())


class ApacheLogRegexBuilder(LogRegexBuilder):
    """Builder for Apache logs (Access/Error/Combined/Common)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="apache",
            category="sysadmin",
            description="Matches Apache access and error logs in common, combined, and error formats.",
            examples=[
                '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /index.html HTTP/1.0" 200 2326',
                "[Wed Oct 11 14:32:52 2000] [error] [client 127.0.0.1] File does not exist",
            ],
            non_examples=["Invalid log line"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "access"}

    def build_pattern(self) -> str:
        if self.subtype == "error":
            return r"^\[(?P<timestamp>.*?)\] \[(?P<module>.*?)\] \[(?P<level>.*?)\] \[pid (?P<pid>\d+)\] (?P<message>.*)"
        elif self.subtype == "combined":
            return r'^(?P<ip>\S+) (?P<ident>\S+) (?P<authuser>\S+) \[(?P<timestamp>.*?)\] "(?P<method>\S+) (?P<path>\S+) (?P<protocol>\S+)" (?P<status>\d{3}) (?P<size>\S+) "(?P<referer>.*?)" "(?P<useragent>.*?)"'
        elif self.subtype == "common":
            return r'^(?P<ip>\S+) (?P<ident>\S+) (?P<authuser>\S+) \[(?P<timestamp>.*?)\] "(?P<method>\S+) (?P<path>\S+) (?P<protocol>\S+)" (?P<status>\d{3}) (?P<size>\S+)'
        # Default to access (standard)
        return r'^(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>.*?)\] "(?P<method>\S+) (?P<path>\S+) (?P<protocol>\S+)" (?P<status>\d{3}) (?P<size>\S+)'


class NginxLogRegexBuilder(LogRegexBuilder):
    """Builder for Nginx logs."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="nginx",
            category="sysadmin",
            description="Matches Nginx access and error logs in combined and standard formats.",
            examples=[
                '192.168.0.1 - - [17/Mar/2026:12:30:45 +0000] "GET /index.html HTTP/1.1" 200 1024',
                "2026/03/17 12:30:45 [error] 1234#0: *1 open() failed",
            ],
            non_examples=["Invalid"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "access"}

    def build_pattern(self) -> str:
        if self.subtype == "error":
            return r"^(?P<timestamp>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<pid>\d+)#(?P<tid>\d+): (?P<message>.*)"
        elif self.subtype == "combined":
            return r'^(?P<ip>\S+) - (?P<user>\S+) \[(?P<timestamp>.*?)\] "(?P<request>.*?)" (?P<status>\d{3}) (?P<bytes_sent>\d+) "(?P<referer>.*?)" "(?P<user_agent>.*?)"'
        # Default to access
        return r'^(?P<ip>\S+) - (?P<user>\S+) \[(?P<timestamp>.*?)\] "(?P<request>.*?)" (?P<status>\d{3}) (?P<bytes_sent>\d+)'


class SyslogLogRegexBuilder(LogRegexBuilder):
    """Builder for Syslog and systemd logs."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="syslog",
            category="sysadmin",
            description="Matches Syslog and systemd journal logs (auth, daemon, kernel, systemd).",
            examples=[
                "Mar 17 12:34:56 server sshd[1234]: Accepted password",
                "Mar 17 12:34:56 host kernel: [123.456] message",
            ],
            non_examples=["Invalid"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "syslog"}

    def build_pattern(self) -> str:
        if self.subtype == "systemd":
            return r"^(?P<timestamp>\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2}) (?P<hostname>\S+) (?P<process>[\w\-\.]+)\[(?P<pid>\d+)\]: (?P<message>.*)"
        elif self.subtype == "auth":
            return r"^(\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2}) (\S+) sshd\[\d+\]: (?P<status>Accepted|Failed) (?P<method>\S+) for (?P<user>\S+) from (?P<ip>\S+) port \d+ ssh2"
        elif self.subtype == "daemon":
            return r"^(\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2}) (\S+) (?P<daemon>[\w\-\.]+): (?P<message>.*)"
        elif self.subtype == "kernel":
            return r"^(\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2}) (\S+) kernel: \[(?P<time>.*?)\] (?P<message>.*)"
        # Standard syslog
        return r"^(\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2}) (\S+) (\S+): (.*)$"


class TimestampLogRegexBuilder(LogRegexBuilder):
    """Builder for various log timestamp formats."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="timestamp_log",
            category="sysadmin",
            description="Matches timestamps in logs (ISO, RFC, UNIX, or bracketed).",
            examples=[
                "2026-03-17T12:34:56Z",
                "1710678896",
                "[10/Oct/2000:13:55:36 -0700]",
            ],
            non_examples=["not-a-timestamp"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "bracket"}

    def build_pattern(self) -> str:
        if self.subtype == "iso":
            return (
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?"
            )
        elif self.subtype == "rfc":
            return r"\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} [+-]\d{4}"
        elif self.subtype == "unix":
            return r"\d{10}(?:\.\d+)?"
        return r"\[.*?\]"


class IPLogRegexBuilder(LogRegexBuilder):
    """Builder for IP addresses in logs (IPv4, IPv6)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="ip_log",
            category="sysadmin",
            description="Matches IPv4 and IPv6 addresses in log files.",
            examples=["192.168.0.1", "2001:db8::1"],
            non_examples=["invalid-ip"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "both"}

    def build_pattern(self) -> str:
        ipv4 = r"(?:\d{1,3}\.){3}\d{1,3}"
        ipv6 = r"(?:[A-Fa-f0-9:]+:+)+[A-Fa-f0-9]+"
        if self.subtype == "ipv4":
            return ipv4
        if self.subtype == "ipv6":
            return ipv6
        return f"(?:{ipv4}|{ipv6})"


class HTTPLogRegexBuilder(LogRegexBuilder):
    """Builder for HTTP-related log entries (methods, status codes)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="http_log",
            category="sysadmin",
            description="Matches HTTP methods (GET, POST, etc.) and status codes (200, 404, etc.).",
            examples=["GET", "200", "404"],
            non_examples=["INVALID"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "both"}

    def build_pattern(self) -> str:
        if self.subtype == "method":
            return r"\b(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH|TRACE|CONNECT)\b"
        if self.subtype == "status":
            return r"\b[1-5]\d{2}\b"
        return r'(GET|POST|PUT|DELETE|HEAD|OPTIONS)\s+.*?\s+HTTP/\d\.\d"|(\d{3})'


class URLLogRegexBuilder(LogRegexBuilder):
    """Builder for URLs in log files."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="url_log",
            category="sysadmin",
            description="Matches full URLs, paths, or query strings in log files.",
            examples=["/index.html", "https://example.com/api", "page.php?id=1"],
            non_examples=["not/a/url"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "full"}

    def build_pattern(self) -> str:
        if self.subtype == "path":
            return r"/(?:[\w\-\._]+/)*[\w\-\._]*"
        elif self.subtype == "query":
            return r"/(?:[\w\-\._]+/)*[\w\-\._]*\?[\w\-\._&%=]*"
        return r"(?:https?:\/\/)?(?:\S+\.)?\S+\/\S*"


class UserLogRegexBuilder(LogRegexBuilder):
    """Builder for usernames in log files."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="user_log",
            category="sysadmin",
            description="Matches local and remote usernames found in logs.",
            examples=["admin", "user_123", "frank.doe"],
            non_examples=["user!"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "both"}

    def build_pattern(self) -> str:
        if self.subtype == "local":
            return r"\b[a-z_][a-z0-9_-]*\$?\b"
        elif self.subtype == "remote":
            return r"\b[A-Za-z0-9._-]+\b"
        return r"\b[A-Za-z0-9._-]+\b"


class ErrorLogRegexBuilder(LogRegexBuilder):
    """Builder for error indicators in logs."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="error_log",
            category="sysadmin",
            description="Matches HTTP error status codes or system error indicators.",
            examples=["404", "500", "ERROR", "CRITICAL"],
            non_examples=["200"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "http"}

    def build_pattern(self) -> str:
        if self.subtype == "sys":
            return r"\b(?:ERR|ERROR|FAULT|CRITICAL|Status:)\s*[0-9A-F]+\b"
        # Default to http
        return r"\b(?:4\d{2}|5\d{2})\b"


class LevelLogRegexBuilder(LogRegexBuilder):
    """Builder for log levels (INFO, WARN, etc.)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="level_log",
            category="sysadmin",
            description="Matches common log levels like INFO, WARN, ERROR, etc.",
            examples=["INFO", "ERROR", "DEBUG"],
            non_examples=["START"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(INFO|WARN|ERROR|DEBUG|TRACE|FATAL|CRITICAL)\b"


class CloudWatchLogRegexBuilder(LogRegexBuilder):
    """Builder for AWS CloudWatch logs."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="cloudwatch_log",
            category="sysadmin",
            description="Matches AWS CloudWatch log events, metrics, and filters.",
            examples=["2026-03-17T12:34:56.123Z [MyService] INFO Service started"],
            non_examples=["Invalid"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "events"}

    def build_pattern(self) -> str:
        if self.subtype == "metrics":
            return r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(?P<request_id>\S+)\s+(?P<message>.*)$"
        elif self.subtype == "filter":
            return r'\{(?:(?:\s*"\$.*?"\s*[:=]\s*".*?"\s*,?)+)\}'
        # Default to events
        return r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d+Z\s+\[\S+\]\s+(INFO|WARN|ERROR|DEBUG)\s+(.*)$"


class ALBLogRegexBuilder(LogRegexBuilder):
    """Builder for AWS ALB access logs."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="alb_log",
            category="sysadmin",
            description="Matches AWS Application Load Balancer (ALB) access logs.",
            examples=[
                'https 2026-03-17T12:34:56.123Z app/my-app 192.168.0.1:12345 192.168.0.2:80 0.002 0.001 0.001 200 1234 5678 0 "GET /index.html HTTP/1.1" "curl/7.68.0" - - arn:aws:elasticloadbalancing:region:123456789012:targetgroup/my-target/1234567890abcdef 0.000 0.000 200 200'
            ],
            non_examples=["Invalid"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r'^(\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) "(\S+) (\S+) (\S+)" (\d{3}) (\d+) (\d+) (\d+) "([^"]*)" "([^"]*)" (\S+) (\S+) (\S+) (\S+)$'


class ELBLogRegexBuilder(LogRegexBuilder):
    """Builder for AWS Classic ELB logs."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="elb_log",
            category="sysadmin",
            description="Matches AWS Classic Elastic Load Balancer (ELB) logs.",
            examples=[
                '2015-05-13T23:39:43.945172Z my-loadbalancer 192.168.131.39:2817 10.0.0.1:80 0.000022 0.001048 0.00002 200 200 0 57 "GET http://example.com:80/ HTTP/1.1" "curl/7.38.0" -'
            ],
            non_examples=["Invalid"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r'^(\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) "(\S+) (\S+) (\S+)" (\d{3}) (\d+) (\d+) (\d+) "([^"]*)" "([^"]*)"$'


class AWSRequestIDRegexBuilder(LogRegexBuilder):
    """Builder for AWS Request IDs and Trace IDs."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="aws_request_id",
            category="sysadmin",
            description="Matches AWS Request IDs and X-Ray Trace IDs.",
            examples=[
                "c5b7f9a0-4a1f-11eb-b378-0242ac130002",
                "Root=1-5759dc10-000000000000000000000000",
            ],
            non_examples=["invalid-id"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "request"}

    def build_pattern(self) -> str:
        uuid = r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"
        if self.subtype == "trace":
            return r"Root=1-[a-f0-9]{8}-[a-f0-9]{24}"
        return uuid


class AWSUserAgentRegexBuilder(LogRegexBuilder):
    """Builder for AWS-specific User Agent strings."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="aws_user_agent",
            category="sysadmin",
            description="Matches AWS User Agent strings (CLI, SDK, or browser).",
            examples=['"aws-cli/2.0.0 Python/3.8.10"', '"aws-sdk-go/1.42.0"'],
            non_examples=["Invalid"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "sdk"}

    def build_pattern(self) -> str:
        if self.subtype == "browser":
            return r"Mozilla\/5\.0\s+\(.*?\).*"
        elif self.subtype == "sdk":
            return r"aws-sdk-[\w\-]+\/[\d\.]+"
        elif self.subtype == "cli":
            return r"aws-cli\/[\d\.]+\s+Python\/[\d\.]+\s+.*"
        return r'"[^"]+"'


class AWSAlertRegexBuilder(LogRegexBuilder):
    """Builder for CloudWatch alarms and alert patterns."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="aws_alert",
            category="sysadmin",
            description="Matches CloudWatch alarm states and metric alerts.",
            examples=["ALARM", "ThresholdReached", "OK"],
            non_examples=["NORMAL"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "state"}

    def build_pattern(self) -> str:
        if self.subtype == "metric":
            return r"\b(ThresholdReached|AlarmUpdated|InsufficientData)\b"
        elif self.subtype == "state":
            return r"\b(ALARM|OK|INSUFFICIENT_DATA)\b"
        return r"\b(ALARM|OK|INSUFFICIENT_DATA)\b"


class DockerContainerRegexBuilder(LogRegexBuilder):
    """Builder for Docker container names and IDs."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="docker_container",
            category="sysadmin",
            description="Matches Docker container names and short/long IDs.",
            examples=["my_app_container", "d3f5e6a7b8c9"],
            non_examples=["invalid!"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "both"}

    def build_pattern(self) -> str:
        if self.subtype == "name":
            return r"[a-zA-Z0-9_.-]+"
        if self.subtype == "id":
            return r"[a-f0-9]{12,64}"
        return r"([a-zA-Z0-9_.-]+)|([a-f0-9]{12,64})"


class DockerStatusRegexBuilder(LogRegexBuilder):
    """Builder for Docker container statuses."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="docker_status",
            category="sysadmin",
            description="Matches Docker container states (running, exited, etc.).",
            examples=["running", "exited", "paused"],
            non_examples=["stopped"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(running|exited|paused|restarting)\b"


class DockerResourceRegexBuilder(LogRegexBuilder):
    """Builder for Docker resource usage (CPU/Memory)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="docker_resource",
            category="sysadmin",
            description="Matches CPU and Memory usage percentages or units in Docker logs.",
            examples=["45.5%", "1.2GB", "256MB"],
            non_examples=["invalid"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "cpu"}

    def build_pattern(self) -> str:
        if self.subtype == "cpu":
            return r"\d{1,3}\.\d+%?"
        if self.subtype == "memory":
            return r"\d+(?:\.\d+)?\s?(B|KB|MB|GB)"
        return r"\d{1,3}\.\d+%?|\d+(?:\.\d+)?\s?(B|KB|MB|GB)"


class DockerNetworkRegexBuilder(LogRegexBuilder):
    """Builder for Docker network activity (ports, protocols)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="docker_network",
            category="sysadmin",
            description="Matches Docker network ports, protocols, and IP addresses.",
            examples=["8080", "192.168.0.2", "TCP"],
            non_examples=["808080"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "both"}

    def build_pattern(self) -> str:
        if self.subtype == "port":
            return r"\b\d{1,5}\b"
        if self.subtype == "proto":
            return r"\b(TCP|UDP)\b"
        return r"(\d{1,5})|(?:\d{1,3}\.){3}\d{1,3}|TCP|UDP"


class DockerEventRegexBuilder(LogRegexBuilder):
    """Builder for Docker lifecycle events (start, stop, etc.)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="docker_event",
            category="sysadmin",
            description="Matches Docker lifecycle events like start, stop, kill, restart.",
            examples=["start", "kill", "stop"],
            non_examples=["pause"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(start|stop|kill|restart)\b"


class K8sPodRegexBuilder(LogRegexBuilder):
    """Builder for Kubernetes Pod names and UIDs."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="k8s_pod",
            category="sysadmin",
            description="Matches Kubernetes Pod names and unique identifiers (UIDs).",
            examples=["nginx-deployment-5d8f6d4f7c-abcde", "my-app-pod-12345"],
            non_examples=["Invalid-Pod"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "name"}

    def build_pattern(self) -> str:
        # Standard k8s name/id pattern
        name_part = r"[a-z0-9]([-a-z0-9]*[a-z0-9])?"
        if self.subtype == "uid":
            return r"[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}"
        return name_part


class K8sContainerRegexBuilder(LogRegexBuilder):
    """Builder for Kubernetes Container names."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="k8s_container",
            category="sysadmin",
            description="Matches Kubernetes container names.",
            examples=["nginx", "sidecar-logger"],
            non_examples=["Upper-Case"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"[a-z0-9]([-a-z0-9]*[a-z0-9])?"


class K8sNamespaceRegexBuilder(LogRegexBuilder):
    """Builder for Kubernetes Namespaces."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="k8s_namespace",
            category="sysadmin",
            description="Matches Kubernetes namespaces names.",
            examples=["default", "kube-system", "prod-env"],
            non_examples=["namespace_"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"[a-z0-9]([-a-z0-9]*[a-z0-9])?"


class K8sStatusRegexBuilder(LogRegexBuilder):
    """Builder for Kubernetes Pod/Container statuses."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="k8s_status",
            category="sysadmin",
            description="Matches Kubernetes Pod and container states (Running, CrashLoopBackOff, etc.).",
            examples=["Running", "CrashLoopBackOff", "Failed"],
            non_examples=["Starting"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return (
            r"\b(Pending|Running|Succeeded|Failed|CrashLoopBackOff|Completed|Error)\b"
        )


class K8sEventRegexBuilder(LogRegexBuilder):
    """Builder for Kubernetes lifecycle and scheduling events."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="k8s_event",
            category="sysadmin",
            description="Matches Kubernetes events like Started, Killing, Evicted.",
            examples=["Started", "Pulling", "Evicted"],
            non_examples=["Stopped"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(Created|Started|Killing|Pulled|Pulling|Scheduled|Evicted)\b"


class K8sNodeRegexBuilder(LogRegexBuilder):
    """Builder for Kubernetes Node info."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="k8s_node",
            category="sysadmin",
            description="Matches Kubernetes Node names or IP addresses.",
            examples=["node-1", "192.168.1.10"],
            non_examples=["node_1"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "both"}

    def build_pattern(self) -> str:
        if self.subtype == "ip":
            return r"(?:\d{1,3}\.){3}\d{1,3}"
        return r"([a-zA-Z0-9.-]+)|((?:\d{1,3}\.){3}\d{1,3})"


class K8sResourceRegexBuilder(LogRegexBuilder):
    """Builder for Kubernetes resource usage (CPU/Memory)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="k8s_resource",
            category="sysadmin",
            description="Matches Kubernetes resource units (m, Mi, Gi, etc.).",
            examples=["500m", "256Mi", "2Gi"],
            non_examples=["500"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\d+(m|Mi|Gi|Ki|n)?"


class K8sErrorRegexBuilder(LogRegexBuilder):
    """Builder for Kubernetes error and crash patterns."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="k8s_error",
            category="sysadmin",
            description="Matches common Kubernetes error states (OOMKilled, ImagePullBackOff, etc.).",
            examples=["OOMKilled", "ErrImagePull", "CrashLoopBackOff"],
            non_examples=["NoError"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(CrashLoopBackOff|OOMKilled|ImagePullBackOff|ErrImagePull|ConnectionRefused)\b"


class K8sLabelRegexBuilder(LogRegexBuilder):
    """Builder for Kubernetes labels and selectors."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="k8s_label",
            category="sysadmin",
            description="Matches Kubernetes labels and key=value selectors.",
            examples=["app=nginx", "env=production"],
            non_examples=["invalid=label="],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "label"}

    def build_pattern(self) -> str:
        part = r"[a-z0-9A-Z_.-]+"
        if self.subtype == "selector":
            return rf"{part}={part}"
        return part


class SQLQueryRegexBuilder(LogRegexBuilder):
    """Builder for SQL query types."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="sql_query_log",
            category="sysadmin",
            description="Matches common SQL command keywords in log files.",
            examples=["SELECT", "INSERT", "UPDATE"],
            non_examples=["invalid"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE)\b"


class SQLTableRegexBuilder(LogRegexBuilder):
    """Builder for SQL table names."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="sql_table_log",
            category="sysadmin",
            description="Matches SQL table names following FROM, JOIN, INTO, or UPDATE.",
            examples=["FROM users", "JOIN orders"],
            non_examples=["users"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*)"


class SQLColumnRegexBuilder(LogRegexBuilder):
    """Builder for SQL column names."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="sql_column_log",
            category="sysadmin",
            description="Matches potential SQL column names in log files.",
            examples=["user_id", "created_at"],
            non_examples=["123"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"


class SQLWhereRegexBuilder(LogRegexBuilder):
    """Builder for SQL WHERE clauses."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="sql_where_log",
            category="sysadmin",
            description="Matches SQL WHERE clauses in log files.",
            examples=["WHERE id = 1", "WHERE active = 1 AND age > 18"],
            non_examples=["WHERE"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\bWHERE\b\s+.+?(?=\bGROUP|\bORDER|\bLIMIT|$)"


class SQLJoinRegexBuilder(LogRegexBuilder):
    """Builder for SQL JOIN operations."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="sql_join_log",
            category="sysadmin",
            description="Matches SQL JOIN operations (INNER, LEFT, RIGHT, etc.).",
            examples=["LEFT JOIN", "INNER JOIN", "JOIN"],
            non_examples=["JOINED"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\b"


class SQLValueRegexBuilder(LogRegexBuilder):
    """Builder for SQL values."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="sql_value_log",
            category="sysadmin",
            description="Matches common SQL values like strings, numbers, and NULL.",
            examples=["'hello'", "123", "NULL", "TRUE"],
            non_examples=["'broken"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"'(?:\\'|[^'])*'|\b\d+\b|\bNULL\b|\b(TRUE|FALSE)\b"


class SQLTransactionRegexBuilder(LogRegexBuilder):
    """Builder for SQL transactions."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="sql_transaction_log",
            category="sysadmin",
            description="Matches SQL transaction commands (BEGIN, COMMIT, etc.).",
            examples=["BEGIN", "COMMIT", "ROLLBACK"],
            non_examples=["FINISHED"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(BEGIN|START TRANSACTION|COMMIT|ROLLBACK|SAVEPOINT)\b"


class SQLPerfRegexBuilder(LogRegexBuilder):
    """Builder for SQL performance metrics."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="sql_perf_log",
            category="sysadmin",
            description="Matches SQL performance metrics like execution time and row counts.",
            examples=["12.5 ms", "rows=1000", "cost=250"],
            non_examples=["abc"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(\d+\.\d+\s?ms|\d+\s?seconds|rows=\d+|cost=\d+)\b"


class SQLErrorRegexBuilder(LogRegexBuilder):
    """Builder for SQL errors."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="sql_error_log",
            category="sysadmin",
            description="Matches common SQL error messages and indicators.",
            examples=["ERROR", "syntax error", "constraint", "duplicate key"],
            non_examples=["SUCCESS"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(ERROR|syntax error|constraint|duplicate key|timeout|connection refused)\b"


class SQLFuncRegexBuilder(LogRegexBuilder):
    """Builder for SQL functions (COUNT, SUM, etc.)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="sql_func_log",
            category="sysadmin",
            description="Matches common SQL built-in functions followed by parentheses.",
            examples=["COUNT(*)", "NOW()", "ROW_NUMBER("],
            non_examples=["COUNT"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(COUNT|SUM|AVG|MIN|MAX|CONCAT|NOW|DATE|ROW_NUMBER)\s*\("


class SQLDDLRegexBuilder(LogRegexBuilder):
    """Builder for SQL DDL statements (CREATE, ALTER, DROP)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="sql_ddl_log",
            category="sysadmin",
            description="Matches SQL Data Definition Language statements like CREATE TABLE, DROP DATABASE.",
            examples=["CREATE TABLE", "ALTER TABLE", "DROP INDEX"],
            non_examples=["CREATE"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(CREATE|ALTER|DROP)\s+(TABLE|INDEX|DATABASE)\b"


class SQLCommentRegexBuilder(LogRegexBuilder):
    """Builder for SQL comments."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="sql_comment_log",
            category="sysadmin",
            description="Matches single-line (--) and multi-line (/* */) SQL comments.",
            examples=["-- comment", "/* multi-line */"],
            non_examples=["// comment"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"(--.*$)|(/\*[\s\S]*?\*/)"


class SSHTimestampRegexBuilder(LogRegexBuilder):
    """Builder for SSH timestamps."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="ssh_timestamp",
            category="sysadmin",
            description="Matches SSH log timestamps (Syslog or ISO format).",
            examples=["Mar 17 12:34:56", "2026-03-17T12:34:56Z"],
            non_examples=["invalid"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "syslog"}

    def build_pattern(self) -> str:
        if self.subtype == "syslog":
            return r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b"
        elif self.subtype == "iso":
            return (
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
            )
        return r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b"


class SSHIPRegexBuilder(LogRegexBuilder):
    """Builder for SSH source IP addresses."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="ssh_ip",
            category="sysadmin",
            description="Matches SSH source IP addresses (public or private ranges).",
            examples=["192.168.1.10", "8.8.8.8"],
            non_examples=["999.999.999.999"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        if self.subtype == "private":
            return r"\b(10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)\b"
        return r"\b(?:\d{1,3}\.){3}\d{1,3}\b"


class SSHUserRegexBuilder(LogRegexBuilder):
    """Builder for SSH usernames."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="ssh_user",
            category="sysadmin",
            description="Matches SSH usernames following 'user' or 'for'.",
            examples=["user admin", "for root"],
            non_examples=["user !@#"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\buser\s+([a-zA-Z0-9._-]+)|for\s+([a-zA-Z0-9._-]+)\b"


class SSHAuthRegexBuilder(LogRegexBuilder):
    """Builder for SSH authentication attempts."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="ssh_auth",
            category="sysadmin",
            description="Matches SSH authentication results (Accepted, Failed, etc.).",
            examples=["Accepted", "Failed", "Invalid user"],
            non_examples=["Denied"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(Accepted|Failed|Invalid user)\b"


class SSHStatusRegexBuilder(LogRegexBuilder):
    """Builder for SSH connection status."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="ssh_status",
            category="sysadmin",
            description="Matches SSH connection lifecycle status (opened, closed, Failed).",
            examples=["Opened", "closed", "Connection reset"],
            non_examples=["Stopped"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b([Oo]pened|[Cc]losed|[Ff]ailed|Connection reset)\b"


class SSHMethodRegexBuilder(LogRegexBuilder):
    """Builder for SSH authentication methods."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="ssh_method",
            category="sysadmin",
            description="Matches SSH authentication methods (password, publickey, etc.).",
            examples=["password", "publickey"],
            non_examples=["biometric"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(password|publickey|keyboard-interactive|gssapi)\b"


class SSHSessionRegexBuilder(LogRegexBuilder):
    """Builder for SSH session lifecycle."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="ssh_session",
            category="sysadmin",
            description="Matches SSH session open/close events and TTY allocation.",
            examples=["session opened", "session closed", "tty"],
            non_examples=["session paused"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(session opened|session closed|tty)\b"


class SSHPortRegexBuilder(LogRegexBuilder):
    """Builder for SSH ports."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="ssh_port",
            category="sysadmin",
            description="Matches the SSH port number in connection logs.",
            examples=["port 22", "port 2222"],
            non_examples=["port abc"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\bport\s+\d{1,5}\b"


class SSHAttackRegexBuilder(LogRegexBuilder):
    """Builder for SSH suspicious patterns."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="ssh_attack",
            category="sysadmin",
            description="Matches signs of SSH brute force or unauthorized attempts.",
            examples=["Failed password", "Invalid user admin"],
            non_examples=["Accepted password"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(Failed password|Invalid user|authentication failure)\b"


class SSHGeoRegexBuilder(LogRegexBuilder):
    """Builder for SSH geo/network ranges."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="ssh_geo",
            category="sysadmin",
            description="Matches SSH source IP addresses within specific geographical or internal ranges.",
            examples=["192.168.1.1", "10.0.0.5"],
            non_examples=["8.8.8.8"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "private"}

    def build_pattern(self) -> str:
        # Focusing on internal network pattern as requested in the example
        return r"\b(10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)\b"


class SSHPIDRegexBuilder(LogRegexBuilder):
    """Builder for SSH process IDs."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="ssh_pid",
            category="sysadmin",
            description="Matches SSH process identifiers in square brackets.",
            examples=["[1234]", "[98765]"],
            non_examples=["(1234)"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\[\d+\]"


class ErrorCodeRegexBuilder(LogRegexBuilder):
    """Builder for various error codes (HTTP, system)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="error_code_log",
            category="sysadmin",
            description="Matches HTTP error codes or generic system error patterns.",
            examples=["404", "errno: 2", "error code=5"],
            non_examples=["200"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "http"}

    def build_pattern(self) -> str:
        if self.subtype == "http":
            return r"\b(4\d{2}|5\d{2})\b"
        elif self.subtype == "system":
            return r"\b(errno|error code)\s*[:=]?\s*\d+\b"
        return r"\b\d+\b"


class PythonErrorRegexBuilder(LogRegexBuilder):
    """Builder for Python exceptions and errors."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="python_error_log",
            category="sysadmin",
            description="Matches Python error indicators (ValueError, Traceback, etc.).",
            examples=[
                "ValueError",
                'File "app.py", line 42',
                "Traceback (most recent call last):",
            ],
            non_examples=["success"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "exception"}

    def build_pattern(self) -> str:
        if self.subtype == "exception":
            return r"\b[A-Z][a-zA-Z]+Error\b"
        elif self.subtype == "traceback":
            return r"Traceback \(most recent call last\):"
        elif self.subtype == "fileline":
            return r'File ".*?", line \d+'
        return r"\b[A-Z][a-zA-Z]+Error\b"


class JavaErrorRegexBuilder(LogRegexBuilder):
    """Builder for Java exceptions and stack traces."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="java_error_log",
            category="sysadmin",
            description="Matches Java exception names and stack trace elements.",
            examples=[
                "NullPointerException",
                "at com.app.Service.run(Service.java:12)",
                "Caused by: java.io.IOException",
            ],
            non_examples=["at 12:00"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "exception"}

    def build_pattern(self) -> str:
        if self.subtype == "exception":
            return r"\b[A-Z][a-zA-Z]+Exception\b"
        elif self.subtype == "trace":
            return r"at\s+[a-zA-Z0-9_.]+\(.+:\d+\)"
        elif self.subtype == "caused":
            return r"Caused by:.*"
        return r"\b[A-Z][a-zA-Z]+Exception\b"


class NodeErrorRegexBuilder(LogRegexBuilder):
    """Builder for Node.js / JS errors."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="node_error_log",
            category="sysadmin",
            description="Matches Node.js error types and stack trace lines.",
            examples=["TypeError", "at Object.<anonymous> (index.js:12:5)"],
            non_examples=["at noon"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "error"}

    def build_pattern(self) -> str:
        if self.subtype == "error":
            return r"\b(Error|TypeError|ReferenceError|SyntaxError)\b"
        elif self.subtype == "trace":
            return r"at\s+.*\(.+:\d+:\d+\)"
        return r"\b(Error|TypeError|ReferenceError|SyntaxError)\b"


class GoErrorRegexBuilder(LogRegexBuilder):
    """Builder for Go errors and panics."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="go_error_log",
            category="sysadmin",
            description="Matches Go panic messages and goroutine stack traces.",
            examples=["panic: runtime error", "goroutine 1 [running]:"],
            non_examples=["go routine"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "panic"}

    def build_pattern(self) -> str:
        if self.subtype == "panic":
            return r"panic: .+"
        elif self.subtype == "goroutine":
            return r"goroutine \d+ \[.*\]:"
        return r"panic: .+"


class RustErrorRegexBuilder(LogRegexBuilder):
    """Builder for Rust panics and errors."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="rust_error_log",
            category="sysadmin",
            description="Matches Rust panic messages and source file locations.",
            examples=["thread 'main' panicked at", "--> src/main.rs:14:9"],
            non_examples=["cargo"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "panic"}

    def build_pattern(self) -> str:
        if self.subtype == "panic":
            return r"thread '.*' panicked at"
        elif self.subtype == "trace":
            return r"--> .+:\d+:\d+"
        return r"thread '.*' panicked at"


class GenericTraceRegexBuilder(LogRegexBuilder):
    """Builder for generic stack trace lines (at ...:line)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="generic_trace_log",
            category="sysadmin",
            description="Matches generic stack trace lines across different languages.",
            examples=["at main.go:45", "at index.js:12"],
            non_examples=["at home"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"at\s+.+:\d+"


class FilePathRegexBuilder(LogRegexBuilder):
    """Builder for file paths in error logs."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="file_path_log",
            category="sysadmin",
            description="Matches Linux or Windows file paths, often seen in stack traces.",
            examples=["/path/to/file.py", "C:\\project\\app.js"],
            non_examples=["file"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "linux"}

    def build_pattern(self) -> str:
        if self.subtype == "linux":
            return r"\/[a-zA-Z0-9_\-\/\.]+\.(py|js|java|go|rs)"
        elif self.subtype == "windows":
            return r"[A-Z]:\\[^\s]+"
        return r"\/[a-zA-Z0-9_\-\/\.]+"


class LineNumberRegexBuilder(LogRegexBuilder):
    """Builder for line numbers in logs and traces."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="line_number_log",
            category="sysadmin",
            description="Matches line number indicators like :42 or line 42.",
            examples=[":42", ":101"],
            non_examples=["time 12:00"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r":\d+"


class PanicRegexBuilder(LogRegexBuilder):
    """Builder for critical panic and fatal error patterns."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="panic_log",
            category="sysadmin",
            description="Matches high-severity error keywords like FATAL, panic, segmentation fault.",
            examples=["FATAL", "panic", "segmentation fault"],
            non_examples=["warning"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(FATAL|panic|segmentation fault|OOMKilled|core dumped)\b"


class MultiLineStackRegexBuilder(LogRegexBuilder):
    """Builder for capturing multi-line stack traces."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="multiline_stack_log",
            category="sysadmin",
            description="Matches blocks of text representing multi-line stack traces.",
            examples=['Traceback (most recent call last):\n  File "app.py", line 1'],
            non_examples=["single line"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "python"}

    def build_pattern(self) -> str:
        if self.subtype == "python":
            return r"Traceback[\s\S]+?(?=\n\S|$)"
        return r"at\s+[\s\S]+?(?=\n\S|$)"


class ISOTimeRegexBuilder(LogRegexBuilder):
    """Builder for ISO 8601 timestamps."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="iso_time",
            category="sysadmin",
            description="Matches ISO 8601 compliant timestamps in various formats.",
            examples=[
                "2026-03-17T12:34:56Z",
                "2026-03-17",
                "2026-03-17T12:34:56+02:00",
            ],
            non_examples=["12:34:56"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "zulu"}

    def build_pattern(self) -> str:
        if self.subtype == "basic":
            return r"\b\d{4}-\d{2}-\d{2}\b"
        elif self.subtype == "datetime":
            return r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\b"
        elif self.subtype == "zulu":
            return r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\b"
        elif self.subtype == "offset":
            return r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}(?::?\d{2})?\b"
        elif self.subtype == "compact":
            return r"\b\d{8}T\d{6}Z?\b"
        return r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?\b"


class UnixTimeRegexBuilder(LogRegexBuilder):
    """Builder for Unix timestamps (seconds or milliseconds)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="unix_time",
            category="sysadmin",
            description="Matches Unix timestamps in seconds, milliseconds, or microseconds.",
            examples=["1679051234", "1679051234567"],
            non_examples=["2026"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "seconds"}

    def build_pattern(self) -> str:
        if self.subtype == "seconds":
            return r"\b\d{10}\b"
        elif self.subtype == "milliseconds":
            return r"\b\d{13}\b"
        elif self.subtype == "microseconds":
            return r"\b\d{16}\b"
        return r"\b\d{10,16}\b"


class RFCTimeRegexBuilder(LogRegexBuilder):
    """Builder for RFC-standard timestamps (RFC 2822, RFC 3339)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="rfc_time",
            category="sysadmin",
            description="Matches official RFC timestamp formats.",
            examples=["Tue, 17 Mar 2026 12:34:56 +0000", "2026-03-17T12:34:56Z"],
            non_examples=["Mar 17"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "rfc3339"}

    def build_pattern(self) -> str:
        if self.subtype == "rfc2822":
            return r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s\d{2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{4}\s\d{2}:\d{2}:\d{2}\s[+-]\d{4}\b"
        elif self.subtype == "rfc3339":
            return r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})\b"
        return r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun).+\d{4}\b"


class StandardDateRegexBuilder(LogRegexBuilder):
    """Builder for common standard date formats (ISO, EU, US)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="standard_date_log",
            category="sysadmin",
            description="Matches common numeric date formats like YYYY-MM-DD or DD/MM/YYYY.",
            examples=["2026-03-17", "17/03/2026", "03/17/2026"],
            non_examples=["12:34"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "iso"}

    def build_pattern(self) -> str:
        if self.subtype == "iso":
            return r"\b\d{4}-\d{2}-\d{2}\b"
        elif self.subtype == "eu":
            return r"\b\d{2}/\d{2}/\d{4}\b"
        elif self.subtype == "us":
            return r"\b\d{2}/\d{2}/\d{4}\b"
        elif self.subtype == "short":
            return r"\b\d{2}-\d{2}-\d{2}\b"
        return r"\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{2}/\d{4}\b"


class TextualDateRegexBuilder(LogRegexBuilder):
    """Builder for textual dates with month names (e.g., March 17, 2026)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="textual_date_log",
            category="sysadmin",
            description="Matches dates with spelled-out or abbreviated month names.",
            examples=["March 17, 2026", "17 Mar 2026"],
            non_examples=["2026-03-17"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        months_full = r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        months_short = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"

        if self.subtype == "full":
            m = months_full
        elif self.subtype == "short":
            m = months_short
        else:
            m = rf"({months_full}|{months_short})"

        if self.subtype == "weekday":
            days = r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun)"
            return rf"\b{days},\s{m}\s\d{{1,2}},?\s\d{{4}}\b"

        # Flexible: DD Month YYYY or Month DD, YYYY
        return rf"\b(?:\d{{1,2}}\s)?{m}(?:\s\d{{1,2}})?\b,?\s\d{{4}}\b"


class CompactDateRegexBuilder(LogRegexBuilder):
    """Builder for space-efficient compact dates (e.g., 20260317)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="compact_date_log",
            category="sysadmin",
            description="Matches dates in compact numeric formats without separators.",
            examples=["20260317", "260317"],
            non_examples=["17/03/26"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        if self.subtype == "yymmdd":
            return r"\b\d{6}\b"
        return r"\b\d{8}\b"


class PartialDateRegexBuilder(LogRegexBuilder):
    """Builder for partial date references (Month/Year, Year, etc.)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="partial_date_log",
            category="sysadmin",
            description="Matches partial date parts like month/year or quarters.",
            examples=["03/2026", "2026", "Q1"],
            non_examples=["17th"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "year"}

    def build_pattern(self) -> str:
        if self.subtype == "month_year":
            return r"\b\d{2}/\d{4}\b"
        elif self.subtype == "day_month":
            return r"\b\d{2}/\d{2}\b"
        elif self.subtype == "quarter":
            return r"\bQ[1-4](?:\s\d{4})?\b"
        return r"\b\d{4}\b"


class DateRangeRegexBuilder(LogRegexBuilder):
    """Builder for date ranges and intervals."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="date_range_log",
            category="sysadmin",
            description="Matches date ranges using 'to' or '-' separators.",
            examples=["2026-03-01 - 2026-03-31", "2026-01-01 to 2026-12-31"],
            non_examples=["2026-03-17"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "dash"}

    def build_pattern(self) -> str:
        date_p = r"\d{4}-\d{2}-\d{2}"
        if self.subtype == "to":
            return rf"\b{date_p}\s+to\s+{date_p}\b"
        return rf"\b{date_p}\s?-\s?{date_p}\b"


class StrictDateRegexBuilder(LogRegexBuilder):
    """Builder for strictly validated date formats (e.g., proper month/day ranges)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="strict_date_log",
            category="sysadmin",
            description="Matches numeric dates with strict digit validation for months and days.",
            examples=["2026-03-17", "2026-12-31"],
            non_examples=["2026-13-40"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        months = r"(0[1-9]|1[0-2])"
        days = r"(0[1-9]|[12][0-9]|3[01])"
        if self.subtype == "month":
            return rf"\b\d{4}-{months}-\d{2}\b"
        elif self.subtype == "day":
            return rf"\b\d{4}-\d{2}-{days}\b"
        return rf"\b\d{4}-{months}-{days}\b"


class SeparatorDateRegexBuilder(LogRegexBuilder):
    """Builder for dates with custom or flexible separators (., /, -, space)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="separator_date_log",
            category="sysadmin",
            description="Matches numeric dates with various separator characters.",
            examples=["17.03.2026", "17/03/2026", "17-03-2026"],
            non_examples=["17:03:2026"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "flexible"}

    def build_pattern(self) -> str:
        if self.subtype == "slash":
            return r"\b\d{2}/\d{2}/\d{4}\b"
        elif self.subtype == "dash":
            return r"\b\d{2}-\d{2}-\d{4}\b"
        elif self.subtype == "dot":
            return r"\b\d{2}\.\d{2}\.\d{4}\b"
        return r"\b\d{2}[-/. ]\d{2}[-/. ]\d{4}\b"


class LocaleDateRegexBuilder(LogRegexBuilder):
    """Builder for locale-specific date formats (EU vs US)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="locale_date_log",
            category="sysadmin",
            description="Matches date formats preferred in specific regions (e.g., DD/MM vs MM/DD).",
            examples=["03/17/2026", "17/03/2026"],
            non_examples=["17:03"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "flexible"}

    def build_pattern(self) -> str:
        if self.subtype == "eu":
            return r"\b\d{2}/\d{2}/\d{4}\b"
        elif self.subtype == "us":
            return r"\b\d{2}/\d{2}/\d{4}\b"
        return r"\b(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})\b"


class OrdinalDateRegexBuilder(LogRegexBuilder):
    """Builder for dates with ordinal indicators (1st, 2nd, 3rd, 4th)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="ordinal_date_log",
            category="sysadmin",
            description="Matches days with ordinal suffixes like '1st' or 'March 17th'.",
            examples=["1st", "March 17th", "22nd"],
            non_examples=["17"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        ords = r"(st|nd|rd|th)"
        if self.subtype == "text":
            return rf"\b[A-Z][a-z]+\s\d{1, 2}{ords}\b"
        return rf"\b\d{1, 2}{ords}\b"


class WeekDateRegexBuilder(LogRegexBuilder):
    """Builder for ISO week-based dates (e.g., 2026-W11)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="week_date_log",
            category="sysadmin",
            description="Matches ISO 8601 week date format (YYYY-Www).",
            examples=["2026-W11", "2025-W52"],
            non_examples=["2026-03"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b\d{4}-W\d{2}\b"


class LogDateOnlyRegexBuilder(LogRegexBuilder):
    """Builder for date-only parts specific to common log formats."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="log_date_only",
            category="sysadmin",
            description="Matches partial date formats found in common application logs.",
            examples=["17/Mar/2026", "Mar 17"],
            non_examples=["2026-03-17"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "apache"}

    def build_pattern(self) -> str:
        if self.subtype == "apache":
            return r"\d{2}/[A-Za-z]{3}/\d{4}"
        elif self.subtype == "syslog":
            return r"[A-Za-z]{3}\s+\d{1,2}"
        return r"\b\d{2}/[A-Za-z]{3}/\d{4}\b"


class NetFlowIPRegexBuilder(LogRegexBuilder):
    """Builder for IP addresses in NetFlow traffic data."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="netflow_ip",
            category="sysadmin",
            description="Matches IP addresses and traffic arrows in NetFlow records.",
            examples=["192.168.1.10", "10.0.0.1 -> 8.8.8.8"],
            non_examples=["256.256.256.256"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        ip = r"(?:\d{1,3}\.){3}\d{1,3}"
        if self.subtype == "src":
            return rf"\S+\s+({ip})\b"  # Context dependent
        elif self.subtype == "dst":
            return rf"->\s*({ip})\b"
        elif self.subtype == "pair":
            return rf"\b{ip}\s+(?:->|=>)\s+{ip}\b"
        elif self.subtype == "private":
            return r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b"
        return rf"\b{ip}\b"


class NetFlowPortRegexBuilder(LogRegexBuilder):
    """Builder for network ports in traffic logs."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="netflow_port",
            category="sysadmin",
            description="Matches network port numbers or standard port ranges.",
            examples=["80", "443", "1024-2048"],
            non_examples=["65536"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        if self.subtype == "wellknown":
            return r"\b(21|22|23|25|53|80|110|143|443|3389|8080)\b"
        elif self.subtype == "range":
            return r"\b\d{1,5}-\d{1,5}\b"
        return r"\b\d{1,5}\b"


class NetFlowProtoRegexBuilder(LogRegexBuilder):
    """Builder for network protocols (TCP, UDP, ICMP, etc.)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="netflow_proto",
            category="sysadmin",
            description="Matches network-layer or application-layer protocols.",
            examples=["TCP", "UDP", "HTTP"],
            non_examples=["FOO"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        if self.subtype == "app":
            return r"\b(HTTP|HTTPS|DNS|SSH|FTP|SMTP|IMAP|POP3|RDP)\b"
        return r"\b(TCP|UDP|ICMP|IGMP|GRE|ESP|AH)\b"


class NetFlowTupleRegexBuilder(LogRegexBuilder):
    """Builder for network flow tuples (IP:Port -> IP:Port)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="netflow_tuple",
            category="sysadmin",
            description="Matches source-to-destination flow pairs with ports.",
            examples=[
                "192.168.1.10:54321 -> 8.8.8.8:53 TCP",
                "10.0.0.1:22 -> 10.0.0.2:443",
            ],
            non_examples=["192.168.1.1"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        ip = r"(?:\d{1,3}\.){3}\d{1,3}"
        port = r"\d{1,5}"
        if self.subtype == "full":
            return rf"\b{ip}:{port}\s?->\s?{ip}:{port}\s+(TCP|UDP)\b"
        return rf"\b{ip}:{port}\s?->\s?{ip}:{port}\b"


class NetFlowVolumeRegexBuilder(LogRegexBuilder):
    """Builder for traffic volume metrics (bytes, packets)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="netflow_volume",
            category="sysadmin",
            description="Matches data volume and transfer rates in network logs.",
            examples=["1024 bytes", "10 MB", "500 packets", "10.5 Mbps"],
            non_examples=["10 meters"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        units = r"(bytes|KB|MB|GB|packets|pkts)"
        if self.subtype == "rate":
            return rf"\b\d+(?:\.\d+)?\s?({units}/s|bps|Kbps|Mbps|Gbps)\b"
        elif self.subtype == "human":
            return r"\b\d+(?:\.\d+)?\s?(KB|MB|GB|TB)\b"
        return rf"\b\d+\s?{units}\b"


class NetFlowTimeRegexBuilder(LogRegexBuilder):
    """Builder for network flow timestamps and durations."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="netflow_time",
            category="sysadmin",
            description="Matches time durations and timestamps in traffic logs.",
            examples=["12:34:56.789", "120 ms", "5.5 s"],
            non_examples=["12 hours"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        if self.subtype == "duration":
            return r"\b\d+(?:\.\d+)?\s?(ms|s|sec|min)\b"
        return r"\b\d{2}:\d{2}:\d{2}(?:\.\d+)?\b"


class NetFlowFlagsRegexBuilder(LogRegexBuilder):
    """Builder for TCP control flags."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="netflow_flags",
            category="sysadmin",
            description="Matches TCP flags like SYN, ACK, FIN, often in combination.",
            examples=["SYN", "ACK", "SYN | ACK", "RST,PSH"],
            non_examples=["FOO"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        flags = r"(SYN|ACK|FIN|RST|PSH|URG|ECE|CWR)"
        if self.subtype == "combo":
            return rf"\b{flags}(?:\s+\|?\s+{flags})*\b"
        return rf"\b{flags}\b"


class NetFlowDirectionRegexBuilder(LogRegexBuilder):
    """Builder for traffic direction indicators."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="netflow_direction",
            category="sysadmin",
            description="Matches keywords indicating traffic flow direction (ingress, egress, etc.).",
            examples=["inbound", "external", "ingress", "egress"],
            non_examples=["middle"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b(inbound|outbound|ingress|egress|internal|external|in|out)\b"


class NetFlowCIDRRegexBuilder(LogRegexBuilder):
    """Builder for CIDR network ranges."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="netflow_cidr",
            category="sysadmin",
            description="Matches IP address ranges in CIDR notation or hyphenated blocks.",
            examples=["192.168.1.0/24", "10.0.0.0-10.0.0.255"],
            non_examples=["192.168.1.256"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "cidr"}

    def build_pattern(self) -> str:
        ip = r"(?:\d{1,3}\.){3}\d{1,3}"
        if self.subtype == "range":
            return rf"\b{ip}-{ip}\b"
        return rf"\b{ip}/\d{{1,2}}\b"


class NetFlowDNSRegexBuilder(LogRegexBuilder):
    """Builder for DNS traffic patterns (domains, record types)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="netflow_dns",
            category="sysadmin",
            description="Matches domain names and DNS record types in traffic captures.",
            examples=["google.com", "api.example.org A", "mail.google.com MX"],
            non_examples=["google"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "domain"}

    def build_pattern(self) -> str:
        domain = r"([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}"
        if self.subtype == "record":
            return r"\s+(A|AAAA|CNAME|MX|NS|TXT|SOA|PTR)\b"
        return rf"\b{domain}\b"


class NetFlowHTTPTrafficRegexBuilder(LogRegexBuilder):
    """Builder for HTTP traffic patterns (methods, status)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="netflow_http_traffic",
            category="sysadmin",
            description="Matches HTTP methods, status codes, and protocol versions.",
            examples=["GET", "404", "HTTP/1.1", "POST"],
            non_examples=["PROTOCOL"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "method"}

    def build_pattern(self) -> str:
        if self.subtype == "method":
            return r"\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|CONNECT|TRACE)\b"
        elif self.subtype == "status":
            return r"\b[1-5]\d{2}\b"
        return r"\bHTTP/\d\.\d\b"


class NetFlowAnomalyRegexBuilder(LogRegexBuilder):
    """Builder for suspicious network traffic patterns."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="netflow_anomaly",
            category="sysadmin",
            description="Matches indicators of network attacks or unusual traffic bursts.",
            examples=["SYN flood", "suspicious traffic", "port scan"],
            non_examples=["normal"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        anomalies = r"(scan|flood|excessive|anomaly|suspicious|unusual|burst|exfiltration|tunneling|malicious)"
        if self.subtype == "scan":
            return r"\b(port\s+scan|SYN\s+scan|vertical\s+scan)\b"
        elif self.subtype == "flood":
            return r"\b(SYN\s+flood|UDP\s+flood|ICMP\s+flood)\b"
        return rf"\b{anomalies}\b"


class TimeOnlyRegexBuilder(LogRegexBuilder):
    """Builder for time-only formats (e.g., 12:34:56)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="time_only_log",
            category="sysadmin",
            description="Matches clock time in 12-hour or 24-hour formats with precision.",
            examples=["12:34:56", "02:30 PM", "23:59:59.999"],
            non_examples=["2026"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        if self.subtype == "12h":
            return r"\b\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM|am|pm)\b"
        elif self.subtype == "ms":
            return r"\b\d{2}:\d{2}:\d{2}\.\d{3}\b"
        return r"\b\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?\b"


class DateTimeRegexBuilder(LogRegexBuilder):
    """Builder for combined date and time stamps."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="datetime_log",
            category="sysadmin",
            description="Matches full date and time combinations, including log-specific formats.",
            examples=["2026-03-17 12:34:56", "[17/Mar/2026:12:34:56 +0000]"],
            non_examples=["12:34"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "iso"}

    def build_pattern(self) -> str:
        if self.subtype == "log":
            return r"\[\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}\s[+-]\d{4}\]"
        return r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}\b"


class TZRegexBuilder(LogRegexBuilder):
    """Builder for timezone identifiers and offsets."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="timezone_log",
            category="sysadmin",
            description="Matches numeric UTC offsets or common timezone abbreviations.",
            examples=["Z", "+02:00", "UTC", "PST"],
            non_examples=["AM"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "flexible"}

    def build_pattern(self) -> str:
        if self.subtype == "offset":
            return r"[+-]\d{2}:?\d{2}"
        elif self.subtype == "abbr":
            return r"\b(UTC|GMT|CET|PST|EST|JST)\b"
        return r"\b(Z|[+-]\d{2}:\d{2}|UTC|CET|PST|EST)\b"


class RelativeTimeRegexBuilder(LogRegexBuilder):
    """Builder for relative time expressions (e.g., 5 minutes ago)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="relative_time_log",
            category="sysadmin",
            description="Matches human-readable relative time phrases.",
            examples=["5 minutes ago", "2 hours", "10 seconds ago"],
            non_examples=["tomorrow"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b\d+\s?(seconds?|minutes?|hours?|days?)\s?(ago)?\b"


class TimeRangeRegexBuilder(LogRegexBuilder):
    """Builder for time ranges and intervals."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="time_range_log",
            category="sysadmin",
            description="Matches time intervals defined by two clock times.",
            examples=["12:00-14:00", "09:30 - 10:45"],
            non_examples=["12:00"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "default"}

    def build_pattern(self) -> str:
        return r"\b\d{2}:\d{2}\s?-\s?\d{2}:\d{2}\b"


class PrecisionTimeRegexBuilder(LogRegexBuilder):
    """Builder for fractional seconds precision (ms, micro, nano)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="precision_time_log",
            category="sysadmin",
            description="Matches the fractional part (milliseconds, etc.) of a timestamp.",
            examples=[".123", ".123456", ".999999999"],
            non_examples=["123"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "ms"}

    def build_pattern(self) -> str:
        if self.subtype == "ms":
            return r"\.\d{3}"
        elif self.subtype == "micro":
            return r"\.\d{6}"
        elif self.subtype == "nano":
            return r"\.\d{9}"
        return r"\.\d+"


class LogTimeRegexBuilder(LogRegexBuilder):
    """Builder for specialized log timestamps (Apache, Syslog)."""

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="log_time",
            category="sysadmin",
            description="Matches full timestamps including date and time as found in typical logs.",
            examples=["17/Mar/2026:12:34:56", "Mar 17 12:34:56"],
            non_examples=["12:34"],
        )

    def default_config(self) -> dict[str, Any]:
        return {"subtype": "apache"}

    def build_pattern(self) -> str:
        if self.subtype == "apache":
            return r"\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}"
        elif self.subtype == "syslog":
            return r"[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}"
        return r"\b\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}\b"
