Name: musicbee-mpris
Version: 1.1.1
Release: 1
Summary: An MPRIS server for MusicBee running in Wine
Source0: musicbee-mpris-%{version}.tar.gz
License: MIT
Requires: systemd, xdotool

%global debug_package %{nil}

%description
An MPRIS server for MusicBee running in Wine

%prep
%setup -q

%build
pyinstaller --onefile --distpath ./dist main.py

%install
mkdir -p %{buildroot}%{_bindir}
install -m 755 dist/main %{buildroot}%{_bindir}/musicbee-mpris

%files
%{_bindir}/musicbee-mpris