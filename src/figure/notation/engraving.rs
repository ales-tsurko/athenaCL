//! Engraving: laying a texture's events out as pixel notation.

use super::glyphs::Glyph;
use crate::figure::{Domain, Event};

/// Staff lines are this many notation pixels apart.
const SPACE: i32 = 4;
/// A staff's height, from its top line to its bottom line.
const STAFF: i32 = 4 * SPACE;
/// A stem's length, from its note's center.
const STEM: i32 = 14;
/// A notehead's width.
const HEAD: i32 = 6;
/// Where a stem is, across from its notes' left edge: on their right edge going up, and on their
/// left edge going down.
const STEM_UP: i32 = HEAD - 1;
/// A beam's thickness, and the distance from one beam to the next.
const BEAM: i32 = 2;
const BEAM_PITCH: i32 = 3;
/// Rows between the staves of a grand staff.
const STAFF_GAP: i32 = 24;
/// Empty rows above and below everything.
const MARGIN: i32 = 4;
/// Rows from the lowest notation to the dynamics' baseline.
const DYNAMICS_GAP: i32 = 8;
/// How far each dynamics letter is from the previous one.
const LETTER: i32 = 7;
/// Where clefs are, at the left of the staves.
const CLEF_X: i32 = 8;
/// Notation pixels given to the shortest note, which is when notes are readable.
const READABLE: f64 = 10.0;
/// Notation pixels per event in event mode.
const SLOT: f64 = 16.0;
/// Ticks per beat when writing durations: 64th notes, triplets and quintuplets divide it.
const TICKS: f64 = 240.0;
/// Onsets this close, in seconds, are a chord.
const TOGETHER: f64 = 1e-6;

/// Pixel notation for a texture's events, engraved once for every zoom.
#[derive(Debug, Clone, PartialEq)]
pub struct Score {
    staves: Vec<Staff>,
    items: Vec<Item>,
    /// Clefs and the grand staff's line, which stay at the left.
    pinned: Vec<Run>,
    notes: Vec<Note>,
    /// The notation's extent on the x axis, and the scale where it's readable.
    extent: (f64, f64),
    readable: f64,
    height: i32,
}

impl Score {
    /// Engrave `events` along an x axis measuring `domain`.
    pub fn new(events: &[Event], domain: Domain) -> Self {
        let mut order: Vec<&Event> = events.iter().collect();
        order.sort_by(|a, b| a.time.total_cmp(&b.time));
        let slots = Slots::new(&order, domain);
        let staves = Staff::layout(&order);
        let mut engraver = Engraver::new(staves);
        for written in write(events, &slots, &engraver.staves) {
            engraver.add(written);
        }
        engraver.engrave();
        engraver.dynamics(events, &slots);
        engraver.finish(&slots)
    }

    /// The staves, top to bottom.
    pub fn staves(&self) -> &[Staff] {
        &self.staves
    }

    /// The height of the notation, in notation pixels.
    pub fn height(&self) -> i32 {
        self.height
    }

    /// The span of the x axis the notation covers.
    pub fn extent(&self) -> (f64, f64) {
        self.extent
    }

    /// Notation pixels per unit of the x axis where notes are readable: where the shortest note
    /// gets ten, or an event slot sixteen.
    pub fn readable_scale(&self) -> f64 {
        self.readable
    }

    /// The clefs, and a grand staff's joining line, at the left.
    pub fn pinned(&self) -> &[Run] {
        &self.pinned
    }

    /// How far the clefs reach across.
    pub fn clef_width(&self) -> i32 {
        self.pinned
            .iter()
            .map(|run| run.x + run.length)
            .max()
            .unwrap_or(0)
    }

    /// The notation between columns `left` and `right` on `axis`, as runs of pixels.
    pub fn runs(&self, axis: &Axis, left: i32, right: i32) -> Vec<Run> {
        let mut runs = Vec::new();
        for item in &self.items {
            item.runs(axis, left, right, &mut runs);
        }
        runs
    }

    /// The note or rest whose head is at `(x, y)` on `axis`.
    pub fn note_at(&self, axis: &Axis, x: i32, y: i32) -> Option<&Note> {
        self.notes.iter().find(|note| {
            let left = axis.x(note.position) + note.left;
            x >= left - 1 && x <= left + note.width && y >= note.top - 1 && y <= note.bottom + 1
        })
    }
}

/// Where the notation is across: the column of `start` on the x axis, and notation pixels per unit
/// of the axis.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Axis {
    /// The column where `start` is.
    pub origin: i32,
    /// The x axis value at `origin`.
    pub start: f64,
    /// Notation pixels per unit of the x axis.
    pub scale: f64,
}

impl Axis {
    /// The column of an x axis value.
    pub fn x(&self, position: f64) -> i32 {
        self.origin + ((position - self.start) * self.scale).round() as i32
    }
}

/// A horizontal run of pixels: `length` pixels from column `x` of row `y`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Run {
    /// The first column.
    pub x: i32,
    /// The row.
    pub y: i32,
    /// How many pixels.
    pub length: i32,
}

/// A staff: its clef, and the row of its top line.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Staff {
    /// The clef.
    pub clef: Clef,
    /// The row of the top line.
    pub top: i32,
}

impl Staff {
    /// The staves for these events: treble or bass if every note fits one, both otherwise.
    fn layout(events: &[&Event]) -> Vec<Self> {
        let steps: Vec<i32> = events
            .iter()
            .filter(|event| event.sounds)
            .map(|event| Spelling::new(event.pitch).step)
            .collect();
        let (low, high) = steps
            .iter()
            .fold((i32::MAX, i32::MIN), |(low, high), &step| {
                (low.min(step), high.max(step))
            });
        let fits = |clef: Clef| {
            steps.is_empty() || (clef.position(low) >= -7 && clef.position(high) <= 15)
        };
        let clefs = if fits(Clef::Treble) {
            vec![Clef::Treble]
        } else if fits(Clef::Bass) {
            vec![Clef::Bass]
        } else {
            vec![Clef::Treble, Clef::Bass]
        };
        let mut top = 0;
        clefs
            .into_iter()
            .map(|clef| {
                let staff = Self { clef, top };
                top += STAFF + STAFF_GAP;
                staff
            })
            .collect()
    }

    /// The row of a step on the staff.
    fn row(self, step: i32) -> i32 {
        self.top + STAFF - SPACE / 2 * self.clef.position(step)
    }

    /// Whether `row` is one of the staff's lines.
    fn is_line(self, row: i32) -> bool {
        (self.top..=self.top + STAFF).contains(&row) && (row - self.top) % SPACE == 0
    }
}

