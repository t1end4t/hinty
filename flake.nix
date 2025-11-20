{
  inputs = {
    nixpkgs.url = "github:cachix/devenv-nixpkgs/rolling";
    systems.url = "github:nix-systems/default";

    devenv.url = "github:cachix/devenv";
    devenv.inputs.nixpkgs.follows = "nixpkgs";

    nixpkgs-python = {
      url = "github:cachix/nixpkgs-python";
      inputs = {
        nixpkgs.follows = "nixpkgs";
      };
    };
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
      ...
    }@inputs:
    let
      forEachSystem = nixpkgs.lib.genAttrs (import systems);
    in
    {
      # ------------------------------------------------------------------
      # 1. PACKAGES: Import the package definition from packages/hinty.nix
      # ------------------------------------------------------------------
      packages = forEachSystem (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          # Define python for simplicity
          python = pkgs.python311;
        in
        {
          # Use callPackage to load the function and pass arguments automatically
          hinty = pkgs.callPackage ./packages/hinty.nix {
            inherit python;
            pythonPackages = python.pkgs;
          };

          # Make the package runnable with 'nix run .'
          default = self.packages.${system}.hinty;
        }
      );

      # ------------------------------------------------------------------
      # 2. DEV SHELLS: Import the devShell definition from devshell.nix
      # ------------------------------------------------------------------
      devShells = forEachSystem (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          # Use callPackage to load the devshell configuration
          default = pkgs.callPackage ./devshell.nix {
            inherit inputs pkgs devenv;
          };
        }
      );
    };
}
