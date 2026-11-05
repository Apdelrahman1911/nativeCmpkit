// Added for NativeCmpKit: bounded ownership recovery, not a native-release executor.
// A record holds an actual retained resource; a slot/ticket is never ownership itself.
use std::sync::{Mutex, MutexGuard};

/// Finite storage is prepared before any native retain. No record is evicted.
pub(super) struct ReleaseSlots<T, const N: usize> {
    slots: [Mutex<Slot<T>>; N],
}

enum Slot<T> {
    Vacant,
    Reserved,
    Owned,
    KnownUnscheduled { vm_key: usize, value: T },
    InFlight,
    Requested,
    // Deliberately no retry/dereference accessor. Underscore fields still OWN T.
    Unknown { _vm_key: usize, _owned: T },
}

#[derive(Default, Debug, Eq, PartialEq)]
pub(super) struct Counts {
    pub(super) vacant: usize,
    pub(super) reserved: usize,
    pub(super) owned: usize,
    pub(super) known_unscheduled: usize,
    pub(super) in_flight: usize,
    pub(super) requested: usize,
    pub(super) unknown: usize,
}

// Only private, non-callback memory transitions run while this mutex is held.
// No indexing, allocation, JNI/AppKit call, formatting or T destructor is inside
// a transition. Poison therefore does not authorize discarding a retained record.
fn lock<T>(slot: &Mutex<Slot<T>>) -> MutexGuard<'_, Slot<T>> {
    slot.lock().unwrap_or_else(|poisoned| poisoned.into_inner())
}

impl<T, const N: usize> ReleaseSlots<T, N> {
    pub(super) fn new() -> Self {
        Self {
            slots: std::array::from_fn(|_| Mutex::new(Slot::Vacant)),
        }
    }

    /// Reserve exclusive storage BEFORE arm/CFRetain; full means no acquisition.
    pub(super) fn reserve(&self, vm_key: usize) -> Option<Reservation<'_, T>> {
        for slot in &self.slots {
            let reserved = {
                let mut state = lock(slot);
                if matches!(&*state, Slot::Vacant) {
                    *state = Slot::Reserved;
                    true
                } else {
                    false
                }
            };
            if reserved {
                return Some(Reservation {
                    slot,
                    vm_key,
                    armed: true,
                });
            }
        }
        None
    }

    /// Each physical slot is visited at most once in one bounded drain pass.
    /// Removing the record and marking in-flight happen under the same lock;
    /// the returned guard never holds a mutex while its caller performs work.
    /// A mismatched VM key does not move or consume any retained record.
    /// The key is ordinary data, captured from the live JNI entry before retain.
    pub(super) fn attempts_for(&self, vm_key: usize) -> impl Iterator<Item = Attempt<'_, T>> {
        self.slots.iter().filter_map(move |slot| {
            let previous = {
                let mut state = lock(slot);
                if !matches!(&*state, Slot::KnownUnscheduled { vm_key: key, .. } if *key == vm_key) {
                    return None;
                }
                // The check and replace are under this same private mutex.
                std::mem::replace(&mut *state, Slot::InFlight)
            };
            let value = match previous {
                Slot::KnownUnscheduled { value, .. } => value,
                _ => unreachable!("private release slot transition changed while locked"),
            };
            Some(Attempt {
                slot,
                vm_key,
                value: Some(value),
                disposition: Disposition::KnownUnscheduled,
            })
        })
    }

    /// Diagnostic snapshot only; not a native-completion or atomic global census.
    pub(super) fn counts(&self) -> Counts {
        let mut counts = Counts::default();
        for slot in &self.slots {
            match &*lock(slot) {
                Slot::Vacant => counts.vacant += 1,
                Slot::Reserved => counts.reserved += 1,
                Slot::Owned => counts.owned += 1,
                Slot::KnownUnscheduled { .. } => counts.known_unscheduled += 1,
                Slot::InFlight => counts.in_flight += 1,
                Slot::Requested => counts.requested += 1,
                Slot::Unknown { .. } => counts.unknown += 1,
            }
        }
        counts
    }
}

/// Linear reservation: no cloning or public release/reset of a reserved slot.
pub(super) struct Reservation<'slot, T> {
    slot: &'slot Mutex<Slot<T>>,
    vm_key: usize,
    armed: bool,
}

