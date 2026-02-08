{ pkgs, ... }: {
  channel = "stable-23.11"; # or "unstable"
  packages = [
    pkgs.python311
    pkgs.python311Packages.requests
    pkgs.python311Packages.google-generativeai
    pkgs.python311Packages.pandas
    pkgs.python311Packages.python-dotenv
    pkgs.nodejs_20
  ];
  env = {};
  idx = {
    extensions = [
      "ms-python.python"
    ];
    previews = {
      enable = true;
      previews = {
        web = {
          command = ["npm" "run" "dev" "--" "--port" "$PORT" "--hostname" "0.0.0.0"];
          cwd = "frontend";
          manager = "web";
        };
      };
    };
    workspace = {
      onCreate = {
        install-python = "python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt";
        install-frontend = "cd frontend && npm install";
      };
      onStart = {
        run-frontend = "cd frontend && npm run dev";
      };
    };
  };
}
