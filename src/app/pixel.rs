//! Pixel text: the wordmark, and labels in athenaCL's micro font, drawn crisp.

use iced::{
    mouse,
    widget::canvas::{self, Canvas},
    Color, Element, Length, Point, Rectangle, Renderer, Size, Theme,
};

use crate::figure::font::{Bitmap, Font};

/// Screen pixels per font pixel of labels, as in figures.
const LABEL_SCALE: f32 = 1.5;
/// Empty columns between characters.
const KERN: usize = 1;
/// Screen pixels per pixel of the wordmark.
const WORDMARK_SCALE: f32 = 2.0;

/// "athenaCL" in athenaCL's pixel letters: its own lowercase, and the macro font's C and L.
const WORDMARK: [&str; 8] = [
    "....................##................................................#########..##.........",
    ".............##.....##..............................................###..........##.........",
    ".............##.....##.............................................##............##.........",
    ".#######...#######..##.######....########...##.######....#######...##............##.........",
    ".......##....##.....###.....##..##......##..###.....##.........##..##............##.........",
    ".########....##.....##......##..##########..##......##...########..##............##.........",
    "##.....##....##.....##......##..##..........##......##..##.....##...###..........##.........",
    ".########.....####..##......##...#########..##......##...########.....#########..###########",
];

/// A label in the micro font, in `color`.
pub(crate) fn label<'a, Message: 'a>(text: &str, color: Color) -> Element<'a, Message> {
    let bitmap = Font::Micro.render(text, KERN);
    let runs = bitmap_runs(&bitmap);
    pixels(runs, bitmap.width(), bitmap.height(), LABEL_SCALE, color)
}

/// The wordmark, in `color`.
pub(crate) fn wordmark<'a, Message: 'a>(color: Color) -> Element<'a, Message> {
    let runs = WORDMARK
        .iter()
        .enumerate()
        .flat_map(|(y, row)| {
            let mut x = 0;
            row.split('.')
                .filter_map(|set| {
                    let run = (!set.is_empty()).then_some((y, x, set.len()));
                    x += set.len() + 1;
                    run
                })
                .collect::<Vec<_>>()
        })
        .collect();
    let width = WORDMARK.first().map_or(0, |row| row.len());
    pixels(runs, width, WORDMARK.len(), WORDMARK_SCALE, color)
}

/// A bitmap's runs, as `(row, column, length)`.
fn bitmap_runs(bitmap: &Bitmap) -> Vec<(usize, usize, usize)> {
    bitmap.runs().collect()
}

/// Runs of pixels, `width` by `height` pixels, drawn `scale` times.
fn pixels<'a, Message: 'a>(
    runs: Vec<(usize, usize, usize)>,
    width: usize,
    height: usize,
    scale: f32,
    color: Color,
) -> Element<'a, Message> {
    Canvas::new(Pixels { runs, scale, color })
        .width(Length::Fixed(width as f32 * scale))
        .height(Length::Fixed(height as f32 * scale))
        .into()
}

/// Runs of pixels to draw: they take no input, so a button around them gets it.
#[derive(Debug)]
struct Pixels {
    runs: Vec<(usize, usize, usize)>,
    scale: f32,
    color: Color,
}

impl<Message> canvas::Program<Message> for Pixels {
    type State = ();

    fn draw(
        &self,
        _state: &(),
        renderer: &Renderer,
        _theme: &Theme,
        bounds: Rectangle,
        _cursor: mouse::Cursor,
    ) -> Vec<canvas::Geometry> {
        let mut frame = canvas::Frame::new(renderer, bounds.size());
        for &(y, x, length) in &self.runs {
            frame.fill_rectangle(
                Point::new(x as f32 * self.scale, y as f32 * self.scale),
                Size::new(length as f32 * self.scale, self.scale),
                self.color,
            );
        }
        vec![frame.into_geometry()]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_wordmark_is_a_rectangle() {
        assert!(WORDMARK.iter().all(|row| row.len() == 92));
    }

    #[test]
    fn labels_take_their_bitmap_size() {
        let bitmap = Font::Micro.render("ERR", KERN);
        assert!(bitmap.width() > 0 && bitmap.height() == 7);
        assert!(!bitmap_runs(&bitmap).is_empty());
    }
}
