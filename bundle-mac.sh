#!/bin/sh
cargo bundle --release
mv "target/release/bundle/osx/athenaCL.app/Contents/Resources/resources" "target/release/bundle/osx/athenaCL.app/Contents/MacOS/"
