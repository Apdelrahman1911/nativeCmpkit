# Owning source mismatch, before the focused runtime result

At immutable6cfe4649, iOS createIOSPermissionState calls PermissionDelegateRegistry.getDelegate. An absent registration throws; CallbackPermissionState.refresh/request catches it and records Failed with default Unknown availability. Android unknown mappings explicitly report Unsupported and false. The missing-vs-registered-factory-failure diagnostic was inconsistent. This is source-confirmed, not yet an executed reproduction.

Minimal repair: internal nullable registry lookup invokes factories outside NSLock; the public getDelegate descriptor/error remains unchanged. Only a null/missing factory maps to the existing NotGrantedPermissionHelper (Unsupported). A throwing registered factory is not caught/converted into Unsupported; the state retains Failed. Both public single and child/batch routes share this owning factory.

The immutable test-only hosted run40671696029 still owns6cfe4649 and its eventual outcome must be retained, even though the local fix is prepared afterward. No test result, issue closure or release claim follows from source edits or the local failed compiler acquisition.
