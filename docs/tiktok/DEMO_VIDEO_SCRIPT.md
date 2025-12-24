# Demo Video Script - TikTok Battle Simulator

**Duration:** 4-5 minutes
**Format:** MP4 or MOV, 1080p recommended
**Max Size:** 50MB per file

---

## Pre-Recording Checklist

- [ ] Clear browser cache and cookies
- [ ] Have TikTok test account ready
- [ ] Start the server: `python -m web.backend.app`
- [ ] Open browser with URL bar visible
- [ ] Screen recording software ready (OBS, Loom, etc.)
- [ ] Optional: Microphone for narration

---

## Scene-by-Scene Script

### Scene 1: Introduction & Website (0:00 - 0:20)

**Action:**
1. Open browser to `https://your-domain.com`
2. Show the main dashboard
3. Scroll to show key features

**Narration (optional):**
> "This is TikTok Battle Simulator, a real-time battle tracking platform for TikTok Live streams. Let me show you how it integrates with TikTok."

**Visual Focus:**
- URL bar clearly showing your domain
- Main dashboard with battle visualization area
- Navigation menu showing features

---

### Scene 2: TikTok Login (0:20 - 1:00) - SCOPE: `user.info.basic`

**Action:**
1. Click "Connect TikTok Account" button
2. Show TikTok OAuth consent screen
3. Authorize the app
4. Return to app with profile displayed

**Narration:**
> "Users can connect their TikTok account using TikTok's secure login. We only request basic profile information - username and avatar - which is displayed here."

**Visual Focus:**
- Clear view of OAuth consent screen
- Show exactly what permissions are requested
- After login, show user's TikTok profile displayed in app

**Important:**
- Keep OAuth consent screen visible for at least 3 seconds
- Show the scopes being requested clearly

---

### Scene 3: Starting a Live Battle (1:00 - 1:45) - SCOPE: `live.room.info`

**Action:**
1. Navigate to "Live Battle" page
2. Enter Creator 1 TikTok username
3. Enter Creator 2 TikTok username (opponent)
4. Click "Start Battle"
5. Show connection status

**Narration:**
> "To start a battle, we enter two TikTok usernames. Our system uses the Live API to verify they're currently streaming and connect to their live rooms."

**Visual Focus:**
- Input fields for usernames
- Connection status indicators
- Room info being displayed (viewer count, etc.)

**Note for Sandbox:**
> If using sandbox, show the sandbox environment and explain that live data will be simulated.

---

### Scene 4: Live Gift Tracking (1:45 - 2:45) - SCOPE: `live.gift.info`

**Action:**
1. Show the battle dashboard with both creators
2. When gifts come in, show:
   - Gift animation appearing
   - Score updating in real-time
   - Gifter name displayed
   - Gift type and value shown
3. Show top gifters section updating

**Narration:**
> "When viewers send gifts during the live stream, we receive the gift data in real-time through the Live API. The dashboard updates instantly showing the gift type, value, and sender. This creates an engaging experience for the audience."

**Visual Focus:**
- Gift events appearing on screen
- Scores incrementing
- Top gifters leaderboard changing
- Time remaining countdown

**Important:**
- Show at least 3-5 gift events
- Show different gift types (Rose, Galaxy, etc.)

---

### Scene 5: Battle Analytics (2:45 - 3:15)

**Action:**
1. Navigate to Analytics page
2. Show overview statistics
3. Show score distribution graph
4. Show agent performance metrics

**Narration:**
> "After battles, creators can view detailed analytics including win rates, average scores, and performance trends over time."

**Visual Focus:**
- Charts and graphs
- Statistics cards
- Historical data

---

### Scene 6: Leaderboards (3:15 - 3:45)

**Action:**
1. Navigate to Leaderboard page
2. Show Top Gifters rankings
3. Show Top Agents rankings
4. Click on a profile to show detailed stats

**Narration:**
> "Our leaderboards recognize top gifters and track agent performance across all battles, creating a competitive and engaging community."

**Visual Focus:**
- Podium display for top 3
- Full rankings list
- Individual stats on click

---

### Scene 7: OBS/Streaming Integration (3:45 - 4:15)

**Action:**
1. Navigate to OBS Setup page
2. Show the overlay URLs
3. Open OBS (or streaming software)
4. Add browser source with overlay URL
5. Show the overlay working in OBS

**Narration:**
> "Streamers can easily add our battle overlays to their streaming software. Simply copy the URL and add it as a browser source in OBS."

**Visual Focus:**
- OBS setup instructions page
- OBS window with browser source
- Overlay displayed in stream preview

---

### Scene 8: Battle Conclusion (4:15 - 4:30)

**Action:**
1. Show battle ending
2. Winner announcement
3. Final stats displayed
4. Replay option shown

**Narration:**
> "When the battle ends, we display the winner, final scores, and provide options to view replays or analytics."

**Visual Focus:**
- Winner announcement animation
- Final statistics summary
- Replay controls

---

### Scene 9: Closing & Privacy (4:30 - 4:45)

**Action:**
1. Navigate to Privacy Policy page
2. Scroll to show key sections
3. Show Terms of Service link

**Narration:**
> "We take user privacy seriously. Our privacy policy and terms of service are always accessible and compliant with TikTok's guidelines."

**Visual Focus:**
- Privacy Policy URL in address bar
- Key privacy sections visible

---

## Post-Recording Checklist

- [ ] Video is under 50MB
- [ ] All three scopes are demonstrated:
  - [ ] `user.info.basic` - Login flow
  - [ ] `live.room.info` - Room connection
  - [ ] `live.gift.info` - Gift tracking
- [ ] URL bar visible throughout
- [ ] Domain matches your application
- [ ] No sensitive data exposed
- [ ] Video is clear and not blurry

---

## Alternative: Sandbox-Only Demo

If you cannot use live TikTok accounts, record using the sandbox:

1. Start with sandbox environment explanation
2. Show simulated OAuth flow
3. Demonstrate with test data
4. Explain that production will use real data

**Add text overlay:**
> "Demonstration using TikTok Developer Portal Sandbox. Production version will connect to live TikTok streams."

---

## Recording Tips

1. **Use 1080p resolution** - Ensures text is readable
2. **Record in a single take** if possible - Shows authentic flow
3. **Move slowly** - Reviewers need to see each step clearly
4. **Pause on important screens** - OAuth, gift events, etc.
5. **Keep browser zoom at 100%** - Consistent appearance
6. **Use a clean browser profile** - No distracting extensions

---

## Export Settings

**Recommended:**
- Format: MP4 (H.264)
- Resolution: 1920x1080
- Frame rate: 30fps
- Bitrate: 5-10 Mbps
- Audio: AAC 128kbps (if using narration)

**Compress if needed:**
```bash
ffmpeg -i demo_video.mp4 -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k demo_video_compressed.mp4
```

---

**Good luck with your demo video!**
