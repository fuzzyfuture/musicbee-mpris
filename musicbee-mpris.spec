Name: musicbee-mpris
Version: 1
Release: 5
Summary: An MPRIS server for MusicBee running in Wine
License: MIT
Requires: systemd, xdotool

%description
An MPRIS server for MusicBee running in Wine

%build
pyinstaller --onefile %{_sourcedir}/main.py

%install
mkdir -p %{buildroot}%{_bindir}
install -m 755 dist/main %{buildroot}%{_bindir}/musicbee-mpris

%files
%{_bindir}/musicbee-mpris