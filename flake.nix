{
  description = "CodeCompanion Groundwork — reproducible dev + Chrome-verification environment (Python stdlib app, chromium, Node for chrome-devtools-mcp)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forEachSystem = nixpkgs.lib.genAttrs systems;
    in
    {
      devShells = forEachSystem (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.mkShell {
            name = "codecompanion-groundwork";

            buildInputs = with pkgs; [
              python312 # the app + tests are stdlib-only: no venv needed
              chromium # headless browser for tools/chrome_sweep.py
              nodejs_24 # runs chrome-devtools-mcp via npx (pinned 1.9.0)
              git
              jq
            ];

            shellHook = ''
              export CHROME_EXECUTABLE="''${CHROME_EXECUTABLE:-$(command -v chromium || command -v chromium-browser || command -v google-chrome || true)}"
              echo "groundwork shell: $(python3 --version 2>&1), node $(node --version 2>&1)"
              echo "chrome: ''${CHROME_EXECUTABLE:-none found}"
              echo "run: python3 -m unittest discover -s tests"
              echo "verify in a real browser: nix run .#chrome-verify"
            '';
          };
        });

      apps = forEachSystem (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          # Reproducible Chrome verification sweep: temp fixture DB +
          # local server + headless chrome-devtools-mcp session, all
          # torn down afterwards. Fails nonzero on any failing check.
          chrome-verify = {
            type = "app";
            program = toString (pkgs.writeShellScript "chrome-verify" ''
              export PATH="${pkgs.python312}/bin:${pkgs.chromium}/bin:${pkgs.nodejs_24}/bin:$PATH"
              export CHROME_EXECUTABLE="''${CHROME_EXECUTABLE:-$(command -v chromium)}"
              exec python3 "''${CHROME_VERIFY_ROOT:-$(pwd)}/tools/chrome_sweep.py" "$@"
            '');
          };
        });
    };
}
