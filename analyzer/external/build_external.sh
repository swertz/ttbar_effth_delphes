#! /bin/sh

INSTALL_PREFIX=$PWD

# yaml-cpp

VERSION=0.5.2
FILENAME=release-$VERSION.tar.gz
FOLDER=yaml-cpp-release-$VERSION
URL=https://github.com/jbeder/yaml-cpp/archive/$FILENAME

curl -OL $URL

tar xf $FILENAME

pushd $FOLDER

# Patch CMakeLists.txt in order to be compatible with CMake 2.6
sed -i "311s/^/#/" CMakeLists.txt

mkdir build
cd build

cmake  -DBoost_NO_BOOST_CMAKE=BOOL:ON -DBOOST_ROOT:PATHNAME=/cvmfs/cp3.uclouvain.be/boost/boost-1.57.0-sl6_amd64_gcc49 -DYAML_CPP_BUILD_TOOLS=OFF -DYAML_CPP_BUILD_CONTRIB=OFF -DCMAKE_INSTALL_PREFIX:PATH=$INSTALL_PREFIX ..

make -j8

make install

popd

rm -f $FILENAME
rm -rf $FOLDER
