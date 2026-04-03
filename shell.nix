{
  pkgs ? import <nixpkgs> { },
}:
pkgs.mkShellNoCC {
  # nativeBuildInputs is usually what you want -- tools you need to run
  nativeBuildInputs = with pkgs.buildPackages; [
    (python3.withPackages (
      ps: with ps; [
        icalendar
        niquests
        beautifulsoup4
        ffmpeg-python
        aiofile
      ]
    ))
  ];
}
