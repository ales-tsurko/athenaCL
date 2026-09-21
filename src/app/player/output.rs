//! One device stream for the synthesizer and decoded audio files.

use std::{
    fmt,
    num::NonZero,
    path::PathBuf,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    time::Duration,
};

use cpal::{
    traits::{DeviceTrait, HostTrait, StreamTrait},
    ErrorKind, SupportedStreamConfig,
};
use midi_player::{Player, PlayerController, PositionObserver, Settings};
use rodio::mixer::{self, Mixer, MixerSource};

use crate::app::player::{events::Events, gain::Gain};

/// Device resources are replaced as a unit, so MIDI and audio cannot use different outputs.
pub(crate) struct AudioOutput {
    // Drop the stream before the control handles it consumes.
    stream: Option<cpal::Stream>,
    pub(crate) midi: PlayerController,
    pub(crate) mixer: Mixer,
    pub(crate) device: DeviceKey,
    pub(crate) needs_poll: bool,
    pub(crate) prepared_midi: Option<MidiResume>,
    midi_audible: Arc<AtomicBool>,
    gain: Gain,
}

impl AudioOutput {
    pub(crate) fn open(
        sf: &str,
        events: Events,
        generation: u64,
        resume: Option<MidiResume>,
        follow: Option<PositionObserver>,
    ) -> Result<Self, OutputError> {
        // A missing remembered font must fall back even when no output device is connected.
        std::fs::File::open(sf).map_err(|error| OutputError::Synthesizer(error.to_string()))?;
        let device = OutputDevice::current()?;
        let (mut output, mut renderer) = Self::new(sf, device.key.clone())?;
        // Loading a large SoundFont can outlast another device change. Do not pin a stream to a
        // device that stopped being the default while the font was loading.
        device.ensure_current(&events, generation)?;
        renderer.follow = follow;
        output.restore_midi(&mut renderer, resume, || !events.is_current(generation))?;
        device.connect(output, renderer, events, generation)
    }

    /// Build the shared render state independently of the physical stream.
    fn new(sf: &str, device: DeviceKey) -> Result<(Self, Renderer), OutputError> {
        let channels = NonZero::new(device.channels).ok_or(OutputError::InvalidFormat)?;
        let rate = NonZero::new(device.rate).ok_or(OutputError::InvalidFormat)?;
        let settings = Settings::builder().sample_rate(rate.get()).build();
        let (player, midi) = Player::new(sf, settings)
            .map_err(|error| OutputError::Synthesizer(error.to_string()))?;
        let (mixer, source) = mixer::mixer(channels, rate);
        let midi_audible = Arc::new(AtomicBool::new(false));
        let gain = Gain::default();
        let renderer = Renderer::new(player, source, midi_audible.clone(), gain.clone());
        Ok((
            Self {
                stream: None,
                midi,
                mixer,
                device,
                needs_poll: false,
                prepared_midi: None,
                midi_audible,
                gain,
            },
            renderer,
        ))
    }

    /// Restore the transport snapshot, tolerating stale files only for idle MIDI tracks.
    pub(crate) fn restore_midi(
        &mut self,
        renderer: &mut Renderer,
        resume: Option<MidiResume>,
        cancelled: impl Fn() -> bool,
    ) -> Result<(), OutputError> {
        let Some(snapshot) = resume else {
            return Ok(());
        };
        match renderer.prepare_midi(&mut self.midi, &snapshot, cancelled) {
            Ok(()) => self.prepared_midi = Some(snapshot),
            Err(error) if snapshot.playing || matches!(error, OutputError::Changed) => {
                return Err(error);
            }
            Err(_) => {
                // An idle MIDI file may have been deleted or edited. It must not prevent
                // reconnecting audio files; playing it later reports its own file error.
                self.midi.stop();
            }
        }
        Ok(())
    }

    pub(crate) fn play_midi(&mut self) {
        self.midi.play();
        self.midi_audible.store(true, Ordering::Relaxed);
    }

    pub(crate) fn set_volume(&self, volume: f32) {
        self.gain.set(volume);
    }

    pub(crate) fn pause_midi(&mut self) {
        self.midi_audible.store(false, Ordering::Relaxed);
        self.midi.stop();
    }

    /// Start only after the UI accepts this output, so discarded opens never make sound.
    pub(crate) fn start(&self) -> Result<(), OutputError> {
        if let Some(stream) = &self.stream {
            stream.play()?;
        }
        Ok(())
    }

    /// Freeze the render clock before saving its position and destroying the stream.
    pub(crate) fn pause(&mut self) {
        if let Some(stream) = &self.stream {
            // An unplugged device can reject pause; dropping its stream still stops it.
            drop(stream.pause());
        }
        self.pause_midi();
    }

    #[cfg(test)]
    pub(crate) fn headless(sf: &str, sample_rate: u32) -> (Self, Renderer) {
        Self::new(
            sf,
            DeviceKey {
                id: "test".into(),
                rate: sample_rate,
                channels: 2,
                format: cpal::SampleFormat::F32,
            },
        )
        .expect("valid test soundfont and format")
    }
}

