//! Figures: what athenaCL's graphics commands show.
//!
//! The commands describe their data (parameter values, texture events and time ranges, cellular
//! automaton cells) and the GUI lays it out and draws it in athenaCL's style, in the colors of the
//! app's theme.

pub mod font;
pub mod notation;

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
    /// What the x axis measures.
    pub domain: Domain,
    /// Whether to draw taller graphs: `TPmap` shows one or two parameters in detail, while
    /// `TImap` and `TCmap` show all of a texture's parameters.
    pub detailed: bool,
    /// The graphs, top to bottom.
    pub graphs: Vec<Graph>,
    /// The events the graphs describe, which can also be shown as a score: a texture's, for
    /// `TImap`. Figures of parameters alone have none.
    pub events: Vec<Event>,
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

/// An event of a texture: a note, or a rest.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Event {
    /// When it starts, in seconds.
    pub time: f64,
    /// Its rhythmic duration in seconds: the time until the next event of its rhythm.
    pub duration: f64,
    /// How long it sounds, in seconds.
    pub sustain: f64,
    /// Whether it sounds: an event with no accent is a rest.
    pub sounds: bool,
    /// Its pitch in semitones from middle C, athenaCL's pitch space. Microtones are fractions.
    pub pitch: f64,
    /// Its amplitude, from 0 to 1.
    pub amplitude: f64,
    /// The tempo when it starts, in beats per minute.
    pub tempo: f64,
}

/// Textures and their clones over time.
#[derive(Debug, Clone, PartialEq)]
pub struct Ensemble {
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
    /// Its events, which can also be shown as a score.
    pub events: Vec<Event>,
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
    /// The automaton's specification, one part per line.
    pub title: Vec<String>,
    /// Cell values, a row per generation.
    pub cells: Vec<Vec<f64>>,
    /// The largest value of a discrete automaton, whose values are shaded in proportion to it.
    /// Continuous automata have values between 0 and 1.
    pub max: Option<f64>,
}

impl Automaton {
    /// How strongly a value is drawn, from 0 (the page) to 1 (ink).
    pub fn shade(&self, value: f64) -> f64 {
        let shade = match self.max {
            Some(max) if max > 0.0 => value / max,
            Some(_) => 0.0,
            None => value,
        };
        shade.clamp(0.0, 1.0)
    }
}

#[cfg(test)]
mod tests {
    #![expect(clippy::float_cmp, reason = "the tests assert exact float values")]

    use super::*;

    #[test]
    fn automata_shade_values() {
        let automaton = |max| Automaton {
            title: Vec::new(),
            cells: Vec::new(),
            max,
        };
        assert_eq!(automaton(Some(2.0)).shade(1.0), 0.5);
        assert_eq!(automaton(Some(2.0)).shade(3.0), 1.0);
        assert_eq!(automaton(None).shade(0.25), 0.25);
    }
}
