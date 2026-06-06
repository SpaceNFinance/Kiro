# Production Guide: "Start Saving NOW" TikTok Short

## Quick Reference

| Spec | Value |
|------|-------|
| Duration | 58 seconds |
| Aspect Ratio | 9:16 (1080x1920) |
| Frame Rate | 30fps (60fps preferred) |
| Format | MP4 (H.264) |
| File Size | Under 287MB (TikTok limit) |
| Audio | AAC, 44.1kHz |

---

## Stock Footage Sources (Royalty-Free)

Use these for the REAL video production. The HTML prototype shows timing/flow — replace with actual footage:

### Sports Cars & Coastal Driving
- **Pexels:** Search "sports car driving coast" — free, no attribution needed
- **Pixabay:** "luxury car road" — free commercial use
- **Coverr.co:** "driving" category — free for any use
- **Mixkit.co:** "sports car" — free with no license required

### Beach & Young People
- **Pexels:** "friends beach" "young people ocean" "beach sunset"
- **Coverr.co:** "beach" and "lifestyle" categories
- **Mixkit.co:** "beach party" "friends outdoor" "young lifestyle"
- **Videvo.net:** Free tier has solid beach footage

### Money & Finance Visuals
- **Pixabay:** "money falling" "dollar bills" "savings"
- **Mixkit.co:** "finance" "money" "business"

---

## Music & Sound Effects

### Background Beat (Royalty-Free)
- **Uppbeat.io** — Search "trap beat" or "hip hop energetic" (free with credit)
- **Pixabay Music** — "trap" "hip hop" (fully free)
- **Epidemic Sound** — "motivational trap" (paid, best quality)
- **YouTube Audio Library** — "hip hop" (free for YouTube/TikTok)

**Ideal BPM:** 100–130 BPM  
**Mood:** High energy, motivational, youthful

### Sound Effects Needed
| SFX | Where to find |
|-----|--------------|
| Cash register | Pixabay SFX, Freesound.org |
| Record scratch | Freesound.org |
| Money counter | Pixabay SFX |
| Typing/keyboard | Freesound.org |
| Notification dings | Zapsplat.com |
| Crowd cheering | Freesound.org |
| Whoosh transitions | Mixkit.co SFX |
| Bass drop | Freesound.org |

---

## Editing Software Options

### Mobile (Quick Edits)
| App | Best For | Cost |
|-----|----------|------|
| **CapCut** | TikTok-native editing, auto-captions | Free |
| **InShot** | Quick cuts, text overlays | Free/Pro |
| **VN Editor** | Multi-layer, transitions | Free |

### Desktop (Pro Quality)
| Software | Best For | Cost |
|----------|----------|------|
| **DaVinci Resolve** | Color grading, effects | Free |
| **Premiere Pro** | Industry standard, speed | $22/mo |
| **Final Cut Pro** | Mac users, smooth workflow | $299 one-time |

### Recommended: **CapCut Desktop** (Free)
- Auto-generates subtitles (saves huge time)
- TikTok-style templates built in
- Export directly in 9:16 at 1080p

---

## Subtitle Specifications

```
Font: Montserrat Black (or Arial Black)
Size: 60-72px at 1080p
Color: White (#FFFFFF)
Stroke: 4px Black (#000000)
Shadow: 2px offset, 50% opacity black
Position: Lower third (but above TikTok UI ~200px from bottom)
Animation: Pop-in or slide-up (0.2s)
Max words per screen: 8-10
CAPS for emphasis words
Yellow (#FFD700) for key numbers/words
```

### Auto-Subtitle Tools
- **CapCut** — Built-in, very accurate
- **Veed.io** — Browser-based, exports SRT
- **Descript** — Best accuracy, paid

---

## Step-by-Step Export Workflow

### Using CapCut (Recommended)

1. **Import footage** — Drag clips into timeline matching the script timings
2. **Cut to beat** — Use beat markers to align cuts with music
3. **Add text/subtitles** — Use auto-captions, then style manually
4. **Apply transitions** — Glitch, flash, zoom (match script notes)
5. **Color grade** — Warm tones, high contrast, slight orange/teal
6. **Export settings:**
   - Resolution: 1080 x 1920
   - Frame rate: 30fps
   - Quality: High
   - Format: MP4

### TikTok Upload Settings
- Add 3-5 hashtags: `#finance #moneytips #investing #youngmoney #savingmoney`
- Enable captions (TikTok auto-captions as backup)
- Post time: 7-9 AM or 7-10 PM (highest engagement for finance content)
- Add trending sound if possible (overlay with your beat)

---

## Converting HTML Prototype to Real Video

The `index.html` file serves as your **storyboard/animatic**. To make the real video:

### Option A: Screen Record + Replace
1. Open `index.html` in Chrome
2. Screen record with OBS (set to 1080x1920 canvas)
3. Use the recording as a timing reference in your editor
4. Replace each scene with real stock footage

### Option B: Direct Production
1. Use `script.md` as your shot list
2. Source footage for each scene from stock sites above
3. Match the timing exactly (no shot > 5 seconds)
4. Follow subtitle text and transition notes

### Option C: AI Video Generation
Use the script with AI video tools:
- **Runway ML** — Gen-2 for short clips (cars, beaches)
- **Pika Labs** — Stylized motion video
- **HeyGen** — If you want an AI presenter

---

## Color Grading Reference

```
Shadows: Slightly teal/blue
Midtones: Neutral to warm
Highlights: Golden/orange
Saturation: +15-20%
Contrast: +10-15%
Vibrance: +20%
```

This gives the "golden hour on the coast" look throughout.

---

## Performance Tips for TikTok Algorithm

1. **Hook in first 1 second** — The car + "You're 20 and BROKE?" grabs attention
2. **No dead air** — Every second has motion, text, or audio change
3. **Loop potential** — The ending CTA connects back to the hook thematically
4. **Engagement bait** — "Screenshot your balance" drives saves/shares
5. **Text on screen** — Increases watch time (people read slower than they listen)
6. **Trending format** — Finance + lifestyle + fast pace = algorithm-friendly

---

## File Deliverables in This Package

```
tiktok-savings-short/
├── script.md          → Full script with timing & shot directions
├── index.html         → Interactive animated prototype (open in browser)
├── PRODUCTION-GUIDE.md → This file (you are here)
```

---

## Quick Start Checklist

- [ ] Watch the HTML prototype (open index.html, click Play)
- [ ] Pick your editing tool (CapCut recommended)
- [ ] Download 10-12 stock clips from sources above
- [ ] Find a 60-second trap beat (Uppbeat or Pixabay)
- [ ] Download SFX (cash register, whoosh, notification)
- [ ] Edit following the script.md timeline
- [ ] Add subtitles (auto-generate then style)
- [ ] Color grade warm/golden
- [ ] Export 1080x1920 MP4, 30fps
- [ ] Upload to TikTok with hashtags + optimal time

---

*Total estimated production time: 2-4 hours with stock footage*
