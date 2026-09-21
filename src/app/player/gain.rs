//! One gain shared by both render sources and every replacement device stream.

use std::sync::{
    atomic::{AtomicU32, Ordering},
    Arc,
};

#[derive(Clone)]
pub(crate) struct Gain(Arc<AtomicU32>);

impl Default for Gain {
    fn default() -> Self {
        Self(Arc::new(AtomicU32::new(1.0_f32.to_bits())))
    }
}

impl Gain {
    pub(crate) fn set(&self, volume: f32) {
        self.0
            .store(volume.clamp(0.0, 1.0).to_bits(), Ordering::Relaxed);
    }

    pub(crate) fn get(&self) -> f32 {
        f32::from_bits(self.0.load(Ordering::Relaxed))
    }
}
