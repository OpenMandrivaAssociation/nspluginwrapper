# NOTE: this is a Linux-specific package, don't use the embedded
# viewer on non-Linux platforms.
%define name	nspluginwrapper
%define version	1.1.0
#define svndate	20061227
%define rel	2
%define release	%mkrel %{?svndate:0.%{svndate}.}%{rel}

# define 32-bit arch of multiarch platforms
%define arch_32 %{nil}
%ifarch x86_64
%define arch_32 i386
%endif
%ifarch ppc64
%define arch_32 ppc
%endif
%ifarch sparc64
%define arch_32 sparc
%endif

# define to build a biarch package
%define build_biarch		0
%if "%{_arch}:%{arch_32}" == "x86_64:i386"
%define build_biarch		1
%endif
%if "%{_arch}:%{arch_32}" == "ppc64:ppc"
%define build_biarch		1
%endif
%{expand: %{?_with_biarch:	%%global build_biarch 1}}
%{expand: %{?_without_biarch:	%%global build_biarch 0}}

# define target architecture of plugins we want to support
%define target_arch i386
%ifarch ppc64
%define target_arch ppc
%endif

# define target operating system of plugins we want to support
%define target_os linux

# define nspluginswrapper libdir (invariant, including libdir)
%define pkglibdir %{_prefix}/lib/%{name}

# define mozilla plugin dir
%define plugindir %{_libdir}/mozilla/plugins

Summary:	A compatibility layer for Netscape 4 plugins
Name:		%{name}
Version:	%{version}
Release:	%{release}
License:	GPLv2+
Group:		Networking/WWW
URL:		http://gwenole.beauchesne.info/projects/nspluginwrapper/
Source0:	%{name}-%{version}%{?svndate:-%{svndate}}.tar.bz2
# from Fedora
Patch2:         nspluginwrapper-1.1.0-runtime-restart.patch
Patch3:         nspluginwrapper-1.1.0-fork.patch
Patch4:         nspluginwrapper-0.9.91.5-shutdown.patch
Patch5:         nspluginwrapper-0.9.91.5-sleep.patch
BuildRequires:	curl-devel
BuildRequires:	gtk+2-devel
BuildRequires:	libxt-devel
Provides:	%{name}-%{_arch} = %{version}
Requires(post):	 %{name}-%{target_arch} = %{version}-%{release}
Requires(preun): %{name}-%{target_arch} = %{version}-%{release}
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
nspluginwrapper makes it possible to use Netscape 4 compatible plugins
compiled for %{target_os}/%{target_arch} into Mozilla for another architecture, e.g. x86_64.

This package consists in:
  * npviewer: the plugin viewer
  * npwrapper.so: the browser-side plugin
  * nspluginwrapper: a tool to manage plugins installation and update

%if %{build_biarch}
%package %{target_arch}
Summary:	A viewer for %{target_os}/%{target_arch} compiled Netscape 4 plugins
Group:		Networking/WWW
%if "%{target_arch}" == "i386"
Requires:	linux32
%endif

%description %{target_arch}
nspluginwrapper makes it possible to use Netscape 4 compatible plugins
compiled for %{target_os}/%{target_arch} into Mozilla for another architecture, e.g. x86_64.

This package consists in:
  * npviewer: the plugin viewer
  * npwrapper.so: the browser-side plugin
  * nspluginwrapper: a tool to manage plugins installation and update

This package provides the npviewer program for %{target_os}/%{target_arch}.
%endif

%prep

%setup -q
%patch2 -p1 -b .restart
%patch3 -p1 -b .fork
%patch4 -p1 -b .shutdown
%patch5 -p1 -b .sleep

%build
export CFLAGS="$RPM_OPT_FLAGS"
export CXXFLAGS="$RPM_OPT_FLAGS"

%if %{build_biarch}
biarch="--with-biarch"
%else
biarch="--without-biarch"
%endif
mkdir objs
pushd objs
../configure --prefix=%{_prefix} --target-cpu=%{target_arch} --with-viewer $biarch --linux-only
# XXX configure option
echo "DONT_STRIP = yes" >> config-host.mak
%make
popd

%install
rm -rf $RPM_BUILD_ROOT

make -C objs install DESTDIR=$RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT%{plugindir}
ln -s %{pkglibdir}/%{_arch}/%{_os}/npwrapper.so $RPM_BUILD_ROOT%{plugindir}/npwrapper.so

%clean
rm -rf $RPM_BUILD_ROOT

%post
if [ $1 = 1 ]; then
  %{_bindir}/%{name} -v -a -i
else
  %{_bindir}/%{name} -v -a -u
  %if %{mdkversion} >= 200810
    if [ -f /usr/lib/mozilla/plugins/libflashplayer.so ] && [ ! -f %{plugindir}/npwrapper.libflashplayer.so ]; then
      %{_bindir}/%{name} -v -i /usr/lib/mozilla/plugins/libflashplayer.so
    fi
  %endif
