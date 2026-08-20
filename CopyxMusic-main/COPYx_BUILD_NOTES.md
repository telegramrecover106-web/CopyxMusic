# COPYx MUSIC — Updated Build

Base: the supplied COPYxMusic project.

Included updates:
- Supplied COPYx MUSIC welcome artwork added at `assets/copyx_welcome.png`.
- `/start` uses the supplied artwork and COPYx MUSIC branding.
- Bot-added group welcome message with group name, adder name/ID/username and COPYx MUSIC link.
- Dynamic group welcome card generated from the supplied artwork; includes the adder profile photo when Telegram exposes one.
- Public and private groups are handled through the same group handlers.
- `/play` in private chat returns the requested group-only warning.
- `/play` checks for an active voice chat before searching.
- Search status animation: search → dance → playback.
- Player message includes duration, requester mention, and a YouTube link on the song title/button.
- Music controls are available to all group members: pause/resume, skip, stop, queue, shuffle, loop, refresh, add-me and close.
- `/stop` clears playback and queue without an admin-only restriction.
- A background voice-chat watcher announces voice-chat start/end and clears playback state when a call ends.
- Assistant auto-join/retry logic from the supplied COPYxMusic implementation is retained.
- Added defensive error handling around playback/status updates to reduce crash loops.

Important:
This build does not reproduce third-party ArtistMusic source code verbatim. Its behavior was used only as a reference for the requested feature set; the implementation is based on your supplied COPYxMusic project.
