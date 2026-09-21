//! The manual's screenshots, made the way the app makes its window.
//!
//! Each one runs real commands against a fresh AthenaObject and renders what they put in the log,
//! with the app's own settings, in both looks: `NAME.png` in the light one, which the published
//! manual shows, and `NAME-dark.png`, which the app shows when it is in the dark one. A shot of the
//! log's output is as wide as a picture on a panel in the log, and cut to what it shows, so that
//! the app draws it pixel for pixel. They are written into `doc/src/images`; run
//! `make screenshots` to make them again.

use std::{
    path::{Path, PathBuf},
    time::{Duration, Instant},
};

use iced::{widget::container, Size};

use super::*;

/// One of the manual's screenshots: the commands that make it, and what of theirs it shows.
struct Shot {
    /// The image's name under `doc/src/images`, without its look or extension.
    name: &'static str,
    /// Commands run first, on a fresh AthenaObject: the examples before the shot's own.
    setup: &'static [&'static str],
    /// The shot's own commands, run after them.
    commands: &'static [&'static str],
    /// What the image shows.
    frame: Frame,
}

/// What a screenshot shows.
#[derive(Clone, Copy)]
enum Frame {
    /// The last command's figure, as the log shows it.
    Figure,
    /// The last command's figure, switched to its score.
    Score,
    /// The last command's player.
    Player,
    /// The whole window.
    Window,
}

/// Tutorial 4's Textures as its examples leave them for its first map: two percussion Textures, the
/// second starting at 5 seconds, both with random amplitudes.
const TUTORIAL_4: &[&str] = &[
    "tmo linegroove",
    "emo mp",
    "tin a1 64",
    "tin b1 62",
    "tie t 5,20",
    "tee a ru,.6,1",
];

/// Tutorial 4's later examples, up to its Texture map: b1's panning and the two rhythms, the tempo
/// of both, and both moved to Csound instrument 80.
const TUTORIAL_4_EDITS: &[&str] = &[
    "tie n wpd,e,15,.25,2.5,0,.5",
    "tie r l,((4,1,1),(4,1,1),(4,2,1),(4,3,1),(4,5,1),(4,3,1)),rw",
    "tio a1",
    "tie r mp,a{8,1,1}b{4,3,1}c{4,2,1}d{4,5,1}:{a=1|b=3|c=4|d=7},(c,0)",
    "tee b wpu,t,20,0,2,120,300",
    "emo cn",
    "tie i 80",
    "tio b1",
    "tie i 80",
    "timap",
];

/// Every screenshot, each beside the example of the manual whose commands made it.
const SHOTS: &[Shot] = &[
    Shot {
        name: "window",
        setup: &[],
        commands: &[],
        frame: Frame::Window,
    },
    // Configuring the User Environment: producing a graphical diagram with TPmap
    Shot {
        name: "tpmap-uniform",
        setup: &[],
        commands: &["tpmap 100 ru"],
        frame: Frame::Figure,
    },
    // Creating an EventList: hearing it with ELh
    Shot {
        name: "player",
        setup: &[],
        commands: &["emo m", "tin a 0", "eln", "elh"],
        frame: Frame::Player,
    },
    // Editing TextureInstance Attributes: a graphical display of Texture position
    Shot {
        name: "temap-position",
        setup: TUTORIAL_4,
        commands: &["temap"],
        frame: Frame::Figure,
    },
    // Muting Textures: muting a Texture with TImute
    Shot {
        name: "temap-muted",
        setup: TUTORIAL_4,
        commands: &["timute", "temap"],
        frame: Frame::Figure,
    },
    // Viewing and Searching ParameterObjects: the two ParameterObject maps with TPmap, the first
    // entered there a question at a time
    Shot {
        name: "tpmap-wave",
        setup: &[],
        commands: &["tpmap 120 wpd,e,30,0,2"],
        frame: Frame::Figure,
    },
    Shot {
        name: "tpmap-noise",
        setup: &[],
        commands: &["tpmap 120 n,50,(c,2),0,1"],
        frame: Frame::Figure,
    },
    // Displaying Texture Parameter Values: viewing a Texture with TImap, as graphs and as a score
    Shot {
        name: "timap",
        setup: TUTORIAL_4,
        commands: TUTORIAL_4_EDITS,
        frame: Frame::Figure,
    },
    Shot {
        name: "timap-score",
        setup: TUTORIAL_4,
        commands: TUTORIAL_4_EDITS,
        frame: Frame::Score,
    },
    // Creating and Editing Clones: viewing Textures and Clones with TEmap, after the chapter's
    // three clones
    Shot {
        name: "temap-clones",
        setup: &[],
        commands: &[
            "emo m",
            "tin a1 0",
            "tie t 0,6",
            "tie r cs,(wpd,e,16,2,0,.6,.02)",
            "tie f wpd,e,16,2,0,12,-24",
            "tcn w1",
            "tcn w2",
            "tce t fma, l, (ws, e, 8, 0, 1, 2)",
            "tce f fa,(c,-7)",
            "tco w1",
            "tcn w3",
            "tce t fma,l,(c,2.5)",
            "tce f fa,(c,7)",
            "temap",
        ],
        frame: Frame::Figure,
    },
];