/// A clef.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Clef {
    /// The treble clef.
    Treble,
    /// The bass clef.
    Bass,
}

impl Clef {
    /// Where a step is on the staff: 0 on the bottom line, 8 on the top one.
    fn position(self, step: i32) -> i32 {
        match self {
            // E4 on the bottom line
            Self::Treble => step - 2,
            // G2
            Self::Bass => step + 10,
        }
    }

    fn glyph(self) -> Glyph {
        match self {
            Self::Treble => Glyph::GClef,
            Self::Bass => Glyph::FClef,
        }
    }

    /// The position of the line the clef marks: G's or F's.
    fn line(self) -> i32 {
        match self {
            Self::Treble => 2,
            Self::Bass => 6,
        }
    }
}

/// A note or rest the pointer can point at: a head, or a rest's glyph.
#[derive(Debug, Clone, PartialEq)]
pub struct Note {
    /// The event it shows, as numbered in the events given to the score.
    pub event: usize,
    /// Its pitch as athenaCL names it, or `REST`.
    pub name: String,
    position: f64,
    left: i32,
    width: i32,
    top: i32,
    bottom: i32,
}

impl Note {
    /// The rectangle it covers on `axis`, as `(x, y, width, height)`.
    pub fn bounds(&self, axis: &Axis) -> (i32, i32, i32, i32) {
        (
            axis.x(self.position) + self.left,
            self.top,
            self.width,
            self.bottom - self.top + 1,
        )
    }
}

/// Where across something is: an offset from an x axis value.
#[derive(Debug, Clone, Copy, PartialEq)]
struct At {
    position: f64,
    dx: i32,
}

impl At {
    fn new(position: f64, dx: i32) -> Self {
        Self { position, dx }
    }
}

/// A piece of the notation.
#[derive(Debug, Clone, PartialEq)]
enum Item {
    /// A glyph whose anchor is at `at`, row `y`. Noteheads in stacked thirds drop their top or
    /// bottom row.
    Glyph {
        glyph: Glyph,
        at: At,
        y: i32,
        trim: Trim,
    },
    /// A bar `height` rows high from `from` to just before `to`: a stem, a beam, a ledger line or
    /// the middle of a tie.
    Bar {
        from: At,
        to: At,
        y: i32,
        height: i32,
    },
}

impl Item {
    fn glyph(glyph: Glyph, at: At, y: i32) -> Self {
        Self::Glyph {
            glyph,
            at,
            y,
            trim: Trim::default(),
        }
    }

    fn bar(from: At, to: At, y: i32, height: i32) -> Self {
        Self::Bar {
            from,
            to,
            y,
            height,
        }
    }

    /// The first and last rows it covers.
    fn rows(&self) -> (i32, i32) {
        match *self {
            Self::Glyph { glyph, y, .. } => {
                let (anchor, rows) = glyph.bitmap();
                let top = y - anchor;
                (top, top + i32::try_from(rows.len()).unwrap_or(0) - 1)
            }
            Self::Bar { y, height, .. } => (y, y + height - 1),
        }
    }

    fn shift(&mut self, rows: i32) {
        match self {
            Self::Glyph { y, .. } | Self::Bar { y, .. } => *y += rows,
        }
    }

    /// Add its pixels between columns `left` and `right` on `axis` to `runs`.
    fn runs(&self, axis: &Axis, left: i32, right: i32, runs: &mut Vec<Run>) {
        match *self {
            Self::Glyph { glyph, at, y, trim } => {
                let x = axis.x(at.position) + at.dx;
                if x > right || x + glyph.width() < left {
                    return;
                }
                glyph_runs(glyph, x, y, trim, runs, |run| clip(run, left, right));
            }
            Self::Bar {
                from,
                to,
                y,
                height,
            } => {
                let start = axis.x(from.position) + from.dx;
                let end = axis.x(to.position) + to.dx;
                for row in y..y + height {
                    let run = Run {
                        x: start,
                        y: row,
                        length: end - start,
                    };
                    if let Some(run) = clip(run, left, right) {
                        runs.push(run);
                    }
                }
            }
        }
    }
}

/// Which rows of a notehead to leave out.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
struct Trim {
    top: bool,
    bottom: bool,
}

/// The runs of a glyph with its anchor at `(x, y)`, through `keep`.
fn glyph_runs(
    glyph: Glyph,
    x: i32,
    y: i32,
    trim: Trim,
    runs: &mut Vec<Run>,
    keep: impl Fn(Run) -> Option<Run>,
) {
    let (anchor, rows) = glyph.bitmap();
    let last = rows.len().saturating_sub(1);
    for (index, row) in rows.iter().enumerate() {
        if (trim.top && index == 0) || (trim.bottom && index == last) {
            continue;
        }
        let row_y = y - anchor + i32::try_from(index).unwrap_or(0);
        let mut column = 0;
        for set in row.split('.') {
            let length = i32::try_from(set.len()).unwrap_or(0);
            if length > 0 {
                if let Some(run) = keep(Run {
                    x: x + column,
                    y: row_y,
                    length,
                }) {
                    runs.push(run);
                }
            }
            column += length + 1;
        }
    }
}

/// The part of `run` between columns `left` and `right`.
fn clip(run: Run, left: i32, right: i32) -> Option<Run> {
    let start = run.x.max(left);
    let end = (run.x + run.length).min(right);
    (end > start).then_some(Run {
        x: start,
        y: run.y,
        length: end - start,
    })
}

/// How a pitch is written: athenaCL's spelling, with sharps, and a quarter-sharp for its quarter
/// tones.
#[derive(Debug, Clone, PartialEq, Eq)]
struct Spelling {
    /// Diatonic steps above middle C.
    step: i32,
    accidental: Option<Glyph>,
    name: String,
}

impl Spelling {
    fn new(pitch: f64) -> Self {
        let quarters = (pitch * 2.0).round() as i32;
        let semitone = quarters.div_euclid(2);
        let quarter = quarters.rem_euclid(2) == 1;
        let (letter, sharp) = match semitone.rem_euclid(12) {
            1 => (0, true),
            2 => (1, false),
            3 => (1, true),
            4 => (2, false),
            5 => (3, false),
            6 => (3, true),
            7 => (4, false),
            8 => (4, true),
            9 => (5, false),
            10 => (5, true),
            11 => (6, false),
            _ => (0, false),
        };
        let octave = semitone.div_euclid(12);
        let accidental = match (sharp, quarter) {
            (true, true) => Some(Glyph::ThreeQuarterSharp),
            (true, false) => Some(Glyph::Sharp),
            (false, true) => Some(Glyph::QuarterSharp),
            (false, false) => None,
        };
        let name = format!(
            "{}{}{}{}",
            "CDEFGAB".chars().nth(letter).unwrap_or('C'),
            if sharp { "#" } else { "" },
            if quarter { "~" } else { "" },
            octave + 4
        );
        Self {
            step: octave * 7 + i32::try_from(letter).unwrap_or(0),
            accidental,
            name,
        }
    }
}

