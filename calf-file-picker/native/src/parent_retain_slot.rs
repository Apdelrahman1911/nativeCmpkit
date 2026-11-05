// Added for NativeCmpKit: one-shot authorization for a real JDK resource borrow.
// A ticket is NOT native ownership. Only the callback's successful CFRetain is.
use std::sync::atomic::{AtomicI64, Ordering};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) enum BorrowError {
    Exhausted,
    Busy,
    NoRequest,
    WrongTicket,
    RepeatedCallback,
    NullResource,
    RetainMismatch,
    NoLiveResource,
}

pub(super) struct RequestIds(AtomicI64);

impl RequestIds {
    pub(super) const fn new() -> Self {
        Self(AtomicI64::new(1))
    }

    pub(super) fn next(&self) -> Result<i64, BorrowError> {
        self.0
            .fetch_update(Ordering::Relaxed, Ordering::Relaxed, |id| id.checked_add(1))
            .map_err(|_| BorrowError::Exhausted)
    }
}

#[derive(Default)]
pub(super) struct RetainSlot {
    request: Option<Request>,
}

struct Request {
    ticket: i64,
    called: bool,
    owned: Option<usize>,
    failure: Option<BorrowError>,
}

pub(super) struct BorrowOutcome {
    // Keep even on a later protocol failure: the caller must release this retain.
    pub(super) owned: Option<usize>,
    pub(super) result: Result<(), BorrowError>,
}

impl RetainSlot {
    pub(super) fn arm(&mut self, ticket: i64) -> Result<(), BorrowError> {
        if self.request.is_some() {
            return Err(BorrowError::Busy);
        }
        if ticket <= 0 {
            return Err(BorrowError::WrongTicket);
        }
        self.request = Some(Request {
            ticket,
            called: false,
            owned: None,
            failure: None,
        });
        Ok(())
    }

    /// Run the retain exactly once, synchronously inside the actual borrow.
    /// No dispatch, mutex, registry operation or AppKit UI is performed here.
    pub(super) fn retain_once(
        &mut self,
        ticket: i64,
        borrowed: usize,
        retain: impl FnOnce(usize) -> usize,
    ) -> Result<(), BorrowError> {
        let request = self.request.as_mut().ok_or(BorrowError::NoRequest)?;
        if let Some(failure) = request.failure {
            return Err(failure);
        }
        let failure = if request.ticket != ticket {
            Some(BorrowError::WrongTicket)
        } else if request.called {
            Some(BorrowError::RepeatedCallback)
        } else if borrowed == 0 {
            Some(BorrowError::NullResource)
        } else {
            None
        };
        if let Some(failure) = failure {
            request.failure = Some(failure);
            return Err(failure);
        }
        // Consume authorization BEFORE entering the ownership operation.
        request.called = true;
        let owned = retain(borrowed);
        request.owned = (owned != 0).then_some(owned);
        if owned != borrowed {
            request.failure = Some(BorrowError::RetainMismatch);
            return Err(BorrowError::RetainMismatch);
        }
        Ok(())
    }