/// The selected physical output and its format, validated around slow preparation work.
struct OutputDevice {
    device: cpal::Device,
    config: SupportedStreamConfig,
    key: DeviceKey,
    needs_poll: bool,
}

impl OutputDevice {
    fn current() -> Result<Self, OutputError> {
        let host = cpal::default_host();
        let device = host.default_output_device().ok_or(OutputError::NoDevice)?;
        let config = device.default_output_config()?;
        let key = DeviceKey::new(&device, &config)?;
        Ok(Self {
            device,
            config,
            key,
            needs_poll: needs_poll(host.id()),
        })
    }

    fn ensure_current(&self, events: &Events, generation: u64) -> Result<(), OutputError> {
        if !events.is_current(generation) || DeviceKey::current()? != self.key {
            return Err(OutputError::Changed);
        }
        Ok(())
    }

    fn connect(
        self,
        mut output: AudioOutput,
        renderer: Renderer,
        events: Events,
        generation: u64,
    ) -> Result<AudioOutput, OutputError> {
        output.stream =
            Some(renderer.open(&self.device, &self.config, events.clone(), generation)?);
        self.ensure_current(&events, generation)?;
        output.needs_poll = self.needs_poll;
        Ok(output)
    }
}

/// The MIDI state to reconstruct while opening a fresh synthesizer.
#[derive(Debug, Clone, PartialEq)]
pub(crate) struct MidiResume {
    pub(crate) path: PathBuf,
    pub(crate) position: f64,
    pub(crate) tempo: u16,
    pub(crate) playing: bool,
}

/// The concrete device and format, including rates that change without a new device ID.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct DeviceKey {
    id: String,
    rate: u32,
    channels: u16,
    format: cpal::SampleFormat,
}

impl DeviceKey {
    fn new(device: &cpal::Device, config: &SupportedStreamConfig) -> Result<Self, OutputError> {
        Ok(Self {
            id: device.id()?.to_string(),
            rate: config.sample_rate(),
            channels: config.channels(),
            format: config.sample_format(),
        })
    }

    pub(crate) fn current() -> Result<Self, OutputError> {
        let device = cpal::default_host()
            .default_output_device()
            .ok_or(OutputError::NoDevice)?;
        Self::new(&device, &device.default_output_config()?)
    }
}

/// A clonable message payload that transfers ownership of a completed background open once.
#[derive(Clone)]
pub struct Opened(Arc<Mutex<Option<Result<AudioOutput, OutputError>>>>);

impl Opened {
    pub(crate) fn new(result: Result<AudioOutput, OutputError>) -> Self {
        Self(Arc::new(Mutex::new(Some(result))))
    }

    pub(crate) fn take(&self) -> Option<Result<AudioOutput, OutputError>> {
        self.0
            .lock()
            .expect("the output handoff does not run fallible code")
            .take()
    }
}

impl fmt::Debug for Opened {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Opened").finish_non_exhaustive()
    }
}

/// Fixed scratch buffers avoid allocating when the device changes its callback size.
pub(crate) struct Renderer {
    player: Player,
    audio: MixerSource,
    left: [f32; 256],
    right: [f32; 256],
    midi_audible: Arc<AtomicBool>,
    gain: Gain,
    follow: Option<PositionObserver>,
}

impl Renderer {
    fn new(player: Player, audio: MixerSource, midi_audible: Arc<AtomicBool>, gain: Gain) -> Self {
        Self {
            player,
            audio,
            left: [0.0; 256],
            right: [0.0; 256],
            midi_audible,
            gain,
            follow: None,
        }
    }

