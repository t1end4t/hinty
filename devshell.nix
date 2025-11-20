{
  pkgs,
  inputs,
  devenv,
  ...
}:

# This function defines the devShell
devenv.lib.mkShell {
  inherit inputs pkgs;
  modules = [
    {
      packages = with pkgs; [
        pyright
        ruff
      ];

      languages.python = {
        enable = true;
        version = "3.11";
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

      env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
        pkgs.stdenv.cc.cc
        pkgs.zlib
        pkgs.libGL
        pkgs.glib
      ];
    }
  ];
}
