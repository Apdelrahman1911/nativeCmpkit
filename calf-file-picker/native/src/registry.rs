//! Opaque, monotonically allocated IDs. A show operation leases an Arc before a close can remove it.
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

pub(crate) struct Registry<T> {
    state: Mutex<State<T>>,
}

struct State<T> {
    next_id: i64,
    entries: HashMap<i64, Arc<T>>,
}

impl<T> Registry<T> {
    pub(crate) fn new() -> Self {
        Self {
            state: Mutex::new(State {
                next_id: 1,
                entries: HashMap::new(),
            }),
        }
    }

    pub(crate) fn insert(&self, value: T) -> Result<i64, &'static str> {
        let mut state = self
            .state
            .lock()
            .map_err(|_| "Native dialog registry is poisoned")?;
        let id = state.next_id;
        state.next_id = id
            .checked_add(1)
            .ok_or("Native dialog identifiers exhausted")?;
        state.entries.insert(id, Arc::new(value));
        Ok(id)
    }

    pub(crate) fn lease(&self, id: i64) -> Result<Arc<T>, &'static str> {
        self.state
            .lock()
            .map_err(|_| "Native dialog registry is poisoned")?
            .entries
            .get(&id)
            .cloned()
            .ok_or("Unknown or closed native dialog handle")
    }

    // Closing is idempotent. Existing show leases keep the value alive until show returns.
    pub(crate) fn close(&self, id: i64) -> Result<(), &'static str> {
        let removed = self
            .state
            .lock()
            .map_err(|_| "Native dialog registry is poisoned")?
            .entries
            .remove(&id);
        drop(removed); // Never run a config destructor while holding the registry mutex.
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::Registry;
    use std::sync::{
        atomic::{AtomicUsize, Ordering},
        Arc, Barrier,
    };

    struct Counted(Arc<AtomicUsize>);
    impl Drop for Counted {
        fn drop(&mut self) {
            self.0.fetch_add(1, Ordering::SeqCst);
        }
    }

    #[test]
    fn invalid_ids_and_closed_ids_are_rejected_and_close_is_idempotent() {
        let registry = Registry::new();
        let id = registry.insert("value").unwrap();
        assert!(registry.lease(0).is_err());
        assert!(registry.lease(-1).is_err());
        registry.close(id).unwrap();
        registry.close(id).unwrap();
        assert!(registry.lease(id).is_err());
        assert_ne!(id, registry.insert("new value").unwrap());
    }

    #[test]
    fn closing_during_show_does_not_destroy_its_lease() {
        let registry = Arc::new(Registry::new());
        let drops = Arc::new(AtomicUsize::new(0));
        let id = registry.insert(Counted(drops.clone())).unwrap();
        let acquired = Arc::new(Barrier::new(2));
        let resume = Arc::new(Barrier::new(2));
        let worker = {
            let registry = registry.clone();
            let acquired = acquired.clone();
            let resume = resume.clone();
            std::thread::spawn(move || {
                let lease = registry.lease(id).unwrap();
                acquired.wait();
                resume.wait();
                assert_eq!(lease.0.load(Ordering::SeqCst), 0);
            })
        };
        acquired.wait();
        registry.close(id).unwrap();
        assert_eq!(drops.load(Ordering::SeqCst), 0);
        resume.wait();
        worker.join().unwrap();
        assert_eq!(drops.load(Ordering::SeqCst), 1);
    }

    #[test]
    fn racing_close_and_acquire_returns_either_a_safe_lease_or_an_error() {
        let registry = Arc::new(Registry::new());
        let drops = Arc::new(AtomicUsize::new(0));
        for _ in 0..128 {
            let id = registry.insert(Counted(drops.clone())).unwrap();
            let other = registry.clone();
            let worker = std::thread::spawn(move || other.lease(id));
            registry.close(id).unwrap();
            drop(worker.join().unwrap());
        }
        assert_eq!(drops.load(Ordering::SeqCst), 128);
    }
}
