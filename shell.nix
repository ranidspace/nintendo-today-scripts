{
  pkgs ? import <nixpkgs> { },
}:
pkgs.mkShell {
  # nativeBuildInputs is usually what you want -- tools you need to run
  nativeBuildInputs = with pkgs.buildPackages; [
    (python3.withPackages(ps: with ps; [ icalendar requests beautifulsoup4 ]))
  ];
}
