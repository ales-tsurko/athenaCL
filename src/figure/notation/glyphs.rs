//! The glyphs of the pixel notation.
//!
//! Each glyph is a list of rows: `#` is a set pixel, `.` an empty one. Its anchor row is the row
//! that sits on its reference position: a pitch's line or space, a staff line, the end of a stem,
//! or the baseline; its left column is its left edge.

/// A glyph of the notation.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum Glyph {
    /// The treble clef; its anchor row is the G line.
    GClef,
    /// The bass clef; its anchor row is the F line.
    FClef,
    /// A filled notehead: quarter notes and shorter.
    NoteheadBlack,
    /// A hollow notehead: half notes.
    NoteheadHalf,
    /// A whole note's head.
    NoteheadWhole,
    /// An eighth's flag, hanging from the top of an up stem.
    Flag8Up,
    /// A sixteenth's flags, hanging from the top of an up stem.
    Flag16Up,
    /// A thirty-second's flags, hanging from the top of an up stem.
    Flag32Up,
    /// An eighth's flag, rising from the bottom of a down stem.
    Flag8Down,
    /// A sixteenth's flags, rising from the bottom of a down stem.
    Flag16Down,
    /// A thirty-second's flags, rising from the bottom of a down stem.
    Flag32Down,
    /// A whole rest, hanging from the line above the middle line.
    RestWhole,
    /// A half rest, sitting on the middle line.
    RestHalf,
    /// A quarter rest, centered on the middle line.
    RestQuarter,
    /// An eighth rest.
    Rest8,
    /// A sixteenth rest.
    Rest16,
    /// A thirty-second rest.
    Rest32,
    /// A sharp; its anchor row is the note's.
    Sharp,
    /// A quarter-tone sharp, for athenaCL's quarter tones.
    QuarterSharp,
    /// A sharp and a quarter tone.
    ThreeQuarterSharp,
    /// A dot lengthening a note by half.
    Dot,
    /// The left end of a tie under the notes.
    TieStartBelow,
    /// The right end of a tie under the notes.
    TieEndBelow,
    /// The left end of a tie over the notes.
    TieStartAbove,
    /// The right end of a tie over the notes.
    TieEndAbove,
    /// A triplet's count.
    Tuplet3,
    /// A quintuplet's count.
    Tuplet5,
    /// A sextuplet's count.
    Tuplet6,
    /// A septuplet's count.
    Tuplet7,
    /// The dynamics' p; its anchor row is the baseline.
    Piano,
    /// The dynamics' m.
    Mezzo,
    /// The dynamics' f.
    Forte,
}

/// Every glyph with its bitmap, in the order the glyphs are declared: a glyph finds its own by its
/// place in the enum, which `the_table_holds_every_glyph_in_order` checks.
type Bitmap = (i32, &'static [&'static str]);
const BITMAPS: [(Glyph, Bitmap); 32] = [
    (Glyph::GClef, G_CLEF),
    (Glyph::FClef, F_CLEF),
    (Glyph::NoteheadBlack, NOTEHEAD_BLACK),
    (Glyph::NoteheadHalf, NOTEHEAD_HALF),
    (Glyph::NoteheadWhole, NOTEHEAD_WHOLE),
    (Glyph::Flag8Up, FLAG_8_UP),
    (Glyph::Flag16Up, FLAG_16_UP),
    (Glyph::Flag32Up, FLAG_32_UP),
    (Glyph::Flag8Down, FLAG_8_DOWN),
    (Glyph::Flag16Down, FLAG_16_DOWN),
    (Glyph::Flag32Down, FLAG_32_DOWN),
    (Glyph::RestWhole, REST_WHOLE),
    (Glyph::RestHalf, REST_HALF),
    (Glyph::RestQuarter, REST_QUARTER),
    (Glyph::Rest8, REST_8),
    (Glyph::Rest16, REST_16),
    (Glyph::Rest32, REST_32),
    (Glyph::Sharp, SHARP),
    (Glyph::QuarterSharp, QUARTER_SHARP),
    (Glyph::ThreeQuarterSharp, THREE_QUARTER_SHARP),
    (Glyph::Dot, DOT),
    (Glyph::TieStartBelow, TIE_START_BELOW),
    (Glyph::TieEndBelow, TIE_END_BELOW),
    (Glyph::TieStartAbove, TIE_START_ABOVE),
    (Glyph::TieEndAbove, TIE_END_ABOVE),
    (Glyph::Tuplet3, TUPLET_3),
    (Glyph::Tuplet5, TUPLET_5),
    (Glyph::Tuplet6, TUPLET_6),
    (Glyph::Tuplet7, TUPLET_7),
    (Glyph::Piano, PIANO),
    (Glyph::Mezzo, MEZZO),
    (Glyph::Forte, FORTE),
];