    pub(super) fn finish(&mut self, ticket: i64) -> BorrowOutcome {
        let Some(request) = self.request.take() else {
            return BorrowOutcome {
                owned: None,
                result: Err(BorrowError::NoRequest),
            };
        };
        let result = if ticket != request.ticket {
            Err(BorrowError::WrongTicket)
        } else if let Some(failure) = request.failure {
            Err(failure)
        } else if !request.called || request.owned.is_none() {
            Err(BorrowError::NoLiveResource)
        } else {
            Ok(())
        };
        BorrowOutcome {
            owned: request.owned,
            result,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::Cell;
    use std::collections::BTreeSet;
    use std::sync::Arc;

    #[test]
    fn successful_callback_authorizes_one_retain_invocation_and_drains_slot() {
        let mut slot = RetainSlot::default();
        let retains = Cell::new(0);
        slot.arm(3).unwrap();
        slot.retain_once(3, 0x1000, |ptr| {
            retains.set(retains.get() + 1);
            ptr
        })
        .unwrap();
        let outcome = slot.finish(3);
        assert_eq!(outcome.result, Ok(()));
        assert_eq!(outcome.owned, Some(0x1000));
        assert_eq!(retains.get(), 1);
        assert_eq!(slot.finish(3).result, Err(BorrowError::NoRequest));
        slot.arm(4).unwrap();
    }

    #[test]
    fn disposed_resource_without_callback_is_not_an_unparented_success() {
        let mut slot = RetainSlot::default();
        slot.arm(3).unwrap();
        let outcome = slot.finish(3);
        assert_eq!(outcome.result, Err(BorrowError::NoLiveResource));
        assert_eq!(outcome.owned, None);
    }

    #[test]
    fn wrong_ticket_and_null_pointer_never_reach_retain() {
        for (ticket, ptr, error) in [
            (2, 0x1000, BorrowError::WrongTicket),
            (3, 0, BorrowError::NullResource),
        ] {
            let mut slot = RetainSlot::default();
            slot.arm(3).unwrap();
            assert_eq!(
                slot.retain_once(ticket, ptr, |_| panic!("must not retain")),
                Err(error)
            );
            assert_eq!(
                slot.retain_once(3, 0x1000, |_| panic!("failure must be sticky")),
                Err(error)
            );
            let outcome = slot.finish(3);
            assert_eq!(outcome.result, Err(error));
            assert_eq!(outcome.owned, None);
        }
    }

    #[test]
    fn duplicate_callback_preserves_exactly_one_owner_for_failure_cleanup() {
        let mut slot = RetainSlot::default();
        let retains = Cell::new(0);
        slot.arm(3).unwrap();
        slot.retain_once(3, 0x1000, |ptr| {
            retains.set(1);
            ptr
        })
        .unwrap();
        assert_eq!(
            slot.retain_once(3, 0x1000, |_| panic!("double retain")),
            Err(BorrowError::RepeatedCallback)
        );
        let outcome = slot.finish(3);
        assert_eq!(outcome.result, Err(BorrowError::RepeatedCallback));
        assert_eq!(outcome.owned, Some(0x1000));
        assert_eq!(retains.get(), 1);
    }

    #[test]
    fn nested_request_is_refused_without_erasing_the_original_owner() {
        let mut slot = RetainSlot::default();
        slot.arm(3).unwrap();
        assert_eq!(slot.arm(4), Err(BorrowError::Busy));
        slot.retain_once(3, 0x1000, |ptr| ptr).unwrap();
        assert_eq!(slot.finish(3).owned, Some(0x1000));
        assert_eq!(
            slot.retain_once(3, 0x1000, |_| panic!("late callback")),
            Err(BorrowError::NoRequest)
        );
    }

    #[test]
    fn retain_mismatch_keeps_any_returned_owner_for_cleanup() {
        for result in [0, 0x2000] {
            let mut slot = RetainSlot::default();
            slot.arm(3).unwrap();
            assert_eq!(
                slot.retain_once(3, 0x1000, |_| result),
                Err(BorrowError::RetainMismatch)
            );
            let outcome = slot.finish(3);
            assert_eq!(outcome.result, Err(BorrowError::RetainMismatch));
            assert_eq!(outcome.owned, (result != 0).then_some(result));
        }
    }

    #[test]
    fn request_ids_are_unique_across_concurrent_native_callers() {
        let ids = Arc::new(RequestIds::new());
        let workers: Vec<_> = (0..8)
            .map(|_| {
                let ids = ids.clone();
                std::thread::spawn(move || (0..64).map(|_| ids.next().unwrap()).collect::<Vec<_>>())
            })
            .collect();
        let actual: BTreeSet<_> = workers
            .into_iter()
            .flat_map(|w| w.join().unwrap())
            .collect();
        assert_eq!(actual.len(), 512);
        assert_eq!(*actual.first().unwrap(), 1);
        assert_eq!(*actual.last().unwrap(), 512);
    }

    #[test]
    fn exhaustion_cannot_wrap_or_reuse_zero_or_an_old_ticket() {
        let ids = RequestIds(AtomicI64::new(i64::MAX));
        assert_eq!(ids.next(), Err(BorrowError::Exhausted));
        assert_eq!(ids.next(), Err(BorrowError::Exhausted));
        assert_eq!(ids.0.load(Ordering::Relaxed), i64::MAX);
    }
}
