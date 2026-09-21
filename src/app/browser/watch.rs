//! A debounced native watcher. Dropping the subscription stops it when the scratch folder changes.

use std::{path::Path, time::Duration};

use iced::{
    futures::{SinkExt, Stream},
    stream, Subscription,
};
use notify::{
    event::{MetadataKind, ModifyKind},
    EventKind, RecursiveMode, Watcher,
};

use crate::app::browser::{Browser, Message};

impl Browser {
    pub(crate) fn subscription(&self) -> Subscription<Message> {
        if self.root.as_os_str().is_empty() {
            return Subscription::none();
        }
        Subscription::run_with((self.root.clone(), self.watch_epoch), |(root, _)| {
            watch(root)
        })
    }
}

fn watch(root: &Path) -> impl Stream<Item = Message> {
    let root = root.to_path_buf();
    stream::channel(1, async move |mut output| {
        let (sender, receiver) = async_channel::bounded(1);
        let callback = move |result: notify::Result<notify::Event>| {
            if let Ok(event) = &result {
                // Scanning and decoding must not trigger another scan on Linux's inotify backend.
                if !changes_files(event.kind) {
                    return;
                }
            }
            // One pending notification is enough to refresh the whole cached tree.
            drop(sender.try_send(result.map(|_| ()).map_err(|error| error.to_string())));
        };
        let watched = notify::recommended_watcher(callback).and_then(|mut watcher| {
            // FSEvents expects the physical path (e.g. /private/var, not the /var symlink).
            let watched_root = root.canonicalize().map_err(notify::Error::io)?;
            watcher.watch(&watched_root, RecursiveMode::Recursive)?;
            Ok(watcher)
        });
        let _watcher = match watched {
            Ok(watcher) => watcher,
            Err(error) => {
                drop(
                    output
                        .send(Message::WatchFailed(root, error.to_string()))
                        .await,
                );
                return;
            }
        };
        while let Ok(result) = receiver.recv().await {
            tokio::time::sleep(Duration::from_millis(300)).await;
            // Drain notifications from the same burst. New events during the scan schedule another.
            let result = receiver.try_recv().unwrap_or(result);
            let message = match result {
                Ok(()) => Message::Changed(root.clone()),
                Err(error) => Message::WatchFailed(root.clone(), error),
            };
            if output.send(message).await.is_err() {
                break;
            }
        }
    })
}

fn changes_files(kind: EventKind) -> bool {
    !matches!(
        kind,
        EventKind::Access(_) | EventKind::Modify(ModifyKind::Metadata(MetadataKind::AccessTime))
    )
}

#[cfg(test)]
mod tests {
    use iced::futures::StreamExt;
    use notify::event::{AccessKind, CreateKind, DataChange, RenameMode};

    use super::*;

    #[test]
    fn reading_files_does_not_trigger_a_refresh_loop() {
        assert!(!changes_files(EventKind::Access(AccessKind::Read)));
        assert!(!changes_files(EventKind::Modify(ModifyKind::Metadata(
            MetadataKind::AccessTime
        ))));
        for kind in [
            EventKind::Create(CreateKind::File),
            EventKind::Modify(ModifyKind::Data(DataChange::Content)),
            EventKind::Modify(ModifyKind::Name(RenameMode::Both)),
        ] {
            assert!(changes_files(kind));
        }
    }

    #[test]
    fn native_watcher_reports_new_files() {
        let dir = tempfile::tempdir().expect("scratch folder");
        let root = dir.path().to_path_buf();
        let runtime = tokio::runtime::Builder::new_current_thread()
            .enable_time()
            .build()
            .expect("timer runtime");
        runtime.block_on(async {
            let mut events = Box::pin(watch(&root));
            let create = async {
                tokio::time::sleep(Duration::from_millis(100)).await;
                std::fs::write(root.join("new.txt"), "new file").expect("new file");
            };
            let receive = tokio::time::timeout(Duration::from_secs(5), events.next());
            let (message, ()) = iced::futures::join!(receive, create);
            assert!(
                matches!(&message, Ok(Some(Message::Changed(changed))) if changed == &root),
                "{message:?}"
            );
        });
    }
}
