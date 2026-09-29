Kore is a native lightweight service/target manager layered above the Koronos scheduler. It models target Wants, service Requires, and ordering After relationships. Independent services may be submitted together so the scheduler can execute them on separate CPUs/cores or through cooperative turns without forced serialization.

Targets:
- koronos.target: base kernel runtime
- hardware.target: console, timer, storage discovery
- runtime.target: module manager and security
- live.target: live initramfs and Aurora
- installer.target: installer image, storage, installer UI
- complete.target: installed system convergence target
