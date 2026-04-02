import os
import subprocess
import sys
import tempfile
import textwrap
import unittest


class TestPyDaffodilCLI(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "pydaffodil.cli", *args],
            cwd=os.path.dirname(__file__),
            text=True,
            capture_output=True,
        )

    def test_cli_requires_config(self):
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".daffodil.yml", result.stderr)

    def test_cli_fails_without_hosts(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = os.path.join(td, ".daffodil.yml")
            with open(cfg, "w", encoding="utf-8") as f:
                f.write(
                    textwrap.dedent(
                        """
                        steps:
                          - name: Build
                            type: local
                            command: echo hello
                        """
                    ).strip()
                )
            result = self.run_cli("--config", cfg)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("No hosts found in YAML config", result.stderr)

    def test_cli_fails_unsupported_step_type(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = os.path.join(td, ".daffodil.yml")
            with open(cfg, "w", encoding="utf-8") as f:
                f.write(
                    textwrap.dedent(
                        """
                        hosts:
                          - name: web1
                            host: 127.0.0.1
                            user: deploy
                        steps:
                          - name: Invalid
                            type: invalid
                        """
                    ).strip()
                )
            result = self.run_cli("--config", cfg)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsupported step type", result.stderr)

    def test_cli_reads_hosts_from_inventory_ini(self):
        with tempfile.TemporaryDirectory() as td:
            inv = os.path.join(td, "inventory.ini")
            with open(inv, "w", encoding="utf-8") as f:
                f.write(
                    textwrap.dedent(
                        """
                        [webservers]
                        web1 host=127.0.0.1 user=deploy port=22
                        """
                    ).strip()
                )
            cfg = os.path.join(td, ".daffodil.yml")
            with open(cfg, "w", encoding="utf-8") as f:
                f.write(
                    textwrap.dedent(
                        """
                        inventoryFile: inventory.ini
                        inventoryGroup: webservers
                        steps:
                          - name: Invalid
                            type: invalid
                        """
                    ).strip()
                )
            result = self.run_cli("--config", cfg)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsupported step type", result.stderr)

    def test_cli_prefers_hosts_over_inventory_when_hosts_present(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = os.path.join(td, ".daffodil.yml")
            with open(cfg, "w", encoding="utf-8") as f:
                f.write(
                    textwrap.dedent(
                        """
                        hosts:
                          - name: web1
                            host: 127.0.0.1
                            user: deploy
                        inventoryFile: missing.ini
                        steps:
                          - name: Invalid
                            type: invalid
                        """
                    ).strip()
                )
            result = self.run_cli("--config", cfg)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsupported step type", result.stderr)


if __name__ == "__main__":
    unittest.main()