/// Where events are on the x axis: in seconds, or in slots, one per onset.
struct Slots {
    domain: Domain,
    onsets: Vec<f64>,
}

impl Slots {
    fn new(events: &[&Event], domain: Domain) -> Self {
        let mut onsets: Vec<f64> = Vec::new();
        for event in events {
            if onsets
                .last()
                .is_none_or(|&last| event.time - last > TOGETHER)
            {
                onsets.push(event.time);
            }
        }
        Self { domain, onsets }
    }

    /// The x axis value of `seconds` into `event`.
    fn position(&self, event: &Event, seconds: f64) -> f64 {
        match self.domain {
            Domain::Time => event.time + seconds,
            Domain::Events => {
                let slot = self
                    .onsets
                    .iter()
                    .position(|&onset| (onset - event.time).abs() <= TOGETHER)
                    .unwrap_or(0) as f64;
                slot + (seconds / event.duration.max(f64::EPSILON)).min(1.0)
            }
        }
    }
}

/// A written duration.
#[derive(Debug, Clone, Copy, PartialEq)]
struct Value {
    head: Head,
    /// Beams or flags: 1 for eighths, 2 for sixteenths, 3 for thirty-seconds.
    flags: i32,
    dotted: bool,
    /// The tuplet the note is in: 3 for a triplet.
    tuplet: Option<u8>,
    /// How long it plays, in beats.
    beats: f64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Head {
    Black,
    Half,
    Whole,
}

/// Written durations in ticks, longest first.
const VALUES: [(i64, Head, i32, bool); 11] = [
    (960, Head::Whole, 0, false),
    (720, Head::Half, 0, true),
    (480, Head::Half, 0, false),
    (360, Head::Black, 0, true),
    (240, Head::Black, 0, false),
    (180, Head::Black, 1, true),
    (120, Head::Black, 1, false),
    (90, Head::Black, 2, true),
    (60, Head::Black, 2, false),
    (45, Head::Black, 3, true),
    (30, Head::Black, 3, false),
];

impl Value {
    /// The values that add up to `beats`, tied, longest first. Durations in thirds or fifths of
    /// a beat are tuplets; others are rounded to 64ths.
    fn split(beats: f64) -> Vec<Self> {
        let ticks = ((beats.max(0.0) * TICKS).round() as i64).max(30);
        let (written, tuplet) = if ticks % 15 == 0 {
            (ticks, None)
        } else if ticks % 20 == 0 {
            (ticks * 3 / 2, Some(3))
        } else if ticks % 48 == 0 {
            (ticks * 5 / 4, Some(5))
        } else {
            ((ticks as f64 / 15.0).round() as i64 * 15, None)
        };
        let played = beats.max(0.0) / written as f64;
        let mut left = written;
        let mut values = Vec::new();
        while left >= 30 {
            let Some(&(length, head, flags, dotted)) =
                VALUES.iter().find(|(length, ..)| *length <= left)
            else {
                break;
            };
            values.push(Self {
                head,
                flags,
                dotted,
                tuplet,
                beats: length as f64 * played,
            });
            left -= length;
        }
        values
    }
}

/// An event's part as written: a chord or a rest, in one written duration.
#[derive(Debug, Clone)]
struct Written {
    /// The events it shows.
    events: Vec<usize>,
    staff: usize,
    position: f64,
    /// Its beat, counted from the start, for beaming.
    beat: f64,
    /// How long it plays, in seconds.
    seconds: f64,
    value: Value,
    /// The chord's pitches, none for a rest.
    pitches: Vec<Spelling>,
    /// Whether it's tied to the next part.
    tied: bool,
}

/// The events as written: chords and rests, split into written durations.
fn write(events: &[Event], slots: &Slots, staves: &[Staff]) -> Vec<Written> {
    let mut order: Vec<usize> = (0..events.len()).collect();
    order.sort_by(|&a, &b| {
        let time = |i: usize| events.get(i).map_or(0.0, |event| event.time);
        time(a).total_cmp(&time(b))
    });
    let mut written = Vec::new();
    let mut last_staff = 0;
    let mut index = 0;
    while let Some(&first) = order.get(index) {
        let Some(event) = events.get(first) else {
            break;
        };
        // a chord: the sounding events starting together, one per staff
        let together: Vec<usize> = order
            .iter()
            .skip(index)
            .take_while(|&&i| {
                events
                    .get(i)
                    .is_some_and(|other| (other.time - event.time).abs() <= TOGETHER)
            })
            .copied()
            .collect();
        index += together.len();
        let sounding: Vec<usize> = together
            .iter()
            .copied()
            .filter(|&i| events.get(i).is_some_and(|event| event.sounds))
            .collect();
        if sounding.is_empty() {
            written.extend(parts(event, first, last_staff, Vec::new(), slots));
            continue;
        }
        for (staff, chord) in by_staff(&sounding, events, staves) {
            last_staff = staff;
            let pitches = chord
                .iter()
                .filter_map(|&i| events.get(i))
                .map(|event| Spelling::new(event.pitch))
                .collect();
            let mut chord_parts = parts(event, first, staff, pitches, slots);
            for part in &mut chord_parts {
                part.events.clone_from(&chord);
            }
            written.extend(chord_parts);
        }
    }
    written
}

/// The events of a chord, by the staff they're written on.
fn by_staff(chord: &[usize], events: &[Event], staves: &[Staff]) -> Vec<(usize, Vec<usize>)> {
    let staff_of = |i: usize| {
        let step = events
            .get(i)
            .map_or(0, |event| Spelling::new(event.pitch).step);
        // on a grand staff, middle C and above go on the treble staff
        if staves.len() > 1 && step < 0 {
            1
        } else {
            0
        }
    };
    let mut staves_used: Vec<(usize, Vec<usize>)> = Vec::new();
    for &i in chord {
        let staff = staff_of(i);
        match staves_used.iter_mut().find(|(used, _)| *used == staff) {
            Some((_, members)) => members.push(i),
            None => staves_used.push((staff, vec![i])),
        }
    }
    staves_used
}

/// An event's written parts, tied.
fn parts(
    event: &Event,
    index: usize,
    staff: usize,
    pitches: Vec<Spelling>,
    slots: &Slots,
) -> Vec<Written> {
    let tempo = if event.tempo > 0.0 {
        event.tempo
    } else {
        120.0
    };
    let beats = event.duration * tempo / 60.0;
    let values = Value::split(beats);
    let count = values.len();
    let mut elapsed = 0.0;
    values
        .into_iter()
        .enumerate()
        .map(|(part, value)| {
            let seconds = elapsed * 60.0 / tempo;
            let written = Written {
                events: vec![index],
                staff,
                position: slots.position(event, seconds),
                beat: event.time * tempo / 60.0 + elapsed,
                seconds: value.beats * 60.0 / tempo,
                value,
                pitches: pitches.clone(),
                tied: !pitches.is_empty() && part + 1 < count,
            };
            elapsed += value.beats;
            written
        })
        .collect()
}

/// Lays written notes out as items.
struct Engraver {
    staves: Vec<Staff>,
    written: Vec<Written>,
    items: Vec<Item>,
    notes: Vec<Note>,
    readable: f64,
}

impl Engraver {
    fn new(staves: Vec<Staff>) -> Self {
        Self {
            staves,
            written: Vec::new(),
            items: Vec::new(),
            notes: Vec::new(),
            readable: f64::INFINITY,
        }
    }

