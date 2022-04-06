# To make an Arch package
`arch/`
This builds a package by first downloading it off PyPi, independent of the git
repo.

`arch-git/`
This builds a package by downlowing from git repo and compiling it.

Steps -
* Change the package version
* Run `namcap PKGBUILD` to do a sanity check
* Run `makepkg` from this directory
* Check `pacman -Qlp [packagefile]`
* Check `pacman -Qip [packagefile]`

To install -
* Run `makepkg -si`
