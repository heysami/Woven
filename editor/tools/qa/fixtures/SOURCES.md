# QA detection fixtures

Stock images used by `../synthetic-input-qa.html` to mock the camera so the
vision nodes (hand / face / OCR) can be verified headlessly - no real webcam or
human needed. Each is drawn into a moving canvas → `captureStream()` and swapped
in for `getUserMedia`, so MediaPipe runs on a real, detectable image.

| File | Subject | Source | License |
|------|---------|--------|---------|
| `hand_pointing.jpg` | a hand pointing up | MediaPipe public assets (`storage.googleapis.com/mediapipe-assets/pointing_up.jpg`) | Apache-2.0 |
| `hand_thumb.jpg` | a thumbs-up hand | MediaPipe public assets (`thumb_up.jpg`) | Apache-2.0 |
| `face_portrait.jpg` | a face portrait | MediaPipe public assets (`portrait.jpg`) | Apache-2.0 |

These are Google MediaPipe's own task test assets, chosen because they are
reliably detected by HandLandmarker / FaceLandmarker. Verified detectable:
`hand_pointing.jpg` → gesture `point`, `face_portrait.jpg` → face present.

The OCR fixture is generated procedurally (canvas text "HELLO"), no file needed.