    fn add(&mut self, written: Written) {
        self.written.push(written);
    }

    fn staff(&self, index: usize) -> Staff {
        self.staves.get(index).copied().unwrap_or(Staff {
            clef: Clef::Treble,
            top: 0,
        })
    }

    /// Engrave everything written: rests, then notes in beamed groups.
    fn engrave(&mut self) {
        let written = std::mem::take(&mut self.written);
        let mut groups: Vec<Vec<&Written>> = Vec::new();
        for part in &written {
            if part.pitches.is_empty() {
                self.rest(part);
                continue;
            }
            // shorter than a beat, in the same beat and tuplet as the note before: beamed to it
            let beamed = groups
                .last()
                .and_then(|group| group.last())
                .is_some_and(|last| {
                    last.value.flags > 0
                        && part.value.flags > 0
                        && last.staff == part.staff
                        && last.value.tuplet == part.value.tuplet
                        && beat_of(last.beat) == beat_of(part.beat)
                        && !last.tied
                });
            match groups.last_mut() {
                Some(group) if beamed => group.push(part),
                _ => groups.push(vec![part]),
            }
        }
        for group in &groups {
            self.group(group);
        }
        for tuplet in unbeamed_tuplets(&groups) {
            self.tuplet_over(&tuplet);
        }
        for pair in written.windows(2) {
            if let [part, next] = pair {
                if part.tied {
                    self.tie(part, next);
                }
            }
        }
        self.readable = written
            .iter()
            .map(|part| part.seconds)
            .filter(|&seconds| seconds > 0.0)
            .fold(f64::INFINITY, f64::min);
        self.written = written;
    }

    /// A rest, on its staff's middle.
    fn rest(&mut self, part: &Written) {
        let staff = self.staff(part.staff);
        let value = part.value;
        let (glyph, line) = match (value.head, value.flags) {
            (Head::Whole, _) => (Glyph::RestWhole, 6),
            (Head::Half, _) => (Glyph::RestHalf, 4),
            (Head::Black, 0) => (Glyph::RestQuarter, 4),
            (Head::Black, 1) => (Glyph::Rest8, 4),
            (Head::Black, 2) => (Glyph::Rest16, 4),
            (Head::Black, _) => (Glyph::Rest32, 4),
        };
        let y = staff.top + STAFF - SPACE / 2 * line;
        let at = At::new(part.position, 1);
        self.items.push(Item::glyph(glyph, at, y));
        if value.dotted {
            let dot = At::new(part.position, 1 + glyph.width() + 1);
            self.items
                .push(Item::glyph(Glyph::Dot, dot, staff.top + STAFF - 10));
        }
        let (top, bottom) = Item::glyph(glyph, at, y).rows();
        for &event in &part.events {
            self.notes.push(Note {
                event,
                name: "REST".to_owned(),
                position: part.position,
                left: 1,
                width: glyph.width(),
                top,
                bottom,
            });
        }
    }

    /// Notes beamed together, or a single note.
    fn group(&mut self, group: &[&Written]) {
        let Some(first) = group.first() else {
            return;
        };
        let staff = self.staff(first.staff);
        let rows: Vec<Vec<i32>> = group
            .iter()
            .map(|part| {
                part.pitches
                    .iter()
                    .map(|pitch| staff.row(pitch.step))
                    .collect()
            })
            .collect();
        let middle = staff.top + STAFF / 2;
        // stems point away from the note farthest from the middle line
        let farthest = rows
            .iter()
            .flatten()
            .copied()
            .max_by_key(|&row| ((row - middle).abs(), row < middle))
            .unwrap_or(middle);
        let up = farthest > middle;

        for (part, rows) in group.iter().zip(&rows) {
            self.chord(part, rows, up, staff);
        }

        let beamed = group.len() > 1;
        let flags = group.iter().map(|part| part.value.flags).max().unwrap_or(0);
        let extra = if flags > 1 { flags - 1 } else { 0 };
        let beam = if up {
            let mut beam = rows.iter().flatten().copied().min().unwrap_or(middle) - STEM - extra;
            while (0..flags).any(|level| {
                let row = beam + level * BEAM_PITCH;
                staff.is_line(row) || staff.is_line(row + 1)
            }) {
                beam -= 1;
            }
            beam
        } else {
            let mut beam = rows.iter().flatten().copied().max().unwrap_or(middle) + STEM + extra;
            while (0..flags).any(|level| {
                let row = beam - level * BEAM_PITCH;
                staff.is_line(row) || staff.is_line(row - 1)
            }) {
                beam += 1;
            }
            beam
        };

        for (part, rows) in group.iter().zip(&rows) {
            if part.value.head == Head::Whole {
                continue;
            }
            let (low, high) = (
                rows.iter().copied().max().unwrap_or(middle),
                rows.iter().copied().min().unwrap_or(middle),
            );
            let tip = if beamed {
                beam
            } else if up {
                high - STEM - 3 * (part.value.flags - 1).max(0)
            } else {
                low + STEM + 3 * (part.value.flags - 1).max(0)
            };
            let dx = if up { STEM_UP } else { 0 };
            let (from, to) = if up { (tip, low) } else { (high, tip) };
            self.items.push(Item::bar(
                At::new(part.position, dx),
                At::new(part.position, dx + 1),
                from,
                to - from + 1,
            ));
            if !beamed && part.value.flags > 0 {
                let flag = match (part.value.flags, up) {
                    (1, true) => Glyph::Flag8Up,
                    (2, true) => Glyph::Flag16Up,
                    (_, true) => Glyph::Flag32Up,
                    (1, false) => Glyph::Flag8Down,
                    (2, false) => Glyph::Flag16Down,
                    (_, false) => Glyph::Flag32Down,
                };
                self.items
                    .push(Item::glyph(flag, At::new(part.position, dx), tip));
            }
        }
        if beamed {
            self.beams(group, up, beam);
        }
        if beamed {
            self.tuplet(group, up, beam);
        }
    }

