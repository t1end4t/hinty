{
  inputs = {
    nixpkgs.url = "github:cachix/devenv-nixpkgs/rolling";
    systems.url = "github:nix-systems/default";

    devenv.url = "github:cachix/devenv";
    devenv.inputs.nixpkgs.follows = "nixpkgs";

    nixpkgs-python = {
      url = "github:cachix/nixpkgs-python";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # --- Added for packaging ---
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    # ------------------------------
  };

  nixConfig = {
    extra-trusted-public-keys = "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=";
    extra-substituters = "https://devenv.cachix.org";
  };

  outputs =
    {
      self,
      nixpkgs,
      devenv,
      systems,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
      ...
    }@inputs:
    let
      forEachSystem = nixpkgs.lib.genAttrs (import systems);

      # --- Added: uv2nix workspace loader ---
      workspace = uv2nix.lib.workspace.loadWorkspace {
        workspaceRoot = ./.;
      };

      overlay = workspace.mkPyprojectOverlay {
        sourcePreference = "wheel";
      };

      pythonSets = forEachSystem (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python3;
        in
        (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope
          (
            nixpkgs.lib.composeManyExtensions [
              pyproject-build-systems.overlays.wheel
              overlay

              # --- FIX: Add setuptools to tree-format build inputs ---
              # (final: prev: {
              #   tree-format = prev.tree-format.overrideAttrs (old: {
              #     nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [
              #       final.setuptools
              #     ];
              #   });
              # })
              # -------------------------------------------------------
            ]
          )
      );
    in
    {
      # Your original devenv devShell (unchanged)
      devShells = forEachSystem (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = devenv.lib.mkShell {
            inherit inputs pkgs;
            modules = [
              {
                packages = with pkgs; [
                  pyright
                  ruff
                ];

                languages.python = {
                  enable = true;
                  version = "3.13";
                  uv = {
                    enable = true;
                    sync.enable = true;
                  };
                };

                scripts.init-project.exec = ''
                  ${pkgs.uv}/bin/uv init
                  ${pkgs.uv}/bin/uv sync
                  ${pkgs.uv}/bin/uv add --dev -r dev-requirements.txt
                '';

                enterShell = ''
                  source .devenv/state/venv/bin/activate
                '';

                # env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
                #   pkgs.stdenv.cc.cc
                #   pkgs.zlib
                #   pkgs.libGL
                #   pkgs.glib
                # ];
              }
            ];
          };
        }
      );

      # --- Added: Nix package build output ---
      packages = forEachSystem (system: {
        default = pythonSets.${system}.mkVirtualEnv "hinty-env" workspace.deps.default;
      });
      # ---------------------------------------
    };
}
