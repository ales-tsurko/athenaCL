# Software Dependencies

athenaCL produces both Csound and MIDI scores. Csound is free and runs on every
platform. Download Csound here: https://csound.com/.




## Quick-Start

`$ cargo run --release`




## Installation

Run from source code directory:

```
$ cargo install --path . 
```

Then:

```
$ athenacl
```




## Command log

Command output wraps to the log's width. Opened text files preserve their line
breaks and have their own horizontal scrollbar; scrolling a file sideways leaves
the rest of the log in place.




## Scratch file browser

Click the folder icon in the header to show or hide the scratch folder's tree.
Use **Change folder** inside the browser to choose a scratch folder. Folder
icons show whether each folder is expanded or collapsed. Drag the browser's
right edge to resize it, between 220 and 480 pixels. The tree refreshes
automatically as files change; **Refresh** also reloads it. Folders and readable
AthenaObjects, audio, MIDI, sound fonts (`.sf2`), and text files are shown.
Symbolic links and unsupported binary files are hidden.

Double-click a file to open it. AthenaObject XML files replace the current
object, just like `AOl`. Audio and MIDI files add a player to the log. Text
files show their contents in the log, with previews limited to 1 MiB. Sound
fonts carry an **SF** tag. Double-click one, press Enter with it selected, or
choose **Use as sound** from its context menu to use it for MIDI playback.

Right-click a file or folder to copy, paste, rename, delete, or create a folder.
Shift-click selects a range; Command-click on macOS or Ctrl-click on Windows and
Linux adds or removes individual items. Copy and Delete apply to the selection;
Rename is available for one item at a time. Copy and paste work within the
browser's current scratch folder. Pasting beside an existing name creates a
numbered copy; renaming refuses an existing name. Deletion requires confirmation
and is permanent.

Drag files or folders onto a folder to move them, or onto **Scratch folder** to
move them back to the root. Dragging a selected item moves the whole selection.
Holding over a closed folder expands it; holding near the tree's top or bottom
scrolls it. Escape cancels a drag. Moves refuse existing names and cannot move a
folder into itself or its descendants.

Text previews and loaded AthenaObjects are snapshots. Moving, renaming, or
deleting their source files does not change what was already loaded. Affected
media players stop and keep their original paths, so the old log entry reports a
missing file. Open the moved or renamed file to add a new player.




## Playback volume and sound

The bottom bar's **VOLUME** meter controls all audio and MIDI playback. Click or
drag its twelve segments to set the level, scroll for one step, or double-click
for full volume. Hover to see the percentage. The speaker button mutes playback
without changing the saved level; click again to restore it. Adjusting the meter
also unmutes. Volume and mute are remembered between sessions.

The header's **SOUND** button chooses the MIDI sound font. Its menu lists the
built-in FluidR3 GM, recent fonts with their folders, and **Load sound font…**
for choosing an `.sf2` file. The active choice is filled. A new font loads in
the background while players keep their old sound, then takes over at the
current playhead. All MIDI players use the selected font, which is remembered
for the next session. An unreadable font adds an **ERR** line and leaves the
previous sound in place. If a remembered font is missing at startup, the
built-in font is restored and the log explains why.

These controls affect playback only. Exported files and Csound renders keep
their original sound and level.
