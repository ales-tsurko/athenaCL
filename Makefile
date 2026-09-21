COVERAGE_LCOV := target/athenacl-lcov.info
CRAP_REPORT := target/athenacl-crap.md
CRAP_EXCLUDES := --exclude '**/build.rs' --exclude '**/benches/**' --exclude '**/examples/**' --exclude '**/tests.rs' --exclude '**/*_tests.rs' --exclude '**/tests/**'
SIMILARITY_ARGS := src --threshold 0.92 --min-lines 12 --min-tokens 80 --fail-on-duplicates

.PHONY: init check run test-all screenshots lint fmt code-health pack-macos

init:
	git lfs pull

check:
	cargo check --all-features --all-targets

run:
	cargo run

test:
	cargo nextest run --all-features --all-targets

# the manual's screenshots, into doc/src/images
screenshots:
	cargo test --lib app::app::screenshots -- --ignored

lint:
	@status=0; \
	cargo clippy --all-targets --all-features -- -D warnings || status=$$?; \
	cargo +nightly fmt --check --all || status=$$?; \
	rumdl fmt --check . || status=$$?; \
	RUSTDOCFLAGS="-D warnings" cargo doc --all-features \
		--no-deps --document-private-items || status=$$?; \
	exit $$status

fmt:
	cargo +nightly fmt --all
	rumdl fmt .

code-health:
	similarity-rs $(SIMILARITY_ARGS)
	cargo machete --skip-target-dir
	cargo llvm-cov nextest --all-features --all-targets --lcov --output-path $(COVERAGE_LCOV)
	cargo crap --workspace --lcov $(COVERAGE_LCOV) $(CRAP_EXCLUDES) --format markdown --output $(CRAP_REPORT)
	cargo crap --workspace --lcov $(COVERAGE_LCOV) $(CRAP_EXCLUDES) --summary --fail-above

pack-macos:
	cargo bundle --release
	mv "target/release/bundle/osx/athenaCL.app/Contents/Resources/resources" "target/release/bundle/osx/athenaCL.app/Contents/MacOS/"
	mv "target/release/bundle/osx/athenaCL.app/Contents/Resources/doc/src" "target/release/bundle/osx/athenaCL.app/Contents/MacOS/manual"
	rmdir "target/release/bundle/osx/athenaCL.app/Contents/Resources/doc"
	open "target/release/bundle/osx"
