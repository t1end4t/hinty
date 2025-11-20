{ lib, python3Packages }:

python3Packages.buildPythonPackage rec {
  pname = "hinty";
  version = "0.1.0";

  src = ./.;  # Use the current directory as source

  # Dependencies from pyproject.toml (map to Nixpkgs names)
  propagatedBuildInputs = with python3Packages; [
    baml-py  # Version >=0.213.0; ensure it's in Nixpkgs or add custom derivation
    click
    python-dotenv  # For 'dotenv'
    loguru
    platformdirs
    prompt-toolkit
    pydantic
    rich
    typing-extensions
  ];

  # Nix will use pyproject.toml for build and entry points (e.g., 'hinty' script)
  # No need for custom build steps unless you have extras

  meta = with lib; {
    description = "Hinty CLI tool for conversation routing and more";
    homepage = "";  # Add your repo URL if available
    license = licenses.mit;  # Assuming MIT; update if different
    maintainers = [ ];  # Add yourself
  };
}