impl<'slot, T> Reservation<'slot, T> {
    /// Bind a real retained record to its already reserved storage. The record
    /// lives in the linear owner while in use, not in the recovery drain.
    pub(super) fn own(self, value: T) -> OwnedRecord<'slot, T> {
        let previous = {
            let mut state = lock(self.slot);
            std::mem::replace(&mut *state, Slot::Owned)
        };
        drop(previous); // Reserved holds no T.
        OwnedRecord {
            owned: Some((self, value)),
        }
    }

    /// Infallible memory-only handoff into the pre-reserved physical storage.
    /// The caller already owns T; no storage allocation occurs after retaining.
    pub(super) fn park(mut self, value: T) {
        let previous = {
            let mut state = lock(self.slot);
            // Only this linear reservation/owner can change Reserved/Owned.
            std::mem::replace(
                &mut *state,
                Slot::KnownUnscheduled {
                    vm_key: self.vm_key,
                    value,
                },
            )
        };
        self.armed = false;
        drop(previous); // Reserved/Owned contains no T; no destructor while locked.
    }
}

/// The actual record and reserved return storage form one inseparable owner.
/// Drop performs only a bounded memory handoff: no attach, JNI or AppKit work.
pub(super) struct OwnedRecord<'slot, T> {
    owned: Option<(Reservation<'slot, T>, T)>,
}

impl<T> OwnedRecord<'_, T> {
    pub(super) fn value(&self) -> &T {
        &self
            .owned
            .as_ref()
            .expect("live owner holds its record and storage")
            .1
    }
}

impl<T> Drop for OwnedRecord<'_, T> {
    fn drop(&mut self) {
        if let Some((reservation, value)) = self.owned.take() {
            reservation.park(value);
        }
    }
}

impl<T> Drop for Reservation<'_, T> {
    fn drop(&mut self) {
        if self.armed {
            let previous = {
                let mut state = lock(self.slot);
                std::mem::replace(&mut *state, Slot::Vacant)
            };
            drop(previous); // An unfilled reservation owns no native resource.
        }
    }
}

#[derive(Clone, Copy)]
enum Disposition {
    KnownUnscheduled,
    MayHaveInvoked,
    Requested,
}

/// RAII owns the moved record throughout a release attempt, including unwinds.
pub(super) struct Attempt<'slot, T> {
    slot: &'slot Mutex<Slot<T>>,
    vm_key: usize,
    value: Option<T>,
    disposition: Disposition,
}

impl<T> Attempt<'_, T> {
    pub(super) fn value(&self) -> &T {
        // The value is taken only by consuming request_transferred().
        self.value
            .as_ref()
            .expect("live release attempt owns its record")
    }

    /// Set BEFORE the possibly invoking JNI call, never after an error is seen.
    pub(super) fn may_have_invoked(&mut self) {
        self.disposition = Disposition::MayHaveInvoked;
    }

    /// Call only after successful request transfer, not actual native completion.
    /// Requested is terminal/no-retry. Metadata drops with no mutex held; the
    /// guard returns the slot to Vacant even if a metadata destructor unwinds.
    pub(super) fn request_transferred(mut self) {
        // A private caller cannot discard an uninvoked retain by skipping the
        // invocation boundary. This check is outside the slot mutex; on unwind
        // the still-known guard restores the original record without retrying.
        assert!(matches!(self.disposition, Disposition::MayHaveInvoked));
        self.disposition = Disposition::Requested;
        let previous = {
            let mut state = lock(self.slot);
            std::mem::replace(&mut *state, Slot::Requested)
        };
        drop(previous); // InFlight holds no T.
        let transferred = self.value.take();
        drop(transferred); // JNI/global-reference metadata disposal is outside locks.
    }
}

