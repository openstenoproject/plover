Name:    plover
Version: 4.0.0.dev1
Release: 1%{?dist}
Summary: Open Source Stenography Software
URL:     http://www.openstenoproject.org/
License: GPLv2+
Source0: https://github.com/openstenoproject/plover/archive/v%{version}.tar.gz
BuildArch: noarch
BuildRequires: python-qt5
BuildRequires: python3 >= 3.5
BuildRequires: python3-appdirs
BuildRequires: python3-babel
BuildRequires: python3-devel
BuildRequires: python3-docopt
BuildRequires: python3-hidapi
BuildRequires: python3-mock
BuildRequires: python3-pyserial >= 2.7
BuildRequires: python3-pytest
BuildRequires: python3-pytz
BuildRequires: python3-qt5
BuildRequires: python3-setuptools >= 20.7.0
BuildRequires: python3-setuptools_scm
BuildRequires: python3-xlib >= 0.16
Requires: python3
Requires: python3-appdirs
Requires: python3-dbus
Requires: python3-hidapi
Requires: python3-pyserial >= 2.7
Requires: python3-qt5
Requires: python3-setuptools >= 20.7.0
Requires: python3-xlib >= 0.16
Requires: wmctrl

%description
Plover is a free open source program intended to
bring realtime stenographic technology not just to stenographers, but also to
hackers, hobbyists, accessibility mavens, and all-around speed demons.

%prep
%setup -q -n %{name}-%{version}

%build
mkdir -p .deps
env PYTHONPATH="$PWD/.deps" %{__python3} -m easy_install -d .deps pyqt-distutils
env PYTHONPATH="$PWD/.deps" %{__python3} setup.py compile_catalog build_ui build

%install
env PYTHONPATH="$PWD/.deps" %py3_install
install -vDm644 -t "%{buildroot}/usr/share/pixmaps" plover/assets/plover.png
install -vDm644 -t "%{buildroot}/usr/share/applications" application/plover.desktop

%check
env PYTHONPATH="$PWD/.deps" %{__python3} setup.py test

%files
%doc README.md
%license LICENSE.txt
%{_bindir}/plover
%{python3_sitelib}/plover*
/usr/share/applications/plover.desktop
/usr/share/pixmaps/plover.png

%changelog