    /// A chord's heads, their accidentals, dots and ledger lines.
    fn chord(&mut self, part: &Written, rows: &[i32], up: bool, staff: Staff) {
        let mut placed: Vec<Placed> = part
            .pitches
            .iter()
            .zip(rows)
            .zip(&part.events)
            .map(|((pitch, &row), &event)| Placed {
                event,
                row,
                dx: 0,
                position: staff.clef.position(pitch.step),
                trim: Trim::default(),
                accidental: pitch.accidental,
                name: pitch.name.clone(),
            })
            .collect();
        // from the stem's end: a second from the previous head goes on the stem's other side
        placed.sort_by_key(|head| if up { -head.row } else { head.row });
        let side = if up { STEM_UP } else { -STEM_UP };
        let mut previous: Option<(i32, i32)> = None;
        for head in &mut placed {
            if let Some((row, dx)) = previous {
                if (row - head.row).abs() == SPACE / 2 && dx == 0 {
                    head.dx = side;
                }
            }
            previous = Some((head.row, head.dx));
        }
        // stacked thirds would share a row: both heads drop it
        let count = placed.len();
        for i in 0..count {
            for j in 0..count {
                let (Some(a), Some(b)) = (placed.get(i), placed.get(j)) else {
                    continue;
                };
                if a.dx == b.dx && b.row - a.row == SPACE {
                    if let Some(upper) = placed.get_mut(i) {
                        upper.trim.bottom = true;
                    }
                    if let Some(lower) = placed.get_mut(j) {
                        lower.trim.top = true;
                    }
                }
            }
        }

        let glyph = match part.value.head {
            Head::Black => Glyph::NoteheadBlack,
            Head::Half => Glyph::NoteheadHalf,
            Head::Whole => Glyph::NoteheadWhole,
        };
        let width = glyph.width();
        let leftmost = placed.iter().map(|head| head.dx).min().unwrap_or(0);
        let mut columns: Vec<Vec<i32>> = Vec::new();
        let mut by_row = placed.clone();
        by_row.sort_by_key(|head| head.row);
        for head in &by_row {
            let Some(accidental) = head.accidental else {
                continue;
            };
            // accidentals that would overlap move a column further left
            let column = columns
                .iter()
                .position(|rows| rows.iter().all(|&row| (row - head.row).abs() > 10))
                .unwrap_or(columns.len());
            match columns.get_mut(column) {
                Some(rows) => rows.push(head.row),
                None => columns.push(vec![head.row]),
            }
            let dx = leftmost - accidental.width() - 2 - 8 * i32::try_from(column).unwrap_or(0);
            self.items.push(Item::glyph(
                accidental,
                At::new(part.position, dx),
                head.row,
            ));
        }
        for head in &placed {
            let at = At::new(part.position, head.dx);
            self.items.push(Item::Glyph {
                glyph,
                at,
                y: head.row,
                trim: head.trim,
            });
            for ledger in ledgers(head.position) {
                let row = staff.top + STAFF - SPACE / 2 * ledger;
                self.items.push(Item::bar(
                    At::new(part.position, head.dx - 2),
                    At::new(part.position, head.dx + width + 2),
                    row,
                    1,
                ));
            }
            if part.value.dotted {
                let row = if head.position % 2 == 0 {
                    head.row - SPACE / 2
                } else {
                    head.row
                };
                let dx = placed.iter().map(|head| head.dx).max().unwrap_or(0) + width + 1;
                self.items
                    .push(Item::glyph(Glyph::Dot, At::new(part.position, dx), row));
            }
        }
        for head in &placed {
            self.notes.push(Note {
                event: head.event,
                name: head.name.clone(),
                position: part.position,
                left: head.dx,
                width,
                top: head.row - 2,
                bottom: head.row + 2,
            });
        }
    }

    /// The beams of a group, `beam` being the outer one's outer row.
    fn beams(&mut self, group: &[&Written], up: bool, beam: i32) {
        let dx = if up { STEM_UP } else { 0 };
        let flags = group.iter().map(|part| part.value.flags).max().unwrap_or(1);
        for level in 0..flags {
            let y = if up {
                beam + level * BEAM_PITCH
            } else {
                beam - level * BEAM_PITCH - (BEAM - 1)
            };
            let mut k = 0;
            while k < group.len() {
                let reaches = |i: usize| group.get(i).is_some_and(|part| part.value.flags > level);
                if !reaches(k) {
                    k += 1;
                    continue;
                }
                let mut j = k;
                while reaches(j + 1) {
                    j += 1;
                }
                let (Some(first), Some(last)) = (group.get(k), group.get(j)) else {
                    break;
                };
                let (from, to) = if j > k {
                    (At::new(first.position, dx), At::new(last.position, dx + 1))
                } else if k + 1 == group.len() {
                    // a lone short note at the end hooks back toward the others
                    (
                        At::new(first.position, dx - 3),
                        At::new(first.position, dx + 1),
                    )
                } else {
                    (At::new(first.position, dx), At::new(first.position, dx + 4))
                };
                self.items.push(Item::bar(from, to, y, BEAM));
                k = j + 1;
            }
        }
    }

    /// A beamed tuplet's count, beyond its beam.
    fn tuplet(&mut self, group: &[&Written], up: bool, beam: i32) {
        let Some(glyph) = group.first().and_then(|part| tuplet_glyph(part.value)) else {
            return;
        };
        let (Some(first), Some(last)) = (group.first(), group.last()) else {
            return;
        };
        let position = (first.position + last.position) / 2.0;
        let (dx, y) = if up {
            (STEM_UP - 1, beam - 2)
        } else {
            (-1, beam + 7)
        };
        self.items
            .push(Item::glyph(glyph, At::new(position, dx), y));
    }

    /// An unbeamed tuplet's count, over its middle note.
    fn tuplet_over(&mut self, tuplet: &[&Written]) {
        let Some(middle) = tuplet.get(tuplet.len() / 2) else {
            return;
        };
        let Some(glyph) = tuplet_glyph(middle.value) else {
            return;
        };
        let staff = self.staff(middle.staff);
        // above the highest note, or the staff
        let top = tuplet
            .iter()
            .flat_map(|part| part.pitches.iter().map(|pitch| staff.row(pitch.step)))
            .min()
            .unwrap_or(staff.top)
            .min(staff.top);
        self.items.push(Item::glyph(
            glyph,
            At::new(middle.position, 1),
            top - STEM - 2,
        ));
    }