    /// Replay silently off the audio thread to retain programs, controllers and held notes. A
    /// direct seek on a fresh midi-player skips those earlier MIDI events.
    #[expect(
        clippy::cast_sign_loss,
        reason = "the normalized position is clamped to 0..=1"
    )]
    pub(crate) fn prepare_midi(
        &mut self,
        controller: &mut PlayerController,
        resume: &MidiResume,
        cancelled: impl Fn() -> bool,
    ) -> Result<(), OutputError> {
        controller
            .set_file(Some(&resume.path))
            .map_err(|error| OutputError::MidiFile(error.to_string()))?;
        let original_tempo = controller.tempo().unwrap_or(120.0);
        controller.set_tempo(f32::from(resume.tempo));
        let duration = controller
            .duration()
            .mul_f64(f64::from(original_tempo) / f64::from(resume.tempo.max(1)));
        let rate = u128::from(self.player.settings().sample_rate);
        // Include per-tick rounding and a second of slack; malformed zero-length pulses must not
        // leave the reconstruction spinning forever without advancing.
        let budget = duration.as_nanos() * rate / 1_000_000_000
            + u128::from(controller.total_ticks())
            + rate;
        let mut rendered = 0;
        let mut target =
            (controller.total_ticks() as f64 * resume.position.clamp(0.0, 1.0)).round() as u64;
        if let Some(follow) = &self.follow {
            target = follow.ticks().min(controller.total_ticks());
        }
        controller.play();
        while controller.position_ticks() < target && controller.is_playing() {
            if cancelled() {
                return Err(OutputError::Changed);
            }
            if rendered >= budget {
                return Err(OutputError::MidiFile(
                    "the playhead stopped advancing".into(),
                ));
            }
            self.player.render(&mut self.left, &mut self.right);
            rendered += self.left.len() as u128;
            if let Some(follow) = &self.follow {
                target = follow.ticks().min(controller.total_ticks());
            }
        }
        controller.set_position_ticks(target);
        if !resume.playing {
            controller.stop();
        }
        self.follow = None;
        Ok(())
    }

    fn open(
        self,
        device: &cpal::Device,
        config: &SupportedStreamConfig,
        events: Events,
        generation: u64,
    ) -> Result<cpal::Stream, OutputError> {
        macro_rules! open {
            ($($format:ident => $sample:ty),+ $(,)?) => {
                match config.sample_format() {
                    $(cpal::SampleFormat::$format => self.open_typed::<$sample>(
                        device, config, events, generation),)+
                    _ => Err(OutputError::InvalidFormat),
                }
            };
        }
        open!(I8 => i8, I16 => i16, I24 => cpal::I24, I32 => i32, I64 => i64,
            U8 => u8, U16 => u16, U24 => cpal::U24, U32 => u32, U64 => u64,
            F32 => f32, F64 => f64)
    }

    fn open_typed<T>(
        mut self,
        device: &cpal::Device,
        config: &SupportedStreamConfig,
        events: Events,
        generation: u64,
    ) -> Result<cpal::Stream, OutputError>
    where
        T: cpal::SizedSample + cpal::FromSample<f32>,
    {
        let channels = usize::from(config.channels());
        let mut config = config.config();
        config.buffer_size = cpal::BufferSize::Default;
        Ok(device.build_output_stream(
            config,
            move |data: &mut [T], _| self.render(data, channels),
            move |error| events.on_error(generation, error),
            Some(Duration::from_secs(2)),
        )?)
    }

    pub(crate) fn render<T>(&mut self, data: &mut [T], channels: usize)
    where
        T: cpal::SizedSample + cpal::FromSample<f32>,
    {
        data.fill(T::EQUILIBRIUM);
        for block in data.chunks_mut(self.left.len() * channels.max(1)) {
            let frames = block.len() / channels.max(1);
            let (Some(left), Some(right)) =
                (self.left.get_mut(..frames), self.right.get_mut(..frames))
            else {
                continue;
            };
            left.fill(0.0);
            right.fill(0.0);
            self.player.render(left, right);
            // Reconstructed held notes and release tails stay silent while the transport is paused,
            // including the gap between stream acceptance and transport resume.
            let audible = self.midi_audible.load(Ordering::Relaxed);
            let gain = self.gain.get();
            for (frame, (left, right)) in block
                .chunks_exact_mut(channels.max(1))
                .zip(left.iter().zip(right.iter()))
            {
                for (channel, sample) in frame.iter_mut().enumerate() {
                    let midi = match (audible, channels, channel) {
                        (true, 1, _) => (left + right) * 0.5,
                        (true, _, 0) => *left,
                        (true, _, 1) => *right,
                        _ => 0.0,
                    };
                    *sample = T::from_sample(
                        ((midi + self.audio.next().unwrap_or(0.0)) * gain).clamp(-1.0, 1.0),
                    );
                }
            }
        }
    }
}

/// Native notifications cover CoreAudio, WASAPI and PipeWire. CPAL's other backends need a slow
/// device check, kept off the UI and render threads.
fn needs_poll(host: cpal::HostId) -> bool {
    let notification_hosts = [
        #[cfg(target_os = "macos")]
        cpal::HostId::CoreAudio,
        #[cfg(target_os = "windows")]
        cpal::HostId::Wasapi,
        #[cfg(target_os = "linux")]
        cpal::HostId::PipeWire,
    ];
    !notification_hosts.contains(&host)
}

#[derive(Debug, thiserror::Error)]
pub(crate) enum OutputError {
    #[error("No audio output is available")]
    NoDevice,
    #[error("Audio output: {0}")]
    Device(#[from] cpal::Error),
    #[error("Cannot initialize the MIDI synthesizer: {0}")]
    Synthesizer(String),
    #[error("Cannot resume MIDI playback: {0}")]
    MidiFile(String),
    #[error("The audio output changed while opening it")]
    Changed,
    #[error("The audio output has an unsupported format")]
    InvalidFormat,
}

impl OutputError {
    pub(crate) fn retryable(&self) -> bool {
        match self {
            Self::NoDevice | Self::Changed => true,
            Self::Device(error) => matches!(
                error.kind(),
                ErrorKind::DeviceBusy
                    | ErrorKind::DeviceNotAvailable
                    | ErrorKind::HostUnavailable
                    | ErrorKind::StreamInvalidated
                    | ErrorKind::DeviceChanged
            ),
            _ => false,
        }
    }
}
