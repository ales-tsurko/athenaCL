//! CPAL notifications forwarded to the UI without polling the render thread.

use std::{
    hash::{Hash, Hasher},
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc,
    },
};

use async_channel::{Receiver, Sender};
use iced::{futures::SinkExt, stream, Subscription};

use crate::app::player::Message;

static NEXT_ID: AtomicU64 = AtomicU64::new(0);

#[derive(Clone)]
pub(crate) struct Events {
    id: u64,
    sender: Sender<u64>,
    receiver: Receiver<u64>,
    generation: Arc<AtomicU64>,
}

impl Events {
    pub(crate) fn new() -> Self {
        let (sender, receiver) = async_channel::unbounded();
        Self {
            id: NEXT_ID.fetch_add(1, Ordering::Relaxed),
            sender,
            receiver,
            generation: Arc::new(AtomicU64::new(0)),
        }
    }

    pub(crate) fn set_generation(&self, generation: u64) {
        self.generation.store(generation, Ordering::Relaxed);
    }

    pub(crate) fn is_current(&self, generation: u64) -> bool {
        self.generation.load(Ordering::Relaxed) == generation
    }

    pub(crate) fn changed(&self, generation: u64) {
        // A closed receiver means the application has exited.
        if self.sender.try_send(generation).is_err() {
            self.sender.close();
        }
    }

    pub(crate) fn on_error(&self, generation: u64, error: cpal::Error) {
        if matches!(
            error.kind(),
            cpal::ErrorKind::DeviceChanged
                | cpal::ErrorKind::StreamInvalidated
                | cpal::ErrorKind::DeviceNotAvailable
                | cpal::ErrorKind::HostUnavailable
        ) {
            self.changed(generation);
        } else {
            // An underrun or denied realtime priority does not invalidate the output.
            eprintln!("Audio output: {error}");
        }
    }

    pub(crate) fn subscription(&self) -> Subscription<Message> {
        Subscription::run_with(self.clone(), |events| {
            let receiver = events.receiver.clone();
            stream::channel(1, async move |mut output| {
                while let Ok(generation) = receiver.recv().await {
                    if output
                        .send(Message::OutputChanged(generation))
                        .await
                        .is_err()
                    {
                        break;
                    }
                }
            })
        })
    }
}

impl Hash for Events {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.id.hash(state);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn route_changes_wake_the_player_but_underruns_do_not_reopen_it() {
        let events = Events::new();
        for kind in [
            cpal::ErrorKind::DeviceChanged,
            cpal::ErrorKind::StreamInvalidated,
            cpal::ErrorKind::DeviceNotAvailable,
            cpal::ErrorKind::HostUnavailable,
        ] {
            events.on_error(42, kind.into());
            assert_eq!(events.receiver.try_recv().expect("route change"), 42);
        }
        for kind in [cpal::ErrorKind::Xrun, cpal::ErrorKind::RealtimeDenied] {
            events.on_error(42, kind.into());
            assert!(events.receiver.is_empty());
        }
    }
}
