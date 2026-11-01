# Proposed owner/lead trust-boundary wording — not adopted

NativeCmpKit's Desktop WebView integration is not a Java security-sandbox boundary. Host application code and callbacks can customize the native engine. The library does not implement an untrusted-Java loader, an applet/Web Start execution service, or isolation based on the legacy Java sandbox.

Applications must not assume that embedding this WebView safely isolates untrusted Java application/plugin code. Whether such code execution is part of the supported application scope requires an explicit owner decision and a separate isolation/security design. This proposal does not retroactively certify every consumer or change the public API.

Webpage JavaScript and hostile HTML/image/media data are distinct from untrusted Java bytecode. JavaScript is off by default, but enabling it or serving hostile data remains an application trust decision. Trusted application Java does not make all embedded-engine/data-API advisories inapplicable. Keep the complete JavaFX module set aligned, review vendor and component advisories, and verify actual host runtimes.

This wording may clarify the original policy criterion only after adoption and exact source review. It does not clear the remaining graph, runtime, consumer, supply-chain or release gates and does not close #144.
