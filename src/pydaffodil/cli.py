import argparse
import sys
from pathlib import Path

import yaml

from .core import Daffodil, parse_inventory_ini_file

def load_config(path):
    cfg_path = Path(path)
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg["__config_dir"] = str(cfg_path.parent)
    return cfg


def load_inventory_hosts(cfg):
    inv_file = pick(cfg, "inventoryFile", "inventoryYml")
    if not inv_file:
        return []
    inv_path = Path(inv_file)
    if not inv_path.is_absolute():
        inv_path = Path(cfg.get("__config_dir") or ".") / inv_path
    group_name = pick(cfg, "inventoryGroup", "inventory_group")
    return parse_inventory_ini_file(str(inv_path), group_name if group_name else None)


def normalize_hosts(cfg):
    hosts = cfg.get("hosts") or []
    if hosts:
        return hosts
    inv_hosts = load_inventory_hosts(cfg)
    if inv_hosts:
        return inv_hosts
    if (cfg.get("remote_host") and cfg.get("remote_user")) or (cfg.get("remoteHost") and cfg.get("remoteUser")):
        return [
            {
                "name": "default",
                "host": cfg.get("remote_host") or cfg.get("remoteHost"),
                "user": cfg.get("remote_user") or cfg.get("remoteUser"),
                "port": cfg.get("port", 22),
                "remote_path": cfg.get("remote_path") or cfg.get("remotePath"),
            }
        ]
    return []

def pick(cfg, *keys, default=None):
    for k in keys:
        if k in cfg and cfg.get(k) is not None:
            return cfg.get(k)
    return default


def build_steps(cli, steps):
    built = []
    for s in steps:
        name = s.get("name") or s.get("step") or s.get("type") or "step"
        stype = s.get("type")
        if stype == "local":
            built.append({"step": name, "command": lambda cmd=s.get("command"): cli.run_command(cmd)})
        elif stype == "ssh":
            built.append({"step": name, "command": lambda cmd=s.get("command"): cli.ssh_command(cmd)})
        elif stype == "transfer":
            built.append(
                {
                    "step": name,
                    "command": lambda lp=pick(s, "localPath", "local_path"), dp=pick(s, "destinationPath", "destination_path"): cli.transfer_files(lp, dp),
                }
            )
        else:
            raise ValueError(f"Unsupported step type: {stype}")
    return built


def run(config, watch_mode=False):
    steps = config.get("steps") or []
    if not steps:
        raise ValueError("No steps provided in YAML config.")
    for s in steps:
        stype = (s.get("type") or "").strip().lower()
        if stype not in {"local", "ssh", "transfer"}:
            raise ValueError(f"Unsupported step type: {s.get('type')}")
    hosts = normalize_hosts(config)
    if not hosts:
        raise ValueError("No hosts found in YAML config.")

    for host in hosts:
        cli = Daffodil(
            remote_user=host.get("user") or pick(config, "remoteUser", "remote_user"),
            remote_host=host.get("host") or pick(config, "remoteHost", "remote_host"),
            remote_path=host.get("remote_path") or host.get("remotePath") or pick(config, "remotePath", "remote_path"),
            port=host.get("port") or pick(config, "port", default=22),
            ssh_key_path=pick(config, "sshKeyPath", "ssh_key_path"),
            ssh_key_pass=pick(config, "sshKeyPass", "ssh_key_pass"),
            scp_ignore=pick(config, "ignoreFile", "scp_ignore", default=".scpignore"),
        )
        built_steps = build_steps(cli, steps)
        if watch_mode:
            w = config.get("watch") or {}
            cli.watch(
                paths=w.get("paths"),
                debounce=w.get("debounce", 2.0),
                repo_path=pick(w, "repoPath", "repo_path"),
                branch=w.get("branch"),
                branches=w.get("branches"),
                tags=w.get("tags", True),
                tag_pattern=pick(w, "tagPattern", "tag_pattern"),
                events=w.get("events"),
                interval=w.get("interval", 5.0),
            ).deploy(built_steps)
        else:
            cli.deploy(built_steps)


def main():
    """Entry point for the `pydaffodil` console script and `python -m pydaffodil.cli`."""
    try:
        parser = argparse.ArgumentParser(description="pydaffodil YAML-based deployment CLI")
        parser.add_argument("--config", required=False, default=".daffodil.yml", help="Path to deployment YAML file")
        parser.add_argument("--watch", action="store_true", help="Run in watch mode")
        args = parser.parse_args()
        if Path(args.config).name != ".daffodil.yml":
            raise ValueError("Config filename must be exactly '.daffodil.yml' (use example/.daffodil.yml).")

        cfg = load_config(args.config)
        run(cfg, args.watch)
    except Exception as e:
        print(f"pydaffodil CLI failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
