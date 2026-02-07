# Complete Frontend Testing Guide

## ✅ Good News!

Your frontend is **already configured correctly**:
- ✅ API URL: `http://localhost:8001` 
- ✅ WebSocket URL: `ws://localhost:8001`
- ✅ Endpoints match: `/session/start`, `/session/{id}/live`, `/session/{id}/video`
- ✅ Video format: Base64 data URLs (already supported by microservice)

## 🚀 Step-by-Step Testing

### Step 1: Start the Microservice

**Open Terminal 1 (PowerShell):**

```powershell
# Navigate to Gemini_Engine directory
cd C:\Users\Ameya\Documents\hackathons\iitgn\ai-interviewer\Gemini_Engine

# Activate virtual environment (if using one)
.venv\Scripts\Activate.ps1

# Start the microservice
uvicorn live_interview_service.service:app --host 0.0.0.0 --port 8001 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### Step 2: Serve the Frontend

**Open Terminal 2 (PowerShell):**

```powershell
# Navigate to frontend_client directory
cd C:\Users\Ameya\Documents\hackathons\iitgn\ai-interviewer\Gemini_Engine\frontend_client

# Start a simple HTTP server
python -m http.server 8080
```

**Expected output:**
```
Serving HTTP on 0.0.0.0 port 8080 (http://0.0.0.0:8080/) ...
```

### Step 3: Open the Frontend in Browser

1. Open your browser (Chrome, Edge, or Firefox)
2. Navigate to: **`http://localhost:8080/live_interview.html`**

### Step 4: Fill Out the Form

In the browser, you'll see a setup form. Fill it out:

- **Candidate ID**: `test-candidate-001` (or any ID)
- **Job ID**: `test-job-001` (or any ID)
- **Job Description**: 
  ```
  We are looking for a Software Engineer with experience in Python, React, and cloud technologies. 
  The ideal candidate should have 3+ years of experience building scalable web applications.
  ```
- **Skills**: `Python, JavaScript, React, Node.js, AWS`
- **Education**: `BS Computer Science, State University, 2020`
- **LeetCode Profile**: `https://leetcode.com/testuser`
- **Projects**: Click "+ Add Another Project" and add:
  - Description: `Built a real-time chat application using React and WebSocket`
  - Technologies: `React, Node.js, WebSocket`

### Step 5: Start the Interview

1. Click the **"Start Live Interview"** button
2. The browser will ask for:
   - **Microphone permission** → Click "Allow"
   - **Camera permission** → Click "Allow"

### Step 6: What to Expect

Once started, you should see:

1. **Connection Status**: Green dot in header (connected)
2. **Timer**: Starts counting (00:00, 00:01, ...)
3. **AI Avatar**: Large circle with AI icon
4. **Audio Visualizer**: 7 bars animating
5. **Your Video**: Webcam feed in the right sidebar
6. **Status Log**: "Session initialized" message

### Step 7: Test Audio

1. **Speak into your microphone**
2. You should see:
   - Audio visualizer bars moving
   - Status text changing to "Zenith Speaking..." when AI responds
   - **Captions box** at bottom showing AI's questions/text

### Step 8: Test Video Proctoring

1. **Look away from the screen** for 5+ seconds
2. You should see:
   - **Red alert overlay** on your video
   - **Status log entry** with violation message
   - **Camera status indicator** turns red

### Step 9: End the Interview

1. Click the **red "End" button** (phone icon) in the footer
2. The frontend will:
   - Close WebSocket connections
   - Call the end session endpoint
   - Show the results page

### Step 10: View Results

You should see:
- **Overall Score**: X/10
- **Technical Score**: X/10
- **Communication Score**: X/10
- **Recommendation**: "hire", "strong_hire", etc.
- **Full Transcript**: All questions and answers

## 🔍 Verification Checklist

### Before Starting
- [ ] Microservice running on port 8001
- [ ] Frontend server running on port 8080
- [ ] Browser can access `http://localhost:8080/live_interview.html`
- [ ] Browser can access `http://localhost:8001/health` (test in new tab)

### During Interview
- [ ] Form submission works
- [ ] WebSocket connections establish (check browser console F12)
- [ ] Microphone permission granted
- [ ] Camera permission granted
- [ ] Audio visualizer shows activity
- [ ] Video feed appears
- [ ] AI transcript appears in captions
- [ ] Proctoring alerts appear (if violations)

### After Ending
- [ ] Results page displays
- [ ] Scores are shown
- [ ] Transcript is displayed
- [ ] `output.json` file created in microservice directory

## 🐛 Troubleshooting

### "Failed to start" Error

**Check:**
1. Is microservice running? Test: `curl http://localhost:8001/health`
2. Open browser console (F12) → Look for errors
3. Check microservice terminal for error messages

### WebSocket Connection Failed

**Check:**
1. Microservice is running
2. No firewall blocking port 8001
3. Browser console shows WebSocket errors
4. Try refreshing the page

### Audio Not Working

**Check:**
1. Microphone permission granted
2. Microphone is not muted in system
3. Browser console for errors
4. Check microservice logs

### Video Not Working

**Check:**
1. Camera permission granted
2. Camera is not in use by another app
3. Browser console for errors
4. Proctoring module available (check microservice logs)

### CORS Errors

The microservice has CORS enabled, but if you see errors:
- Make sure you're accessing via `http://localhost:8080` (not `file://`)
- Check microservice logs for CORS issues

## 📊 Browser Console Commands

Open browser console (F12) and you can check:

```javascript
// Check WebSocket connections
console.log(state.wsAudio?.readyState);  // Should be 1 (OPEN)
console.log(state.wsVideo?.readyState);  // Should be 1 (OPEN)

// Check session ID
console.log(state.sessionId);

// Check transcript
console.log(state.transcript);
```

## 🎯 Expected Console Output

When everything works, you should see in browser console:
```
Audio WS connected
Video WS connected
```

And in microservice terminal:
```
[Live] Connecting to model gemini-2.5-flash-native-audio-preview-12-2025
[Service] Saved interview output to: ...
```

## 📝 Quick Test Without Full Interview

If you want to test just the endpoints without the full interview:

1. Open browser console (F12)
2. Run:
```javascript
// Test session start
fetch('http://localhost:8001/session/start', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        candidate_id: 'test',
        job_id: 'test',
        job_description: 'Test job'
    })
}).then(r => r.json()).then(console.log);
```

## ✅ Success Indicators

You'll know everything works when:
1. ✅ Form submits without errors
2. ✅ WebSocket connections show "connected" status
3. ✅ Audio visualizer animates when you speak
4. ✅ AI responses appear in captions
5. ✅ Video feed shows your webcam
6. ✅ Proctoring alerts appear (if you look away)
7. ✅ End session shows results
8. ✅ `output.json` file is created

## 🎉 You're Ready!

Everything is configured correctly. Just:
1. Start microservice
2. Serve frontend
3. Open in browser
4. Start interviewing!

The frontend and microservice are fully compatible! 🚀