impl Glyph {
    /// The glyph's anchor row and its rows of pixels.
    pub(crate) fn bitmap(self) -> Bitmap {
        BITMAPS.get(self as usize).map_or((0, &[]), |&(_, it)| it)
    }

    /// The glyph's width in pixels.
    pub(crate) fn width(self) -> i32 {
        let (_, rows) = self.bitmap();
        rows.first()
            .map_or(0, |row| i32::try_from(row.len()).unwrap_or(0))
    }
}

const G_CLEF: (i32, &[&str]) = (
    17,
    &[
        ".......##...",
        "......#..#..",
        "......#..#..",
        "......#..#..",
        "......#..#..",
        "......#.##..",
        "......#.#...",
        "......###...",
        "......##....",
        ".....##.....",
        "....###.....",
        "...##.#.....",
        "..##..#.....",
        ".##...#.....",
        "##...######.",
        "#...##.#..##",
        "#..#...#...#",
        "#..#..##...#",
        "#...#..#...#",
        ".#.....#..#.",
        "..##...#.##.",
        "....####....",
        ".......#....",
        "..##...#....",
        ".####..#....",
        ".####..#....",
        "..##..#.....",
        "...###......",
    ],
);

const F_CLEF: (i32, &[&str]) = (
    4,
    &[
        "..#####.....",
        ".#.....##...",
        "#.......#.##",
        "##......#.##",
        "###.....##..",
        ".#......##..",
        "........#.##",
        ".......##.##",
        "......##....",
        ".....##.....",
        "...##.......",
        ".##.........",
    ],
);

const NOTEHEAD_BLACK: (i32, &[&str]) = (2, &["..###.", ".#####", "######", "#####.", ".###.."]);

const NOTEHEAD_HALF: (i32, &[&str]) = (2, &["..###.", ".##.##", "##..##", "##.##.", ".###.."]);

const NOTEHEAD_WHOLE: (i32, &[&str]) =
    (2, &["..###..", "##..###", "##...##", "###..##", "..###.."]);

const FLAG_8_UP: (i32, &[&str]) = (
    0,
    &[
        "#...", "##..", ".##.", "..#.", "..##", "...#", "...#", "..#.", "..#.",
    ],
);

const FLAG_16_UP: (i32, &[&str]) = (
    0,
    &[
        "#...", "##..", ".##.", "#.#.", "##.#", ".##.", "..##", "...#", "...#", "..#.",
    ],
);

const FLAG_32_UP: (i32, &[&str]) = (
    0,
    &[
        "#...", "##..", ".##.", "#.#.", "##.#", ".##.", "#.##", "##.#", ".##.", "..##", "...#",
        "...#", "..#.",
    ],
);

const FLAG_8_DOWN: (i32, &[&str]) = (
    8,
    &[
        "..#.", "..#.", "...#", "...#", "..##", "..#.", ".##.", "##..", "#...",
    ],
);

const FLAG_16_DOWN: (i32, &[&str]) = (
    9,
    &[
        "..#.", "...#", "...#", "..##", ".##.", "##.#", "#.#.", ".##.", "##..", "#...",
    ],
);

const FLAG_32_DOWN: (i32, &[&str]) = (
    12,
    &[
        "..#.", "...#", "...#", "..##", ".##.", "##.#", "#.##", ".##.", "##.#", "#.#.", ".##.",
        "##..", "#...",
    ],
);

const REST_WHOLE: (i32, &[&str]) = (0, &[".....", "#####", "#####"]);

