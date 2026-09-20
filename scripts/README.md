# App icon generator

`python3 scripts/generate_app_icon.py` renders the app's `:: athcl` PNG and SVG
into `resources/`. Use `--output DIRECTORY` to preview changes elsewhere. This
script uses Python 3's standard library and works from any current directory. It
renders the source artwork; it does not rebuild `athenaCL.icns`.

UI icons live entirely in `src/app/icons/`. Add an `Icon` variant and its square
pixel mask in `glyphs.rs`; the shared widget handles caching and theme colours.
