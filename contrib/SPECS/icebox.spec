%define name icebox

Summary: icebox ecs
Name: %{name}
Version: %{version}
Release: %{release}%{?dist}
Source0: %{name}-%{version}.tar.gz
Source1: icebox.conf
Source2: icebox.logrotate
Source3: icebox-public
Source4: icebox-manage
Source5: icebox-worker
Source6: icebox-dba
Source7: icebox-shell
Source8: icebox-public.service
Source9: icebox-manage.service
Source10: icebox-worker.service
License: MIT
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: sekirocc@gmail.comNKNOWN>
Url: http://icebox.com

Requires: python-flask = 1:0.10.1, python-sqlalchemy = 1.0.11, python-alembic = 0.8.3
Requires: python-redis = 2.10.3, python-jsonschema = 2.3.0, python2-PyMySQL = 0.6.7, python-cinderclient >= 1.6.0, python-glanceclient = 1:2.0.0
Requires: python-keystoneclient = 1:2.3.1, python-neutronclient = 4.1.1, python-novaclient = 1:3.3.1, python-ceilometerclient = 2.3.0
Requires: python-ipython = 3.2.1
Requires: densefog >= 1.0.4

%description
UNKNOWN

%prep
%setup -n %{name}-%{version} -n %{name}-%{version}

%build
python setup.py build

%install
mkdir %{buildroot}/etc/icebox -p
%{__install} -p -D -m 0755 %{SOURCE1} %{buildroot}/etc/icebox/icebox.conf
%{__install} -p -D -m 0644 %{SOURCE2} %{buildroot}/etc/logrotate.d/icebox.logrotate
%{__install} -p -D -m 0755 %{SOURCE3} %{buildroot}/etc/init.d/icebox-public
%{__install} -p -D -m 0755 %{SOURCE4} %{buildroot}/etc/init.d/icebox-manage
%{__install} -p -D -m 0755 %{SOURCE5} %{buildroot}/etc/init.d/icebox-worker
%{__install} -p -D -m 0755 %{SOURCE6} %{buildroot}/usr/local/bin/icebox-dba
%{__install} -p -D -m 0755 %{SOURCE7} %{buildroot}/usr/local/bin/icebox-shell
%{__install} -p -D -m 0755 %{SOURCE8} %{buildroot}/usr/lib/systemd/system/icebox-public.service
%{__install} -p -D -m 0755 %{SOURCE9} %{buildroot}/usr/lib/systemd/system/icebox-manage.service
%{__install} -p -D -m 0755 %{SOURCE10} %{buildroot}/usr/lib/systemd/system/icebox-worker.service
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%pre

%post
mv /usr/bin/icebox-dba /usr/bin/.icebox-dba
mv /usr/bin/icebox-shell /usr/bin/.icebox-shell

%preun
if  [ $1 == 0 ];then
    rm -rf /usr/bin/.icebox-dba
    rm -rf /usr/bin/.icebox-shell
    if [ ! -z "`ps aux | grep icebox | grep -v grep`" ];then
        #killall -9 icebox  >/dev/null
        systemctl stop icebox-public.service
        systemctl stop icebox-manage.service
        systemctl stop icebox-worker.service
    fi
fi

%files -f INSTALLED_FILES
%defattr(-,root,root)
/etc/icebox/icebox.conf
/etc/logrotate.d/icebox.logrotate
/etc/init.d/icebox-public
/etc/init.d/icebox-manage
/etc/init.d/icebox-worker
/usr/local/bin/icebox-dba
/usr/local/bin/icebox-shell
/usr/lib/systemd/system/icebox-public.service
/usr/lib/systemd/system/icebox-manage.service
/usr/lib/systemd/system/icebox-worker.service

%config(noreplace) /etc/icebox/icebox.conf
