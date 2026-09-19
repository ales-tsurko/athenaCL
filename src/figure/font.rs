//! athenaCL's bitmap fonts.
//!
//! A port of `FontBitMap` from athenaCL's `fontLibrary.py`: text is laid out glyph by glyph,
//! each glyph trimmed of its empty right columns and followed by a fixed gap.

mod glyphs;

/// A character and its rows of pixels.
type Glyph = (char, &'static [&'static str]);

/// One of athenaCL's bitmap fonts.
///
/// Figures only use the micro font, as athenaCL's graphs did; the others are athenaCL's too,
/// ported along with it.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[cfg_attr(
    not(test),
    expect(
        dead_code,
        reason = "the other fonts are athenaCL's, ported along for completeness"
    )
)]
pub enum Font {
    /// The small font of graph labels.
    Micro,
    /// A large font.
    Macro,
    /// A large rounded font.
    Poster,
    /// A large capitals font.
    Capital,
    /// A bold font.
    Strong,
}

/// A line of text rendered to pixels.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Bitmap {
    width: usize,
    rows: Vec<Vec<bool>>,
}

impl Bitmap {
    /// Width in pixels.
    pub fn width(&self) -> usize {
        self.width
    }

    /// Height in pixels.
    pub fn height(&self) -> usize {
        self.rows.len()
    }

    /// Horizontal runs of set pixels, as `(row, first column, length)`.
    pub fn runs(&self) -> impl Iterator<Item = (usize, usize, usize)> + '_ {
        self.rows.iter().enumerate().flat_map(|(y, row)| {
            let mut x = 0;
            std::iter::from_fn(move || {
                let rest = row.get(x..)?;
                x += rest.iter().position(|&set| set)?;
                let length = row
                    .get(x..)
                    .map_or(0, |rest| rest.iter().take_while(|&&set| set).count())
                    .max(1);
                x += length;
                Some((y, x - length, length))
            })
        })
    }
}

impl Font {
    fn glyphs(self) -> &'static [Glyph] {
        match self {
            Self::Micro => glyphs::MICRO,
            Self::Macro => glyphs::MACRO,
            Self::Poster => glyphs::POSTER,
            Self::Capital => glyphs::CAPITAL,
            Self::Strong => glyphs::STRONG,
        }
    }

    fn glyph(self, c: char) -> Option<&'static [&'static str]> {
        let glyphs = self.glyphs();
        glyphs
            .binary_search_by_key(&c, |&(c, _)| c)
            .ok()
            .and_then(|index| glyphs.get(index))
            .map(|&(_, glyph)| glyph)
    }

    /// The size of a character cell, which athenaCL takes from `a`.
    pub fn cell(self) -> (usize, usize) {
        let a = self.glyph('a').expect("every font has an `a`");
        (a.first().map_or(0, |row| row.len()), a.len())
    }

    /// Render a line of text, leaving `kern` empty columns after each character.
    ///
    /// Letters are case-insensitive, a space is as wide as a character cell, and characters the
    /// font lacks are drawn as its `?`. Empty columns on the right are trimmed.
    pub fn render(self, text: &str, kern: usize) -> Bitmap {
        let (cell_width, height) = self.cell();
        let mut rows = vec![Vec::new(); height];
        for c in text.chars().map(|c| c.to_ascii_lowercase()) {
            match self.glyph(c) {
                Some(glyph) => {
                    let width = used_width(glyph);
                    for (row, line) in rows.iter_mut().zip(glyph) {
                        row.extend(line.bytes().take(width).map(|b| b == b'#'));
                        row.extend(std::iter::repeat_n(false, kern));
                    }
                }
                None if c == ' ' => {
                    for row in &mut rows {
                        row.extend(std::iter::repeat_n(false, cell_width + kern));
                    }
                }
                // athenaCL draws the `?` as is, without trimming or kerning it
                None => {
                    let glyph = self.glyph('?').expect("every font has a `?`");
                    for (row, line) in rows.iter_mut().zip(glyph) {
                        row.extend(line.bytes().map(|b| b == b'#'));
                    }
                }
            }
        }
        let width = rows
            .iter()
            .map(|row| row.iter().rposition(|&set| set).map_or(0, |x| x + 1))
            .max()
            .unwrap_or(0);
        for row in &mut rows {
            row.truncate(width);
        }
        Bitmap { width, rows }
    }
}

/// Width up to the rightmost set pixel of any row.
fn used_width(glyph: &[&str]) -> usize {
    glyph
        .iter()
        .map(|row| row.rfind('#').map_or(0, |x| x + 1))
        .max()
        .unwrap_or(0)
}

#[cfg(test)]
mod tests {
    use super::*;

    const FONTS: [Font; 5] = [
        Font::Micro,
        Font::Macro,
        Font::Poster,
        Font::Capital,
        Font::Strong,
    ];

    fn picture(bitmap: &Bitmap) -> Vec<String> {
        bitmap
            .rows
            .iter()
            .map(|row| row.iter().map(|&set| if set { '#' } else { '.' }).collect())
            .collect()
    }

    #[test]
    fn glyph_tables_are_well_formed() {
        for font in FONTS {
            let (_, height) = font.cell();
            let glyphs = font.glyphs();
            assert!(glyphs.windows(2).all(|pair| pair[0].0 < pair[1].0));
            for (c, glyph) in glyphs {
                assert_eq!(glyph.len(), height, "{font:?} {c:?}");
                assert!(glyph.iter().all(|row| row.len() == glyph[0].len()));
                assert!(glyph
                    .iter()
                    .all(|row| row.bytes().all(|b| b == b'#' || b == b'.')));
            }
        }
    }

    #[test]
    fn cells_match_athenacl() {
        let cells = FONTS.map(Font::cell);
        assert_eq!(cells, [(5, 7), (15, 8), (12, 10), (14, 10), (10, 8)]);
    }

    #[test]
    fn renders_trimmed_glyphs() {
        assert_eq!(
            picture(&Font::Micro.render("a", 1)),
            ["....", ".##.", "#..#", "####", "#..#", "#..#", "...."]
        );
    }

    #[test]
    fn letters_are_case_insensitive() {
        assert_eq!(Font::Micro.render("Ab", 1), Font::Micro.render("aB", 1));
    }

    #[test]
    fn kerning_separates_characters_but_not_the_end() {
        // 4 columns of `a`, a gap, then the 4 columns of `b`
        assert_eq!(Font::Micro.render("ab", 1).width(), 9);
        assert_eq!(Font::Micro.render("ab", 3).width(), 11);
    }

    #[test]
    fn spaces_are_a_cell_wide() {
        // `a`, gap, space cell and its gap, `a`
        assert_eq!(Font::Micro.render("a a", 1).width(), 4 + 1 + 5 + 1 + 4);
        assert_eq!(Font::Micro.render("a ", 1).width(), 4);
    }

    #[test]
    fn unknown_characters_are_question_marks() {
        let question = Font::Micro.render("?", 1);
        assert_eq!(Font::Micro.render("é", 1), question);
        assert_eq!(Font::Micro.render("", 1).width(), 0);
    }

    #[test]
    fn runs_cover_the_set_pixels() {
        let bitmap = Font::Micro.render("a", 1);
        let runs: Vec<_> = bitmap.runs().filter(|&(y, _, _)| y < 4).collect();
        assert_eq!(runs, [(1, 1, 2), (2, 0, 1), (2, 3, 1), (3, 0, 4)]);
    }
}
