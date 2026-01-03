#!/bin/bash

VERSION=$(grep "^Version:" musicbee-mpris.spec | awk '{print $2}')

tar czf ~/rpmbuild/SOURCES/musicbee-mpris-${VERSION}.tar.gz --exclude=.git --transform="s,^,musicbee-mpris-${VERSION}/," .
rpmbuild -bb musicbee-mpris.spec