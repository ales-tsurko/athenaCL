//! A coloured icon raster retained in the widget tree, independent of position and scale.

use std::cell::RefCell;

use iced::{advanced::image, Color};

use crate::app::icons::Icon;

/// The last glyph and foreground colour drawn by this widget.
#[derive(Debug, Default)]
pub(super) struct Cache(RefCell<Option<Raster>>);

impl Cache {
    /// Reuse the same image handle until either the glyph or the actual ink changes.
    pub(super) fn image(&self, icon: Icon, color: Color) -> image::Handle {
        let ink = color.into_rgba8();
        let mut cached = self.0.borrow_mut();
        if let Some(raster) = cached
            .as_ref()
            .filter(|raster| raster.icon == icon && raster.ink == ink)
        {
            return raster.handle.clone();
        }

        let handle = icon.rasterize(ink);
        *cached = Some(Raster {
            icon,
            ink,
            handle: handle.clone(),
        });
        handle
    }
}

/// Decoded pixels and their cache key; no theme names or display-specific variants.
#[derive(Debug)]
struct Raster {
    icon: Icon,
    ink: [u8; 4],
    handle: image::Handle,
}

impl Icon {
    /// Materialize the source mask only on a cache miss. No image codec is involved.
    fn rasterize(self, ink: [u8; 4]) -> image::Handle {
        let rows = self.rows();
        let side = rows.len() as u32;
        let pixels: Vec<u8> = rows
            .iter()
            .flat_map(|row| row.iter())
            .flat_map(|&pixel| if pixel == b'#' { ink } else { [0; 4] })
            .collect();
        image::Handle::from_rgba(side, side, pixels)
    }
}

#[cfg(test)]
mod tests {
    use iced::{advanced::image, Color};

    use crate::app::icons::{cache::Cache, Icon};

    #[test]
    fn repeated_paints_reuse_the_image_and_colour_changes_invalidate_it() {
        let cache = Cache::default();
        let ink = Color::from_rgba8(137, 61, 219, 0.5);
        let original = cache.image(Icon::Metronome, ink);
        for _ in 0..120 {
            assert_eq!(cache.image(Icon::Metronome, ink).id(), original.id());
        }

        let recoloured = cache.image(Icon::Metronome, Color::WHITE);
        assert_ne!(recoloured.id(), original.id());
        assert_eq!(
            cache.image(Icon::Metronome, Color::WHITE).id(),
            recoloured.id()
        );
        assert_ne!(
            cache.image(Icon::Folder, Color::WHITE).id(),
            recoloured.id()
        );

        let (width, height, pixels) = match original {
            image::Handle::Rgba {
                width,
                height,
                pixels,
                ..
            } => Some((width, height, pixels)),
            _ => None,
        }
        .expect("icons contain decoded pixels");
        assert_eq!((width, height), (16, 16));
        let pixels = pixels.as_chunks::<4>().0;
        assert!(pixels.contains(&ink.into_rgba8()));
        assert!(pixels.contains(&[0; 4]));
        assert!(pixels
            .iter()
            .all(|&pixel| pixel == ink.into_rgba8() || pixel == [0; 4]));
    }
}