    /// Ties from a part's heads to the next part's.
    fn tie(&mut self, part: &Written, next: &Written) {
        let staff = self.staff(part.staff);
        let middle = staff.top + STAFF / 2;
        for pitch in &part.pitches {
            let row = staff.row(pitch.step);
            let from = part.position;
            let to = next.position;
            // over the notes when their stems point down
            if row <= middle {
                let y = row - 3;
                self.items
                    .push(Item::glyph(Glyph::TieStartAbove, At::new(from, 3), y));
                self.items
                    .push(Item::bar(At::new(from, 6), At::new(to, 1), y - 1, 1));
                self.items
                    .push(Item::glyph(Glyph::TieEndAbove, At::new(to, 1), y));
            } else {
                let y = row + 3;
                self.items
                    .push(Item::glyph(Glyph::TieStartBelow, At::new(from, 3), y));
                self.items
                    .push(Item::bar(At::new(from, 6), At::new(to, 1), y + 1, 1));
                self.items
                    .push(Item::glyph(Glyph::TieEndBelow, At::new(to, 1), y));
            }
        }
    }

    /// Dynamics under the lowest staff: each beat's average level, where it changes. Averaging
    /// by beat keeps random amplitudes from printing a mark on every note.
    fn dynamics(&mut self, events: &[Event], slots: &Slots) {
        let lowest = self
            .items
            .iter()
            .map(|item| item.rows().1)
            .chain(self.staves.iter().map(|staff| staff.top + STAFF))
            .max()
            .unwrap_or(STAFF);
        let baseline = lowest + DYNAMICS_GAP;
        let mut order: Vec<&Event> = events.iter().filter(|event| event.sounds).collect();
        order.sort_by(|a, b| a.time.total_cmp(&b.time));
        let mut beats: Vec<(i64, &Event, f64, u32)> = Vec::new();
        for event in order {
            let tempo = if event.tempo > 0.0 {
                event.tempo
            } else {
                120.0
            };
            let beat = beat_of(event.time * tempo / 60.0);
            match beats.last_mut() {
                Some((last, _, sum, count)) if *last == beat => {
                    *sum += event.amplitude;
                    *count += 1;
                }
                _ => beats.push((beat, event, event.amplitude, 1)),
            }
        }
        let mut last = None;
        for (_, first, sum, count) in beats {
            let mark = dynamic(sum / f64::from(count));
            if last == Some(mark) {
                continue;
            }
            last = Some(mark);
            let position = slots.position(first, 0.0);
            let mut dx = 0;
            for letter in mark.chars() {
                let glyph = match letter {
                    'p' => Glyph::Piano,
                    'm' => Glyph::Mezzo,
                    _ => Glyph::Forte,
                };
                self.items
                    .push(Item::glyph(glyph, At::new(position, dx), baseline));
                dx += LETTER;
            }
        }
    }

    /// Move everything so the top is a margin down, and finish the score.
    fn finish(mut self, slots: &Slots) -> Score {
        let mut pinned = Vec::new();
        let mut top = self
            .items
            .iter()
            .map(|item| item.rows().0)
            .chain(self.staves.iter().map(|staff| staff.top))
            .min()
            .unwrap_or(0);
        for staff in &self.staves {
            let clef = staff.clef.glyph();
            let (anchor, _) = clef.bitmap();
            top = top.min(staff.top + STAFF - SPACE / 2 * staff.clef.line() - anchor);
        }
        let shift = MARGIN - top;
        for item in &mut self.items {
            item.shift(shift);
        }
        for staff in &mut self.staves {
            staff.top += shift;
        }
        for note in &mut self.notes {
            note.top += shift;
            note.bottom += shift;
        }
        for staff in &self.staves {
            let y = staff.top + STAFF - SPACE / 2 * staff.clef.line();
            glyph_runs(
                staff.clef.glyph(),
                CLEF_X,
                y,
                Trim::default(),
                &mut pinned,
                Some,
            );
        }
        // a grand staff's staves are joined at the left
        if let (Some(first), Some(last)) = (self.staves.first(), self.staves.last()) {
            if self.staves.len() > 1 {
                for y in first.top..=last.top + STAFF {
                    pinned.push(Run { x: 0, y, length: 1 });
                }
            }
        }
        let bottom = self
            .items
            .iter()
            .map(|item| item.rows().1)
            .chain(self.staves.iter().map(|staff| staff.top + STAFF))
            .chain(pinned.iter().map(|run| run.y))
            .max()
            .unwrap_or(0);
        let extent = self.extent(slots);
        let readable = match slots.domain {
            Domain::Time if self.readable.is_finite() && self.readable > 0.0 => {
                READABLE / self.readable
            }
            Domain::Time => READABLE,
            Domain::Events => SLOT,
        };
        Score {
            staves: self.staves,
            items: self.items,
            pinned,
            notes: self.notes,
            extent,
            readable,
            height: bottom + MARGIN + 1,
        }
    }

    /// From the first part to the end of the last.
    fn extent(&self, slots: &Slots) -> (f64, f64) {
        let start = self
            .written
            .iter()
            .map(|part| part.position)
            .fold(f64::INFINITY, f64::min);
        let end = match slots.domain {
            Domain::Time => self
                .written
                .iter()
                .map(|part| part.position + part.seconds)
                .fold(f64::NEG_INFINITY, f64::max),
            Domain::Events => slots.onsets.len() as f64,
        };
        if start.is_finite() && end > start {
            (start, end)
        } else {
            (0.0, 1.0)
        }
    }
}

/// A head as placed in its chord.
#[derive(Debug, Clone)]
struct Placed {
    /// The event it shows.
    event: usize,
    row: i32,
    /// Across from the chord's left edge: a head a second from its neighbor goes on the stem's
    /// other side.
    dx: i32,
    /// Its position on the staff.
    position: i32,
    trim: Trim,
    accidental: Option<Glyph>,
    name: String,
}

/// The count of a tuplet's value.
fn tuplet_glyph(value: Value) -> Option<Glyph> {
    value.tuplet.map(|count| match count {
        3 => Glyph::Tuplet3,
        5 => Glyph::Tuplet5,
        6 => Glyph::Tuplet6,
        _ => Glyph::Tuplet7,
    })
}

/// Unbeamed tuplet notes in runs of as many as the tuplet counts: three for a triplet.
fn unbeamed_tuplets<'w>(groups: &[Vec<&'w Written>]) -> Vec<Vec<&'w Written>> {
    let mut tuplets: Vec<Vec<&Written>> = Vec::new();
    for group in groups {
        let [single] = group.as_slice() else {
            continue;
        };
        let Some(count) = single.value.tuplet else {
            continue;
        };
        let joins = tuplets.last().is_some_and(|run| {
            run.len() < usize::from(count)
                && run.last().is_some_and(|last| {
                    last.staff == single.staff && last.value.tuplet == Some(count)
                })
        });
        match tuplets.last_mut() {
            Some(run) if joins => run.push(single),
            _ => tuplets.push(vec![single]),
        }
    }
    tuplets
}