/// The tallest a shot of the log's output gets before it is cut to what it shows.
const TALL: f32 = 1200.0;
/// The page around what a shot of the log's output shows, so that it does not run into the shot's
/// edges.
const MARGIN: u16 = 12;
/// How long a command may take to answer before the shot gives up on it.
const PATIENCE: Duration = Duration::from_secs(60);

#[test]
#[ignore = "writes the manual's screenshots into doc/src/images: run `make screenshots`"]
fn manual_screenshots() {
    let images = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("doc/src/images");
    std::fs::create_dir_all(&images).expect("the images directory should be made");
    for shot in SHOTS {
        let mut state = session(shot.setup.iter().chain(shot.commands));
        for mode in [Mode::Light, Mode::Dark] {
            let name = match mode {
                Mode::Light => format!("{}.png", shot.name),
                Mode::Dark => format!("{}-dark.png", shot.name),
            };
            state.mode = mode;
            render(&mut state, shot.frame, &images.join(name));
        }
    }
}

#[test]
fn a_shot_is_as_wide_as_a_picture_in_the_log_and_cut_to_what_it_shows() {
    let dir = std::env::temp_dir()
        .join("athenacl-tests")
        .join(std::process::id().to_string());
    std::fs::create_dir_all(&dir).expect("the test directory should be made");
    let path = dir.join("shot.png");
    let mut state = session(&["tpmap 10 ru"]);
    render(&mut state, Frame::Figure, &path);

    let shot = image::open(&path).expect("the shot reads back");
    // the snapshot is at twice the size
    let (width, height) = (f64::from(shot.width()), f64::from(shot.height()));
    assert!(
        (width - f64::from(manual::picture_width(OUTPUT_WIDTH)) * 2.0).abs() < 1.0,
        "{width}"
    );
    assert!(0.0 < height && height < f64::from(TALL) * 2.0, "{height}");
}

/// The app after running `commands` on a fresh AthenaObject.
fn session<'a>(commands: impl IntoIterator<Item = &'a &'a str>) -> State {
    let mut state = fresh_state();
    run(&mut state, "aorm confirm");
    state.output.clear();
    for command in commands {
        run(&mut state, command);
    }
    state
}

/// The app as it opens, with nothing made yet.
fn fresh_state() -> State {
    State {
        answer: String::new(),
        history: History::default(),
        suggestions: Suggestions::default(),
        output: Vec::new(),
        question: None,
        player_state: GlobalPlayerState::headless(),
        scratch_dir: String::new(),
        input_id: "input".to_owned(),
        path_lib: Vec::new(),
        texture_lib: Vec::new(),
        active_path: String::new(),
        active_texture: String::new(),
        mode: Mode::Light,
        figure_view: View::Plot,
        tempo: "120".to_owned(),
        reveal: None,
    }
}

