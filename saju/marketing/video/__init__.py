"""쇼츠 영상(목소리 + 배경음 + 움직이는 화면)을 무료 도구로 만든다.

- 목소리: Supertonic(무료, 내 컴퓨터에서 도는 TTS). 없으면 소리 없이 시간만 맞춘다.
- 배경음: music.py가 직접 만든다(저작권 없음).
- 화면: HTML 틀(talk.html, rank.html)을 Playwright로 한 장씩 찍어 ffmpeg로 잇는다.
API 비용이 들지 않는다.
"""