const REST_HALF: (i32, &[&str]) = (2, &["#####", "#####", "....."]);

const REST_QUARTER: (i32, &[&str]) = (
    6,
    &[
        ".#...", ".##..", "..##.", "..###", ".###.", "###..", ".##..", "..##.", ".###.", "###..",
        "#....", ".#...",
    ],
);

const REST_8: (i32, &[&str]) = (
    2,
    &[
        "##..#", "##.#.", ".##..", "..#..", ".#...", ".#...", "#....",
    ],
);

const REST_16: (i32, &[&str]) = (
    2,
    &[
        "..##..#", "..##.#.", "...##..", "##.#...", "##.#...", ".##....", ".#.....", "#......",
    ],
);

const REST_32: (i32, &[&str]) = (
    4,
    &[
        "....##..#",
        "....##.#.",
        ".....##..",
        "..##.#...",
        "..##.#...",
        "...##....",
        "##.#.....",
        "##.#.....",
        ".##......",
        ".#.......",
        "#........",
    ],
);

const SHARP: (i32, &[&str]) = (
    5,
    &[
        ".#.#.", ".#.#.", ".#.##", "####.", "##.#.", ".#.#.", ".#.##", "####.", "##.#.", ".#.#.",
        ".#.#.",
    ],
);

const QUARTER_SHARP: (i32, &[&str]) = (
    5,
    &[
        ".#..", ".#..", ".###", "###.", "##..", ".#..", ".###", "###.", "##..", ".#..", ".#..",
    ],
);

const THREE_QUARTER_SHARP: (i32, &[&str]) = (
    5,
    &[
        ".#.#.#.", ".#.#.#.", ".#.#.##", "######.", "##.#.#.", ".#.#.#.", ".#.#.##", "######.",
        "##.#.#.", ".#.#.#.", ".#.#.#.",
    ],
);

const DOT: (i32, &[&str]) = (1, &[".#.", "###", ".#."]);

const TIE_START_BELOW: (i32, &[&str]) = (0, &["#..", ".##"]);

const TIE_END_BELOW: (i32, &[&str]) = (0, &["..#", "##."]);

const TIE_START_ABOVE: (i32, &[&str]) = (1, &[".##", "#.."]);

const TIE_END_ABOVE: (i32, &[&str]) = (1, &["##.", "..#"]);

const TUPLET_3: (i32, &[&str]) = (4, &["###", "..#", ".##", "..#", "###"]);

const TUPLET_5: (i32, &[&str]) = (4, &["###", "#..", "##.", "..#", "##."]);

const TUPLET_6: (i32, &[&str]) = (4, &[".##", "#..", "###", "#.#", "###"]);

const TUPLET_7: (i32, &[&str]) = (4, &["###", "..#", ".#.", ".#.", ".#."]);

const PIANO: (i32, &[&str]) = (
    4,
    &[
        "..#.##.", "..##..#", ".##...#", ".#...#.", ".####..", "#......", "##.....",
    ],
);

const MEZZO: (i32, &[&str]) = (
    4,
    &[".##.##..", ".#.#..#.", "#..#..#.", "#.#..#..", "#.#..#.."],
);

const FORTE: (i32, &[&str]) = (
    6,
    &[
        "....##", "...#..", "..#...", ".####.", "..#...", "..#...", ".#....", ".#....", "#.....",
    ],
);

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_table_holds_every_glyph_in_order() {
        for (index, &(glyph, (_, rows))) in BITMAPS.iter().enumerate() {
            assert_eq!(glyph as usize, index, "{glyph:?} is not at its own place");
            assert!(!rows.is_empty(), "{glyph:?} has no rows");
            assert_eq!(glyph.bitmap().1, rows, "{glyph:?} finds another's bitmap");
        }
    }

    #[test]
    fn glyphs_are_rectangles_as_wide_as_they_measure() {
        for &(glyph, (_, rows)) in &BITMAPS {
            let width = rows.first().map_or(0, |row| row.len());
            assert!(
                rows.iter().all(|row| row.len() == width),
                "{glyph:?} is ragged"
            );
            assert_eq!(glyph.width(), width as i32);
        }
    }
}
