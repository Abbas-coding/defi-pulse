"""Execute the local baseline notebook and export a standalone HTML copy."""

import argparse
import json
import os
from pathlib import Path
import socket
import sys
import tempfile


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", type=Path,
                        default=root / "notebooks/01_defi_pulse_end_to_end.ipynb")
    args = parser.parse_args()
    # Jupyter kernels communicate over local sockets. Fail immediately in a
    # restricted environment instead of hanging during kernel startup/cleanup.
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
    import nbformat
    from nbclient import NotebookClient
    from nbconvert import HTMLExporter
    from jupyter_client import KernelManager
    from jupyter_client.kernelspec import KernelSpecManager

    path = args.notebook.resolve()
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    # Keep kernel/runtime/cache files local to this execution, not the user's home.
    with tempfile.TemporaryDirectory(prefix="defi-pulse-notebook-") as runtime:
        runtime = Path(runtime)
        kernel_dir = runtime / "kernels/python3"
        kernel_dir.mkdir(parents=True)
        (kernel_dir / "kernel.json").write_text(json.dumps({
            "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "DeFi Pulse project environment", "language": "python",
        }))
        env = os.environ.copy()
        env.update(JUPYTER_RUNTIME_DIR=str(runtime / "runtime"),
                   IPYTHONDIR=str(runtime / "ipython"), MPLCONFIGDIR=str(runtime / "matplotlib"))
        manager = KernelManager(kernel_name="python3", ip="127.0.0.1", connection_file=str(runtime / "connection.json"),
                                kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(runtime / "kernels")]))
        client = NotebookClient(notebook, timeout=300, startup_timeout=60, kernel_name="python3", km=manager,
                                resources={"metadata": {"path": str(root)}})
        def before_cell(cell, cell_index):
            if cell.cell_type == "code":
                print(f"Executing code cell {cell_index + 1}/{len(notebook.cells)}", flush=True)
        client.on_cell_start = before_cell
        print("Starting notebook kernel on loopback; no external data requests.", flush=True)
        # Explicit cleanup is required because the manager is provided by this script.
        try:
            client.execute(cwd=str(root), env=env)
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
            manager.cleanup_resources()
    errors = [output for cell in notebook.cells if cell.cell_type == "code"
              for output in cell.outputs if output.output_type == "error"]
    if errors:
        raise RuntimeError("Notebook execution produced errors; outputs were not published.")
    nbformat.write(notebook, path)
    exporter = HTMLExporter()
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True
    exporter.embed_images = True
    body, _ = exporter.from_notebook_node(notebook)
    # Markdown references are relative to notebooks/; HTML is three directories
    # below the repository root, so keep its project-document links usable too.
    body = body.replace('href="../docs/', 'href="../../../docs/')
    html = root / "data/notebook_outputs/defi_pulse_baseline/notebook.html"
    html.parent.mkdir(parents=True, exist_ok=True)
    html.write_text(body, encoding="utf-8")
    print(f"Executed notebook: {path}", flush=True)
    print(f"Standalone HTML: {html}", flush=True)


if __name__ == "__main__":
    main()