/// The whole beat a beat position is in.
fn beat_of(beat: f64) -> i64 {
    (beat + 1e-9).floor() as i64
}

/// The staff positions of the ledger lines a note at `position` needs.
fn ledgers(position: i32) -> Vec<i32> {
    let mut lines = Vec::new();
    let mut below = -2;
    while below >= position {
        lines.push(below);
        below -= 2;
    }
    let mut above = 10;
    while above <= position {
        lines.push(above);
        above += 2;
    }
    lines
}

/// The dynamics mark of an amplitude.
fn dynamic(amplitude: f64) -> &'static str {
    [
        (0.3, "pp"),
        (0.45, "p"),
        (0.6, "mp"),
        (0.75, "mf"),
        (0.9, "f"),
    ]
    .into_iter()
    .find(|&(limit, _)| amplitude < limit)
    .map_or("ff", |(_, mark)| mark)
}

#[cfg(test)]
mod tests {
    #![expect(clippy::float_cmp, reason = "the tests assert exact values")]

    use super::*;

    fn event(time: f64, duration: f64, pitch: f64) -> Event {
        Event {
            time,
            duration,
            sustain: duration,
            sounds: true,
            pitch,
            amplitude: 0.7,
            tempo: 120.0,
        }
    }

    fn rest(time: f64, duration: f64) -> Event {
        Event {
            sounds: false,
            ..event(time, duration, 0.0)
        }
    }

    /// Eighth notes at 120 BPM, one per pitch.
    fn eighths(pitches: &[f64]) -> Vec<Event> {
        pitches
            .iter()
            .enumerate()
            .map(|(i, &pitch)| event(i as f64 * 0.25, 0.25, pitch))
            .collect()
    }

    fn axis() -> Axis {
        Axis {
            origin: 40,
            start: 0.0,
            scale: 80.0,
        }
    }

    fn pixels(score: &Score) -> Vec<(i32, i32)> {
        score
            .runs(&axis(), 0, 1000)
            .into_iter()
            .flat_map(|run| (run.x..run.x + run.length).map(move |x| (x, run.y)))
            .collect()
    }

    #[test]
    fn pitches_are_spelled_with_sharps() {
        assert_eq!(Spelling::new(0.0).name, "C4");
        assert_eq!(Spelling::new(1.0).name, "C#4");
        assert_eq!(Spelling::new(1.0).accidental, Some(Glyph::Sharp));
        assert_eq!(Spelling::new(-1.0).name, "B3");
        assert_eq!(Spelling::new(-1.0).step, -1);
        assert_eq!(Spelling::new(21.0).name, "A5");
        assert_eq!(Spelling::new(21.0).step, 12);
    }

    #[test]
    fn quarter_tones_get_quarter_sharps() {
        assert_eq!(Spelling::new(0.5).name, "C~4");
        assert_eq!(Spelling::new(0.5).accidental, Some(Glyph::QuarterSharp));
        assert_eq!(
            Spelling::new(1.5).accidental,
            Some(Glyph::ThreeQuarterSharp)
        );
        // three quarters of a semitone rounds up to the next one
        assert_eq!(Spelling::new(1.8).name, "D4");
    }

    #[test]
    fn durations_are_written_as_note_values() {
        let one = |beats| {
            let values = Value::split(beats);
            assert_eq!(values.len(), 1, "{beats} beats is one value");
            values.into_iter().next().unwrap()
        };
        assert_eq!(one(1.0).flags, 0);
        assert_eq!(one(0.5).flags, 1);
        assert_eq!(one(0.25).flags, 2);
        assert!(one(0.75).dotted);
        assert_eq!(one(2.0).head, Head::Half);
        assert_eq!(one(4.0).head, Head::Whole);
    }

    #[test]
    fn odd_durations_are_tied() {
        // five sixteenths: a quarter tied to a sixteenth
        let values = Value::split(1.25);
        assert_eq!(values.len(), 2);
        assert_eq!(values.iter().map(|value| value.beats).sum::<f64>(), 1.25);
    }

    #[test]
    fn thirds_of_a_beat_are_triplets() {
        let values = Value::split(1.0 / 3.0);
        assert_eq!(values.len(), 1);
        assert_eq!(values[0].tuplet, Some(3));
        assert_eq!(values[0].flags, 1);
        assert!((values[0].beats - 1.0 / 3.0).abs() < 1e-9);
    }

    #[test]
    fn fifths_of_a_beat_are_quintuplets() {
        let values = Value::split(0.2);
        assert_eq!(values[0].tuplet, Some(5));
        assert_eq!(values[0].flags, 2);
    }

    #[test]
    fn high_or_low_notes_choose_the_clef() {
        let treble = Score::new(&eighths(&[0.0, 7.0, 19.0]), Domain::Time);
        assert_eq!(treble.staves().len(), 1);
        assert_eq!(treble.staves()[0].clef, Clef::Treble);

        let bass = Score::new(&eighths(&[-24.0, -17.0, -12.0]), Domain::Time);
        assert_eq!(bass.staves()[0].clef, Clef::Bass);

        let both = Score::new(&eighths(&[-24.0, 24.0]), Domain::Time);
        assert_eq!(
            both.staves()
                .iter()
                .map(|staff| staff.clef)
                .collect::<Vec<_>>(),
            [Clef::Treble, Clef::Bass]
        );
    }

    #[test]
    fn notes_sit_at_their_times() {
        let events = eighths(&[0.0, 2.0, 4.0, 5.0]);
        let score = Score::new(&events, Domain::Time);
        let axis = axis();
        for (i, event) in events.iter().enumerate() {
            let note = score.notes.iter().find(|note| note.event == i).unwrap();
            assert_eq!(note.bounds(&axis).0, axis.x(event.time));
        }
    }