impl<T> Drop for Attempt<'_, T> {
    fn drop(&mut self) {
        let next = match self.value.take() {
            Some(value) => match self.disposition {
                Disposition::KnownUnscheduled => Slot::KnownUnscheduled {
                    vm_key: self.vm_key,
                    value,
                },
                Disposition::MayHaveInvoked | Disposition::Requested => Slot::Unknown {
                    _vm_key: self.vm_key,
                    _owned: value,
                },
            },
            None => Slot::Vacant, // A successful request transferred the retain.
        };
        let previous = {
            let mut state = lock(self.slot);
            std::mem::replace(&mut *state, next)
        };
        drop(previous); // InFlight/Requested has no T; never drop under the mutex.
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::panic::{catch_unwind, AssertUnwindSafe};
    use std::sync::atomic::{AtomicUsize, Ordering};
    use std::sync::{Arc, Barrier};

    struct Record {
        pointer: usize, // Numeric model value, NOT a real retained native pointer.
        drops: Arc<AtomicUsize>,
        on_drop: Option<Box<dyn Fn() + Send + Sync>>,
    }

    impl Drop for Record {
        fn drop(&mut self) {
            self.drops.fetch_add(1, Ordering::SeqCst);
            if let Some(on_drop) = &self.on_drop {
                on_drop();
            }
        }
    }

    fn record(pointer: usize, drops: &Arc<AtomicUsize>) -> Record {
        Record { pointer, drops: drops.clone(), on_drop: None }
    }

    #[test]
    fn full_reservation_refuses_before_any_model_retain() {
        let slots = ReleaseSlots::<Record, 1>::new();
        let reservation = slots.reserve(1).unwrap();
        let retains = AtomicUsize::new(0);
        if slots.reserve(1).is_some() { retains.fetch_add(1, Ordering::SeqCst); }
        assert_eq!(retains.load(Ordering::SeqCst), 0);
        assert_eq!(slots.counts().reserved, 1);
        drop(reservation);
        assert_eq!(slots.counts().vacant, 1);
    }

    #[test]
    fn memory_handoff_keeps_one_actual_record_until_request_transfer() {
        let slots = ReleaseSlots::<Record, 1>::new();
        let drops = Arc::new(AtomicUsize::new(0));
        let owner = slots.reserve(1).unwrap().own(record(0x1000, &drops));
        assert_eq!(owner.value().pointer, 0x1000);
        assert_eq!(slots.counts().owned, 1);
        assert_eq!(slots.attempts_for(1).count(), 0);
        drop(owner);
        assert_eq!(drops.load(Ordering::SeqCst), 0);
        assert_eq!(slots.counts().known_unscheduled, 1);
        let mut attempt = slots.attempts_for(1).next().unwrap();
        assert_eq!(attempt.value().pointer, 0x1000);
        assert_eq!(slots.counts().in_flight, 1);
        attempt.may_have_invoked();
        attempt.request_transferred();
        assert_eq!(drops.load(Ordering::SeqCst), 1);
        assert_eq!(slots.counts().vacant, 1);
        assert_eq!(slots.attempts_for(1).count(), 0);
    }

    #[test]
    fn provably_uninvoked_failure_restores_the_same_owned_record() {
        let slots = ReleaseSlots::<Record, 1>::new();
        let drops = Arc::new(AtomicUsize::new(0));
        slots.reserve(1).unwrap().park(record(0x1000, &drops));
        drop(slots.attempts_for(1).next().unwrap());
        assert_eq!(slots.counts().known_unscheduled, 1);
        assert_eq!(drops.load(Ordering::SeqCst), 0);
        let mut next = slots.attempts_for(1).next().unwrap();
        assert_eq!(next.value().pointer, 0x1000);
        next.may_have_invoked();
        next.request_transferred();
        assert_eq!(drops.load(Ordering::SeqCst), 1);
    }

    #[test]
    fn potentially_invoked_failure_is_quarantined_and_never_retried() {
        let slots = ReleaseSlots::<Record, 1>::new();
        let drops = Arc::new(AtomicUsize::new(0));
        slots.reserve(1).unwrap().park(record(0x1000, &drops));
        let mut attempt = slots.attempts_for(1).next().unwrap();
        attempt.may_have_invoked();
        drop(attempt);
        assert_eq!(slots.counts().unknown, 1);
        assert_eq!(slots.attempts_for(1).count(), 0);
        assert!(slots.reserve(1).is_none());
        assert_eq!(drops.load(Ordering::SeqCst), 0);
    }

    #[test]
    fn unwind_before_invocation_keeps_known_unscheduled_ownership() {
        let slots = ReleaseSlots::<Record, 1>::new();
        let drops = Arc::new(AtomicUsize::new(0));
        slots.reserve(1).unwrap().park(record(0x1000, &drops));
        assert!(catch_unwind(AssertUnwindSafe(|| {
            let _attempt = slots.attempts_for(1).next().unwrap();
            panic!("model pre-invocation failure");
        })).is_err());
        assert_eq!(slots.counts().known_unscheduled, 1);
        assert_eq!(drops.load(Ordering::SeqCst), 0);
    }

    #[test]
    fn unwind_after_possible_invocation_keeps_unknown_not_retryable() {
        let slots = ReleaseSlots::<Record, 1>::new();
        let drops = Arc::new(AtomicUsize::new(0));
        slots.reserve(1).unwrap().park(record(0x1000, &drops));
        assert!(catch_unwind(AssertUnwindSafe(|| {
            let mut attempt = slots.attempts_for(1).next().unwrap();
            attempt.may_have_invoked();
            panic!("model possibly invoked failure");
        })).is_err());
        assert_eq!(slots.counts().unknown, 1);
        assert_eq!(slots.attempts_for(1).count(), 0);
        assert_eq!(drops.load(Ordering::SeqCst), 0);
    }

    #[test]
    fn one_drain_pass_visits_each_retryable_physical_slot_only_once() {
        let slots = ReleaseSlots::<Record, 3>::new();
        let drops = Arc::new(AtomicUsize::new(0));
        for pointer in 1..=3 { slots.reserve(1).unwrap().park(record(pointer, &drops)); }
        let visits = slots.attempts_for(1).map(|attempt| { drop(attempt); 1 }).sum::<usize>();
        assert_eq!(visits, 3);
        assert_eq!(slots.counts().known_unscheduled, 3);
        assert_eq!(drops.load(Ordering::SeqCst), 0);
    }

    #[test]
    fn request_metadata_destructor_can_reenter_without_a_held_mutex() {
        let slots = Arc::new(ReleaseSlots::<Record, 1>::new());
        let drops = Arc::new(AtomicUsize::new(0));
        let weak = Arc::downgrade(&slots);
        let mut value = record(0x1000, &drops);
        value.on_drop = Some(Box::new(move || {
            assert_eq!(weak.upgrade().unwrap().counts().requested, 1);
        }));
        slots.reserve(1).unwrap().park(value);
        let mut attempt = slots.attempts_for(1).next().unwrap();
        attempt.may_have_invoked();
        attempt.request_transferred();
        assert_eq!(drops.load(Ordering::SeqCst), 1);
        assert_eq!(slots.counts().vacant, 1);
    }

    #[test]
    fn requested_metadata_unwind_does_not_reinstate_a_release_record() {
        let slots = ReleaseSlots::<Record, 1>::new();
        let drops = Arc::new(AtomicUsize::new(0));
        let mut value = record(0x1000, &drops);
        value.on_drop = Some(Box::new(|| panic!("model metadata Drop failure")));
        slots.reserve(1).unwrap().park(value);
        assert!(catch_unwind(AssertUnwindSafe(|| {
            let mut attempt = slots.attempts_for(1).next().unwrap();
            attempt.may_have_invoked();
            attempt.request_transferred();
        })).is_err());
        assert_eq!(slots.counts().vacant, 1);
        assert_eq!(slots.attempts_for(1).count(), 0);
        assert_eq!(drops.load(Ordering::SeqCst), 1);
    }

    #[test]
    fn concurrent_reservations_are_bounded_and_each_record_transfers_once() {
        let slots = Arc::new(ReleaseSlots::<Record, 8>::new());
        let drops = Arc::new(AtomicUsize::new(0));
        let ready = Arc::new(Barrier::new(9));
        let proceed = Arc::new(Barrier::new(9));
        let workers = (1..=8).map(|pointer| {
            let slots = slots.clone();
            let drops = drops.clone();
            let ready = ready.clone();
            let proceed = proceed.clone();
            std::thread::spawn(move || {
                let reservation = slots.reserve(1).unwrap();
                ready.wait();
                proceed.wait();
                reservation.park(record(pointer, &drops));
            })
        }).collect::<Vec<_>>();
        ready.wait();
        assert_eq!(slots.counts().reserved, 8);
        assert!(slots.reserve(1).is_none());
        proceed.wait();
        for worker in workers { worker.join().unwrap(); }
        assert_eq!(slots.counts().known_unscheduled, 8);
        for mut attempt in slots.attempts_for(1) {
            attempt.may_have_invoked();
            attempt.request_transferred();
        }
        assert_eq!(slots.counts().vacant, 8);
        assert_eq!(drops.load(Ordering::SeqCst), 8);
    }

    #[test]
    fn empty_capacity_has_no_reservation_or_release_work() {
        let slots = ReleaseSlots::<Record, 0>::new();
        assert!(slots.reserve(1).is_none());
        assert_eq!(slots.attempts_for(1).count(), 0);
        assert_eq!(slots.counts(), Counts::default());
    }

    #[test]
    fn wrong_vm_pass_does_not_move_known_or_quarantined_records() {
        let slots = ReleaseSlots::<Record, 3>::new();
        let drops = Arc::new(AtomicUsize::new(0));
        slots.reserve(1).unwrap().park(record(0x1000, &drops));
        slots.reserve(2).unwrap().park(record(0x2000, &drops));
        slots.reserve(1).unwrap().park(record(0x3000, &drops));
        let mut known = slots.attempts_for(1);
        drop(known.next().unwrap());
        let mut unknown = known.next().unwrap();
        unknown.may_have_invoked();
        drop(unknown);
        assert_eq!(slots.counts().known_unscheduled, 2);
        assert_eq!(slots.counts().unknown, 1);
        assert_eq!(slots.attempts_for(3).count(), 0);
        assert_eq!(slots.counts().in_flight, 0);
        assert_eq!(drops.load(Ordering::SeqCst), 0);
        let mut first_vm = slots.attempts_for(1).next().unwrap();
        assert_eq!(first_vm.value().pointer, 0x1000);
        first_vm.may_have_invoked();
        first_vm.request_transferred();
        assert_eq!(slots.attempts_for(1).count(), 0);
        assert_eq!(slots.counts().known_unscheduled, 1);
        assert_eq!(slots.counts().unknown, 1);
        assert_eq!(drops.load(Ordering::SeqCst), 1);
    }

    #[test]
    fn uninvoked_transfer_is_refused_without_discarding_the_retain_record() {
        let slots = ReleaseSlots::<Record, 1>::new();
        let drops = Arc::new(AtomicUsize::new(0));
        slots.reserve(1).unwrap().park(record(0x1000, &drops));
        assert!(catch_unwind(AssertUnwindSafe(|| {
            slots.attempts_for(1).next().unwrap().request_transferred();
        }))
        .is_err());
        assert_eq!(slots.counts().known_unscheduled, 1);
        assert_eq!(slots.counts().unknown, 0);
        assert_eq!(drops.load(Ordering::SeqCst), 0);
    }

    #[test]
    fn owner_unwind_parks_the_real_record_without_record_destructor_work() {
        let slots = ReleaseSlots::<Record, 1>::new();
        let drops = Arc::new(AtomicUsize::new(0));
        assert!(catch_unwind(AssertUnwindSafe(|| {
            let _owner = slots.reserve(1).unwrap().own(record(0x1000, &drops));
            panic!("model logical primary before JNI exception delivery");
        }))
        .is_err());
        assert_eq!(slots.counts().known_unscheduled, 1);
        assert_eq!(drops.load(Ordering::SeqCst), 0);
        assert_eq!(slots.attempts_for(1).next().unwrap().value().pointer, 0x1000);
        assert_eq!(slots.counts().known_unscheduled, 1);
    }

    #[test]
    fn capacity_sixty_four_is_finite_and_all_actual_model_records_transfer_once() {
        let slots = ReleaseSlots::<Record, 64>::new();
        let drops = Arc::new(AtomicUsize::new(0));
        let retains = AtomicUsize::new(0);
        for pointer in 1..=64 {
            let reservation = slots.reserve(1).unwrap();
            retains.fetch_add(1, Ordering::SeqCst); // Numeric model, NOT CFRetain.
            drop(reservation.own(record(pointer, &drops)));
        }
        if slots.reserve(1).is_some() {
            retains.fetch_add(1, Ordering::SeqCst);
        }
        assert_eq!(retains.load(Ordering::SeqCst), 64);
        assert_eq!(slots.counts().known_unscheduled, 64);
        assert_eq!(drops.load(Ordering::SeqCst), 0);
        for mut attempt in slots.attempts_for(1) {
            attempt.may_have_invoked();
            attempt.request_transferred();
        }
        assert_eq!(drops.load(Ordering::SeqCst), 64);
        assert_eq!(slots.counts().vacant, 64);
    }

    #[test]
    fn concurrent_drain_passes_cannot_duplicate_one_retained_model_record() {
        let slots = Arc::new(ReleaseSlots::<Record, 16>::new());
        let drops = Arc::new(AtomicUsize::new(0));
        let seen = Arc::new(Mutex::new(std::collections::BTreeSet::new()));
        for pointer in 1..=16 {
            slots.reserve(1).unwrap().park(record(pointer, &drops));
        }
        let start = Arc::new(Barrier::new(5));
        let workers = (0..4)
            .map(|_| {
                let slots = slots.clone();
                let seen = seen.clone();
                let start = start.clone();
                std::thread::spawn(move || {
                    start.wait();
                    for mut attempt in slots.attempts_for(1) {
                        assert!(seen.lock().unwrap().insert(attempt.value().pointer));
                        attempt.may_have_invoked();
                        attempt.request_transferred();
                    }
                })
            })
            .collect::<Vec<_>>();
        start.wait();
        for worker in workers {
            worker.join().unwrap();
        }
        assert_eq!(seen.lock().unwrap().len(), 16);
        assert_eq!(drops.load(Ordering::SeqCst), 16);
        assert_eq!(slots.counts().vacant, 16);
    }
}
