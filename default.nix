{ lib, python3Packages, fetchPypi }:

let
  baml-py = python3Packages.buildPythonPackage rec {
    pname = "baml-py";
    version = "0.213.0";
    src = fetchPypi { inherit pname version; sha256 = "your-sha256-here"; };  # Replace with actual sha256 from nix-prefetch-url
    # Add propagatedBuildInputs if baml-py has dependencies (check PyPI)
  };
in
python3Packages.buildPythonPackage rec {
  pname = "hinty";
  version = "0.1.0";

  src = ./.; # Use the current directory as source

  # Dependencies from pyproject.toml (map to Nixpkgs names)
  propagatedBuildInputs = with python3Packages; [
    baml-py  # Use the custom derivation
    click
    python-dotenv # For 'dotenv'
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
    homepage = ""; # Add your repo URL if available
    license = licenses.mit; # Assuming MIT; update if different
    maintainers = [ ]; # Add yourself
  };
}