fi

%preun
if [ $1 = 0 ]; then
  %{_bindir}/%{name} -v -a -r
fi

# Flash Player
%triggerin -- FlashPlayer < 9.0.115.0
if [ -f %{plugindir}/npwrapper.libflashplayer.so ]; then
  %{_bindir}/%{name} -v -u %{plugindir}/npwrapper.libflashplayer.so
else
  %{_bindir}/%{name} -v -i /usr/lib/mozilla/plugins/libflashplayer.so
fi

%triggerpostun -- FlashPlayer < 9.0.115.0
if [ ! -f /usr/lib/mozilla/plugins/libflashplayer.so ]; then
  %{_bindir}/%{name} -v -r %{plugindir}/npwrapper.libflashplayer.so
fi

%triggerin -- FlashPlayer-plugin
if [ -f %{plugindir}/npwrapper.libflashplayer.so ]; then
  %{_bindir}/%{name} -v -u %{plugindir}/npwrapper.libflashplayer.so
else
  %{_bindir}/%{name} -v -i /usr/lib/mozilla/plugins/libflashplayer.so
fi

%triggerpostun -- FlashPlayer-plugin
if [ ! -f /usr/lib/mozilla/plugins/libflashplayer.so ]; then
  %{_bindir}/%{name} -v -r %{plugindir}/npwrapper.libflashplayer.so
fi

# Acrobat Reader
%triggerin -- acroread5-nppdf, acroread-nppdf
if [ -f %{plugindir}/npwrapper.nppdf.so ]; then
  %{_bindir}/%{name} -v -u %{plugindir}/npwrapper.nppdf.so
else
  %{_bindir}/%{name} -v -i /usr/lib/mozilla/plugins/nppdf.so
fi

%triggerpostun -- acroread5-nppdf, acroread-nppdf
if [ ! -f /usr/lib/mozilla/plugins/nppdf.so ]; then
  %{_bindir}/%{name} -v -r %{plugindir}/npwrapper.nppdf.so
fi

# Real Player 8
%triggerin -- RealPlayer-rpnp < 10
if [ -f %{plugindir}/npwrapper.rpnp.so ]; then
  %{_bindir}/%{name} -v -u %{plugindir}/npwrapper.rpnp.so
else
  %{_bindir}/%{name} -v -i /usr/lib/mozilla/plugins/rpnp.so
fi

%triggerpostun -- RealPlayer-rpnp < 10
if [ ! -f /usr/lib/mozilla/plugins/rpnp.so ]; then
  %{_bindir}/%{name} -v -r %{plugindir}/npwrapper.rpnp.so
fi

# Real Player 10
%triggerin -- RealPlayer-rpnp >= 10
if [ -f %{plugindir}/npwrapper.nphelix.so ]; then
  %{_bindir}/%{name} -v -u %{plugindir}/npwrapper.nphelix.so
else
  %{_bindir}/%{name} -v -i /usr/lib/mozilla/plugins/nphelix.so
fi

%triggerpostun -- RealPlayer-rpnp >= 10
if [ ! -f /usr/lib/mozilla/plugins/nphelix.so ]; then
  %{_bindir}/%{name} -v -r %{plugindir}/npwrapper.nphelix.so
fi

%files
%defattr(-,root,root)
%doc README NEWS
%{_bindir}/%{name}
%{_bindir}/nspluginplayer
%{plugindir}/npwrapper.so
%dir %{pkglibdir}
%dir %{pkglibdir}/noarch
%{pkglibdir}/noarch/npviewer
%{pkglibdir}/noarch/mkruntime
%dir %{pkglibdir}/%{_arch}
%dir %{pkglibdir}/%{_arch}/%{_os}
%{pkglibdir}/%{_arch}/%{_os}/npconfig
%if ! %{build_biarch}
%{pkglibdir}/%{_arch}/%{_os}/npviewer
%{pkglibdir}/%{_arch}/%{_os}/npviewer.bin
%{pkglibdir}/%{_arch}/%{_os}/libxpcom.so
%{pkglibdir}/%{_arch}/%{_os}/libnoxshm.so
%endif
%{pkglibdir}/%{_arch}/%{_os}/npplayer
%{pkglibdir}/%{_arch}/%{_os}/npwrapper.so

%if %{build_biarch}
%files %{target_arch}
%defattr(-,root,root)
%dir %{pkglibdir}/%{target_arch}
%dir %{pkglibdir}/%{target_arch}/%{target_os}
%{pkglibdir}/%{target_arch}/%{target_os}/npviewer
%{pkglibdir}/%{target_arch}/%{target_os}/npviewer.bin
%{pkglibdir}/%{target_arch}/%{target_os}/libxpcom.so
%{pkglibdir}/%{target_arch}/%{target_os}/libnoxshm.so
%endif
