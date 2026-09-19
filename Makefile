MIRI_FLAGS := -Zmiri-disable-isolation -Zmiri-tree-borrows
MIRI_SYSROOT := $(CURDIR)/target/miri-sysroot
COVERAGE_LCOV := target/athenacl-lcov.info
CRAP_REPORT := target/athenacl-crap.md
CRAP_EXCLUDES := --exclude '**/build.rs' --exclude '**/benches/**' --exclude '**/examples/**' --exclude '**/tests.rs' --exclude '**/*_tests.rs' --exclude '**/tests/**'
SIMILARITY_ARGS := src --threshold 0.92 --min-lines 12 --min-tokens 80 --fail-on-duplicates

.PHONY: init check test-all lint fmt code-health pack-macos

init:
	git lfs pull

check:
	cargo check --all-features --all-targets

test:
	cargo nextest run --all-features --all-targets

lint:
	@status=0; \
	cargo clippy --all-targets --all-features -- -D warnings || status=$$?; \
	cargo +nightly fmt --check --all || status=$$?; \
	RUSTDOCFLAGS="-D warnings" cargo doc --all-features \
		--no-deps --document-private-items || status=$$?; \
	exit $$status

fmt:
	cargo +nightly fmt --all

code-health:
	similarity-rs $(SIMILARITY_ARGS)
	cargo machete --skip-target-dir
	cargo llvm-cov nextest --all-features --all-targets --lcov --output-path $(COVERAGE_LCOV)
	cargo crap --workspace --lcov $(COVERAGE_LCOV) $(CRAP_EXCLUDES) --format markdown --output $(CRAP_REPORT)
	cargo crap --workspace --lcov $(COVERAGE_LCOV) $(CRAP_EXCLUDES) --summary --fail-above
	MIRI_SYSROOT="$(MIRI_SYSROOT)" cargo +nightly miri setup
	@set -e; \
	MIRI_SYSROOT="$(MIRI_SYSROOT)" MIRIFLAGS="$(MIRI_FLAGS)" cargo +nightly miri test  --all-features; \

pack-macos:
	cargo bundle --release
	mv "target/release/bundle/osx/athenaCL.app/Contents/Resources/resources" "target/release/bundle/osx/athenaCL.app/Contents/MacOS/"
	open "target/release/build/osx"
