#!/bin/bash
set -e -x

package_name=icebox

echo 'prepare...'
rpmbuild_dir=/root/rpmbuild
ln -s `pwd`/contrib $rpmbuild_dir

cd core
version=`python setup.py --version`
release=1
cd ../

spec=$package_name.spec
sed -i "2i\%define version ${version}\n%define release ${release}" contrib/SPECS/$spec

echo 'rpmbuild...'
cd core
python setup.py sdist
cp dist/$package_name-$version.tar.gz ../contrib/SOURCES
cd ../

yum-builddep -y contrib/SPECS/$spec
rpmbuild -ba contrib/SPECS/$spec --define "dist .el7"

echo 'uploading...'
wget http://192.168.31.110:8080/upload.py
for filename in `find ./ -name *.rpm`
do
    if [[ "$version" =~ "dev" ]]; then
        python upload.py -f $filename -r icebox-development
    else
        python upload.py -f $filename -r icebox
    fi
done
