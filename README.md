# NOTE:

1. To build hinty package to use

```nu
cd hinty/
nix build
```

2. To use it over-wide in NixOS or update it

```nu
cd hinty/
nix profile install .#
```

3. To update after code changes (hinty should exist)

```nu
cd hinty/
nix profile upgrade hinty
```

4. To remove profile

```nu
nix profile remove <name>
```

5. To remove result/ folder after built

```nu
rm -rf result
```
