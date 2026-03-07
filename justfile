set shell := ["pwsh", "-NoLogo", "-NoProfile", "-Command"]

run-demo:
    cd examples; vx uv run python run_workflow.py; vx uv run python demo.py


