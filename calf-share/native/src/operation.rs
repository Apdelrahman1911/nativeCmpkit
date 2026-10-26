use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, AtomicI32, Ordering};
use std::sync::Arc;

pub(crate) const PENDING: i32 = -1;
pub(crate) const SUCCESS: i32 = 0;
pub(crate) const DISMISSED: i32 = 1;
pub(crate) const UNAVAILABLE: i32 = 2;
pub(crate) const FAILED: i32 = 3;

pub(crate) struct Completion {
    result: AtomicI32,
    cancelled: AtomicBool,
}
impl Completion {
    fn new() -> Self {
        Self {
            result: AtomicI32::new(PENDING),
            cancelled: AtomicBool::new(false),
        }
    }
    pub(crate) fn cancelled(&self) -> bool {
        self.cancelled.load(Ordering::Acquire)
    }
}

/// IDs, not borrowed Java pointers/raw Arcs, cross the asynchronous UI boundary. Registry methods
/// run under one mutex; UI objects are stored separately and destroyed only on the AppKit thread.
#[derive(Default)]
pub(crate) struct Registry {
    next: i64,
    active: Option<i64>,
    entries: HashMap<i64, Arc<Completion>>,
}
impl Registry {
    pub(crate) fn begin(&mut self) -> Option<(i64, Arc<Completion>)> {
        if self.active.is_some() || self.entries.len() >= 64 {
            return None;
        }
        self.next = self.next.checked_add(1)?;
        let state = Arc::new(Completion::new());
        self.entries.insert(self.next, state.clone());
        self.active = Some(self.next);
        Some((self.next, state))
    }
    /// Invoke only after native owners have been detached. Duplicate/late callbacks cannot replace
    /// an already-final result or clear a newer operation's active identity.
    pub(crate) fn finish(&mut self, id: i64, result: i32) {
        if let Some(state) = self.entries.get(&id) {
            let _ =
                state
                    .result
                    .compare_exchange(PENDING, result, Ordering::AcqRel, Ordering::Acquire);
        }
        if self.active == Some(id) {
            self.active = None;
        }
    }
    pub(crate) fn take(&mut self, id: i64) -> i32 {
        let result = self
            .entries
            .get(&id)
            .map(|state| state.result.load(Ordering::Acquire))
            .unwrap_or(UNAVAILABLE);
        if result != PENDING {
            self.entries.remove(&id);
        }
        result
    }
    /// Keep the single-flight slot until main-thread cleanup acknowledges finish(id).
    pub(crate) fn cancel(&mut self, id: i64) {
        if let Some(state) = self.entries.remove(&id) {
            state.cancelled.store(true, Ordering::Release);
        }
    }
    pub(crate) fn len(&self) -> usize {
        self.entries.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn result_is_pending_then_consumed_once() {
        let mut registry = Registry::default();
        let (id, _) = registry.begin().unwrap();
        assert_eq!(registry.take(id), PENDING);
        registry.finish(id, SUCCESS);
        assert_eq!(registry.take(id), SUCCESS);
        assert_eq!(registry.take(id), UNAVAILABLE);
    }
    #[test]
    fn single_flight_rejects_overlapping_requests() {
        let mut registry = Registry::default();
        let (id, _) = registry.begin().unwrap();
        assert!(registry.begin().is_none());
        registry.finish(id, DISMISSED);
        assert!(registry.begin().is_some());
    }
    #[test]
    fn cancellation_releases_registry_reference_but_waits_for_ui_cleanup() {
        let mut registry = Registry::default();
        let (id, state) = registry.begin().unwrap();
        assert_eq!(Arc::strong_count(&state), 2);
        registry.cancel(id);
        assert!(state.cancelled());
        assert_eq!(Arc::strong_count(&state), 1);
        assert!(registry.begin().is_none());
        registry.finish(id, DISMISSED);
        assert!(registry.begin().is_some());
    }
    #[test]
    fn late_completion_cannot_clear_a_new_owner() {
        let mut registry = Registry::default();
        let (old, _) = registry.begin().unwrap();
        registry.finish(old, SUCCESS);
        let (new, _) = registry.begin().unwrap();
        registry.finish(old, DISMISSED);
        assert!(registry.begin().is_none());
        assert_eq!(registry.take(old), SUCCESS);
        registry.finish(new, SUCCESS);
        assert!(registry.begin().is_some());
    }
    #[test]
    fn completion_and_cancel_drop_each_arc_exactly_once() {
        let mut registry = Registry::default();
        for i in 0..10_000 {
            let (id, state) = registry.begin().unwrap();
            if i % 2 == 0 {
                registry.cancel(id);
            }
            registry.finish(id, DISMISSED);
            registry.take(id);
            assert_eq!(Arc::strong_count(&state), 1);
            assert_eq!(registry.len(), 0);
        }
    }
    #[test]
    fn unconsumed_results_have_a_bounded_registry() {
        let mut registry = Registry::default();
        for _ in 0..64 {
            let (id, _) = registry.begin().unwrap();
            registry.finish(id, SUCCESS);
        }
        assert!(registry.begin().is_none());
        assert_eq!(registry.len(), 64);
    }
}
