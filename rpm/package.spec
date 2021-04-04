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
BuildRequires: python3-pyserial >= 2.7
BuildRequires: python3-pytest
BuildRequires: python3-pytz
BuildRequires: python3-qt5
BuildRequires: python3-setuptools >= 38.2.4
BuildRequires: python3-setuptools_scm
BuildRequires: python3-wcwidth >= 0.1.7
BuildRequires: python3-xlib >= 0.16
Requires: python3
Requires: python3-appdirs
Requires: python3-dbus
Requires: python3-pyserial >= 2.7
Requires: python3-qt5 >= 5.8.2
Requires: python3-setuptools >= 38.2.4
Requires: python3-wcwidth >= 0.1.7
Requires: python3-xlib >= 0.16

%description
Plover is a free open source program intended to
bring realtime stenographic technology not just to stenographers, but also to
hackers, hobbyists, accessibility mavens, and all-around speed demons.

%prep
%setup -q -n %{name}-%{version}

%build
sed -i '/^\s*PyQt5\b.*/d' setup.cfg
%{__python3} setup.py compile_catalog build_ui build

%install
%py3_install
install -vDm644 -t "%{buildroot}/usr/share/pixmaps" plover/assets/plover.png
install -vDm644 -t "%{buildroot}/usr/share/applications" linux/plover.desktop

%check
%{__python3} setup.py test

%files
%doc README.md
%license LICENSE.txt
%{_bindir}/plover
%{python3_sitelib}/plover*
/usr/share/applications/plover.desktop
/usr/share/pixmaps/plover.png

%changelog

