# V66 Live Data Service Startup Hotfix

Permanent no-admin fix: the resident KuCoin Live Data Service now registers under the current user's HKCU Run key and starts immediately. The obsolete scheduled-task implementation is removed if present. System Health and recovery understand the new mechanism. Future builds inherit this source.
