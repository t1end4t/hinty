{
  lib,
  pythonPackages,
}:

# This function defines the `hinty` package.
pythonPackages.buildPythonPackage rec {
  # Use the name and version from your pyproject.toml
  pname = "hinty";
  version = "0.1.0";

  # The source is the directory containing this flake.nix (up one level)
  src = lib.cleanSource ../.;

  # Tell Nix to build it using the information in pyproject.toml
  format = "pyproject";

  # Map the Python dependencies to Nix store packages.
  # NOTE: 'baml-py' is likely not in Nixpkgs and will fail the build.
  # This list assumes the other standard packages are present.
  propagatedBuildInputs = with pythonPackages; [
    # baml-py # <--- Uncomment and fix with an overlay if needed!
    click
    python-dotenv # Nix package name is often 'python-dotenv'
    loguru
    platformdirs
    prompt-toolkit
    pydantic
    rich
    typing-extensions
  ];

  # If you don't have tests, you may set:
  # doCheck = false;
}