    #[test]
    fn events_get_equal_slots_in_event_mode() {
        let events = vec![
            event(0.0, 1.0, 0.0),
            event(1.0, 0.25, 2.0),
            event(1.25, 2.0, 4.0),
        ];
        let score = Score::new(&events, Domain::Events);
        let axis = axis();
        let lefts: Vec<i32> = (0..3)
            .map(|i| {
                let note = score.notes.iter().find(|note| note.event == i).unwrap();
                note.bounds(&axis).0
            })
            .collect();
        assert_eq!(lefts[1] - lefts[0], lefts[2] - lefts[1]);
        assert_eq!(score.readable_scale(), SLOT);
    }

    #[test]
    fn the_readable_scale_gives_the_shortest_note_ten_pixels() {
        let score = Score::new(&eighths(&[0.0, 2.0]), Domain::Time);
        // an eighth at 120 BPM is a quarter of a second
        assert_eq!(score.readable_scale(), 40.0);
    }

    #[test]
    fn eighths_in_a_beat_are_beamed() {
        let score = Score::new(&eighths(&[0.0, 2.0]), Domain::Time);
        let beams = score
            .items
            .iter()
            .filter(|item| matches!(item, Item::Bar { height: BEAM, .. }))
            .count();
        assert_eq!(beams, 1);
        let flags = score
            .items
            .iter()
            .filter(|item| {
                matches!(
                    item,
                    Item::Glyph {
                        glyph: Glyph::Flag8Up | Glyph::Flag8Down,
                        ..
                    }
                )
            })
            .count();
        assert_eq!(flags, 0);
    }

    #[test]
    fn a_lone_eighth_is_flagged() {
        let score = Score::new(&[event(0.0, 0.25, 0.0)], Domain::Time);
        assert!(score.items.iter().any(|item| matches!(
            item,
            Item::Glyph {
                glyph: Glyph::Flag8Up,
                ..
            }
        )));
    }

    #[test]
    fn rests_show_as_rests() {
        let score = Score::new(&[event(0.0, 0.5, 0.0), rest(0.5, 0.5)], Domain::Time);
        assert!(score.items.iter().any(|item| matches!(
            item,
            Item::Glyph {
                glyph: Glyph::RestQuarter,
                ..
            }
        )));
        assert!(score.notes.iter().any(|note| note.name == "REST"));
    }

    #[test]
    fn accidentals_are_printed_on_every_note() {
        let score = Score::new(&eighths(&[1.0, 1.0]), Domain::Time);
        let sharps = score
            .items
            .iter()
            .filter(|item| {
                matches!(
                    item,
                    Item::Glyph {
                        glyph: Glyph::Sharp,
                        ..
                    }
                )
            })
            .count();
        assert_eq!(sharps, 2);
    }

    #[test]
    fn high_notes_get_ledger_lines() {
        assert_eq!(ledgers(4), Vec::<i32>::new());
        assert_eq!(ledgers(10), [10]);
        assert_eq!(ledgers(13), [10, 12]);
        assert_eq!(ledgers(-2), [-2]);
        assert_eq!(ledgers(-5), [-2, -4]);
    }

    #[test]
    fn dynamics_print_where_the_beat_level_changes() {
        // two beats of eighths: mf, then ff; a loud note inside a beat changes nothing
        let mut events = eighths(&[0.0, 2.0, 4.0, 5.0, 7.0]);
        for (event, amplitude) in events.iter_mut().zip([0.66, 0.72, 0.95, 0.94, 0.93]) {
            event.amplitude = amplitude;
        }
        let score = Score::new(&events, Domain::Time);
        let letters = |glyph| {
            score
                .items
                .iter()
                .filter(|item| matches!(item, Item::Glyph { glyph: g, .. } if *g == glyph))
                .count()
        };
        // mf, then ff
        assert_eq!(letters(Glyph::Mezzo), 1);
        assert_eq!(letters(Glyph::Forte), 3);
        assert_eq!(dynamic(0.2), "pp");
        assert_eq!(dynamic(0.95), "ff");
    }

    #[test]
    fn chords_share_a_stem() {
        let chord = vec![
            event(0.0, 0.5, 0.0),
            event(0.0, 0.5, 4.0),
            event(0.0, 0.5, 7.0),
        ];
        let score = Score::new(&chord, Domain::Time);
        let stems = score
            .items
            .iter()
            .filter(|item| matches!(item, Item::Bar { height, .. } if *height > BEAM))
            .count();
        assert_eq!(stems, 1);
        assert_eq!(score.notes.len(), 3);
    }

    #[test]
    fn stacked_thirds_drop_their_shared_row() {
        // quarter notes E4 and G4: a third apart
        let score = Score::new(&[event(0.0, 0.5, 4.0), event(0.0, 0.5, 7.0)], Domain::Time);
        let trims: Vec<Trim> = score
            .items
            .iter()
            .filter_map(|item| match item {
                Item::Glyph {
                    glyph: Glyph::NoteheadBlack,
                    trim,
                    ..
                } => Some(*trim),
                _ => None,
            })
            .collect();
        assert!(trims.iter().any(|trim| trim.top));
        assert!(trims.iter().any(|trim| trim.bottom));
    }

    #[test]
    fn beams_keep_off_staff_lines() {
        let score = Score::new(&eighths(&[16.0, 17.0]), Domain::Time);
        let staff = score.staves()[0];
        for item in &score.items {
            if let Item::Bar {
                y, height: BEAM, ..
            } = item
            {
                assert!(!staff.is_line(*y) && !staff.is_line(y + 1));
            }
        }
    }

    #[test]
    fn everything_sits_inside_the_height() {
        let score = Score::new(&eighths(&[-5.0, 0.0, 24.0, 12.0]), Domain::Time);
        for (_, y) in pixels(&score) {
            assert!(y >= 0 && y < score.height(), "row {y} is outside");
        }
    }

    #[test]
    fn hovering_finds_the_note() {
        let events = eighths(&[0.0, 4.0]);
        let score = Score::new(&events, Domain::Time);
        let axis = axis();
        let note = score.notes.iter().find(|note| note.event == 1).unwrap();
        let (x, y, width, height) = note.bounds(&axis);
        let found = score.note_at(&axis, x + width / 2, y + height / 2).unwrap();
        assert_eq!(found.event, 1);
        assert_eq!(found.name, "E4");
        assert!(score.note_at(&axis, x + 500, y).is_none());
    }

    #[test]
    fn runs_are_clipped() {
        let score = Score::new(&eighths(&[0.0, 2.0, 4.0]), Domain::Time);
        for run in score.runs(&axis(), 60, 80) {
            assert!(run.x >= 60 && run.x + run.length <= 80);
        }
    }
}
