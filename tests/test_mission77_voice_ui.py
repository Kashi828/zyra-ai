
from pathlib import Path

def test_voice_ui_controls_exist():
    html = Path("desktop/index.html").read_text()
    assert 'id="voiceButton"' in html
    assert 'id="voiceStart"' in html
    assert 'id="voiceStop"' in html
    assert 'id="voiceLanguage"' in html
    assert 'id="voicePanel"' in html

def test_voice_ui_uses_standard_speech_recognition():
    js = Path("desktop/app.js").read_text()
    assert "SpeechRecognition" in js
    assert "webkitSpeechRecognition" in js
    assert "recognition.onresult" in js
    assert 'voiceLanguage' in js

def test_voice_ui_keeps_transcript_in_existing_goal():
    js = Path("desktop/app.js").read_text()
    assert '$("goal").value' in js
    assert 'review before running' in js