/// Enter `command`, and give the app everything the interpreter says until it is done with it.
fn run(state: &mut State, command: &str) {
    drop(update(
        state,
        Message::Interpreter(interpreter::Message::SendCmd(command.to_owned())),
    ));
    let receiver = &interpreter::INTERPRETER_WORKER.gui_receiver;
    let deadline = Instant::now() + PATIENCE;
    loop {
        let Ok(message) = receiver.try_recv() else {
            assert!(
                Instant::now() < deadline,
                "{command:?} did not answer in {PATIENCE:?}"
            );
            std::thread::sleep(Duration::from_millis(20));
            continue;
        };
        if let interpreter::Message::Error(error) | interpreter::Message::PythonError(error) =
            &message
        {
            panic!("{command:?} failed: {error}");
        }
        // nobody is there to answer, so a shot gives its commands everything as arguments
        if let interpreter::Message::Ask { prompt, .. } = &message {
            panic!("{command:?} asks {prompt:?}: give it the answer as an argument");
        }
        // a command is done once it has printed its result
        let done = matches!(message, interpreter::Message::Post(_));
        drop(update(state, Message::Interpreter(message)));
        if done {
            break;
        }
    }
}

/// Draw `frame` of `state`, in its look, into the PNG at `path`.
fn render(state: &mut State, frame: Frame, path: &Path) {
    let colors = state.mode.colors();
    let theme = state.mode.theme();
    let window = matches!(frame, Frame::Window);
    if matches!(frame, Frame::Score) {
        let index = last(state, |output| matches!(output, Output::Figure(_)));
        drop(update(state, Message::FigureView(index, View::Score)));
    }

    let size = if window {
        Size::from(MIN_WINDOW_SIZE)
    } else {
        Size::new(manual::picture_width(OUTPUT_WIDTH), TALL)
    };
    let element: Element<'_, Message> = if window {
        view(state)
    } else {
        let index = last(state, |output| match frame {
            Frame::Player => matches!(output, Output::Player(_)),
            _ => matches!(output, Output::Figure(_)),
        });
        let output = state.output.get(index).expect("the index is the output's");
        container(view_output(index, output, state, colors, colors.figure()))
            .padding(MARGIN)
            .width(Length::Fill)
            .style(Colors::fill(colors.paper))
            .into()
    };

    let mut simulator = iced_test::Simulator::with_size(settings(), size, element);
    let snapshot = simulator.snapshot(&theme).expect("the shot renders");
    let mut image = crate::app::snapshot::pixels(&snapshot);
    if !window {
        image = crop_to_content(&image, colors.paper);
    }
    image.save(path).expect("the shot is saved");
}

/// Where the last output that `wanted` picks is in the log.
fn last(state: &State, wanted: impl Fn(&Output) -> bool) -> usize {
    state
        .output
        .iter()
        .rposition(wanted)
        .expect("the commands put what the shot shows in the log")
}

/// The rows of `image` from the first to the last that show something on `paper`, and its margin
/// of `paper` above and below them.
fn crop_to_content(image: &image::RgbaImage, paper: iced::Color) -> image::RgbaImage {
    let [red, green, blue, _] = paper.into_rgba8();
    let shows = |y: &u32| {
        (0..image.width()).any(|x| {
            let [r, g, b, _] = image.get_pixel(x, *y).0;
            r.abs_diff(red) > 3 || g.abs_diff(green) > 3 || b.abs_diff(blue) > 3
        })
    };
    // the snapshot is at twice the size, and so is the margin
    let margin = u32::from(MARGIN) * 2;
    let top = (0..image.height())
        .find(shows)
        .unwrap_or(0)
        .saturating_sub(margin);
    let bottom = (0..image.height()).rev().find(shows).unwrap_or(top);
    let bottom = (bottom + 1 + margin).min(image.height());
    image::imageops::crop_imm(image, 0, top, image.width(), bottom - top).to_image()
}
