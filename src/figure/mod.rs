//! Figures: what athenaCL's graphics commands show.
//!
//! The commands describe their data (parameter values, texture time ranges, cellular automaton
//! cells) and the GUI lays it out and draws it in athenaCL's style.

pub mod font;

/// A figure from a graphics command.
#[derive(Debug, Clone, PartialEq)]
pub enum Figure {
    /// Parameter values over events or time: `TPmap`, `TImap` and `TCmap`.
    Parameters(Parameters),
    /// Textures and their clones over time: `TEmap`.
    Ensemble(Ensemble),
    /// Generations of a cellular automaton: `AUca`.
    Automaton(Automaton),
}

/// Graphs of parameter values, sharing the x axis.
#[derive(Debug, Clone, PartialEq)]
pub struct Parameters {
    /// Colors.
    pub palette: Palette,
    /// What the x axis measures.
    pub domain: Domain,
    /// Whether to draw taller graphs: `TPmap` shows one or two parameters in detail, while
    /// `TImap` and `TCmap` show all of a texture's parameters.
    pub detailed: bool,
    /// The graphs, top to bottom.
    pub graphs: Vec<Graph>,
}

/// What the x axis of parameter graphs measures.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Domain {
    /// Event numbers, from zero.
    Events,
    /// Seconds.
    Time,
}

/// The values of one parameter.
#[derive(Debug, Clone, PartialEq)]
pub struct Graph {
    /// The parameter and its generator, e.g. `amplitude: randomBeta`.
    pub title: String,
    /// Values in event order.
    pub marks: Vec<Mark>,
}

/// A parameter value over a span of the x axis: an event, where `start` and `end` are equal,
/// or the time from an event's start until its sustain ends.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Mark {
    /// Where the value starts.
    pub start: f64,
    /// Where the value ends.
    pub end: f64,
    /// The value.
    pub value: f64,
}

/// Textures and their clones over time.
#[derive(Debug, Clone, PartialEq)]
pub struct Ensemble {
    /// Colors.
    pub palette: Palette,
    /// Textures, in display order.
    pub textures: Vec<Texture>,
}

/// A texture and its clones.
#[derive(Debug, Clone, PartialEq)]
pub struct Texture {
    /// The texture itself.
    pub lane: Lane,
    /// Its clones, in display order.
    pub clones: Vec<Lane>,
}

/// A texture or clone on the timeline.
#[derive(Debug, Clone, PartialEq)]
pub struct Lane {
    /// Its name.
    pub name: String,
    /// Absolute start time in seconds.
    pub start: f64,
    /// Absolute end time in seconds.
    pub end: f64,
    /// Whether it's muted.
    pub muted: bool,
}

/// Generations of a one-dimensional cellular automaton.
#[derive(Debug, Clone, PartialEq)]
pub struct Automaton {
    /// Colors.
    pub palette: Palette,
    /// The automaton's specification, one part per line.
    pub title: Vec<String>,
    /// Cell values, a row per generation.
    pub cells: Vec<Vec<f64>>,
    /// The largest value of a discrete automaton, whose values are shaded in proportion to it.
    /// Continuous automata have values between 0 and 1.
    pub max: Option<f64>,
}

impl Automaton {
    /// How dark a value is drawn, from 0 (white) to 1 (black).
    pub fn shade(&self, value: f64) -> f64 {
        let shade = match self.max {
            Some(max) if max > 0.0 => value / max,
            Some(_) => 0.0,
            None => value,
        };
        shade.clamp(0.0, 1.0)
    }
}

/// Colors, from athenaCL's `gui` preferences.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Palette {
    /// Behind the data (`COLORbgAbs`).
    pub background: Rgb,
    /// Grid lines (`COLORbgGrid`).
    pub grid: Rgb,
    /// Margins around the data (`COLORbgMargin`).
    pub margin: Rgb,
    /// Textures (`COLORfgMain`).
    pub main: Rgb,
    /// The top edge of textures (`COLORfgMainFrame`).
    pub main_frame: Rgb,
    /// Clones (`COLORfgAlt`).
    pub alt: Rgb,
    /// The top edge of clones (`COLORfgAltFrame`).
    pub alt_frame: Rgb,
    /// Titles and data points (`COLORtxTitle`).
    pub title: Rgb,
    /// Secondary labels (`COLORtxLabel`).
    pub label: Rgb,
    /// Axis units (`COLORtxUnit`).
    pub unit: Rgb,
}

/// An opaque color.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Rgb(pub u8, pub u8, pub u8);

impl Rgb {
    /// Parse an HTML-style `#rrggbb` or `#rgb` color, as used throughout athenaCL.
    pub fn parse(value: &str) -> Option<Self> {
        let hex = value.strip_prefix('#')?;
        if !hex.is_ascii() {
            return None;
        }
        let channel = |digits: &str| u8::from_str_radix(digits, 16).ok();
        match hex.len() {
            6 => Some(Self(
                channel(&hex[0..2])?,
                channel(&hex[2..4])?,
                channel(&hex[4..6])?,
            )),
            3 => {
                let short = |i: usize| channel(&hex[i..=i]).map(|v| v * 17);
                Some(Self(short(0)?, short(1)?, short(2)?))
            }
            _ => None,
        }
    }

    /// A gray from white (0) to black (1), as athenaCL shades cellular automata.
    pub fn gray(shade: f64) -> Self {
        let level = ((1.0 - shade) * 255.0).clamp(0.0, 255.0) as u8;
        Self(level, level, level)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_html_colors() {
        assert_eq!(Rgb::parse("#FF8000"), Some(Rgb(255, 128, 0)));
        assert_eq!(Rgb::parse("#9f9f9f"), Some(Rgb(159, 159, 159)));
        assert_eq!(Rgb::parse("#f80"), Some(Rgb(255, 136, 0)));
        assert_eq!(Rgb::parse("FF8000"), None);
        assert_eq!(Rgb::parse("#FF80"), None);
        assert_eq!(Rgb::parse("#GG8000"), None);
        assert_eq!(Rgb::parse("red"), None);
    }

    #[test]
    fn grays_run_from_white_to_black() {
        assert_eq!(Rgb::gray(0.0), Rgb(255, 255, 255));
        assert_eq!(Rgb::gray(1.0), Rgb(0, 0, 0));
        // truncated like athenaCL's `FloatToRGB`
        assert_eq!(Rgb::gray(0.5), Rgb(127, 127, 127));
    }

    #[test]
    fn automata_shade_values() {
        let automaton = |max| Automaton {
            palette: Palette {
                background: Rgb(0, 0, 0),
                grid: Rgb(0, 0, 0),
                margin: Rgb(0, 0, 0),
                main: Rgb(0, 0, 0),
                main_frame: Rgb(0, 0, 0),
                alt: Rgb(0, 0, 0),
                alt_frame: Rgb(0, 0, 0),
                title: Rgb(0, 0, 0),
                label: Rgb(0, 0, 0),
                unit: Rgb(0, 0, 0),
            },
            title: Vec::new(),
            cells: Vec::new(),
            max,
        };
        assert_eq!(automaton(Some(2.0)).shade(1.0), 0.5);
        assert_eq!(automaton(Some(2.0)).shade(3.0), 1.0);
        assert_eq!(automaton(None).shade(0.25), 0.25);
    }
}
