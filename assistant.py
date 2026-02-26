from ai_engine import AIEngine
from commands import handle_command
from config import ASSISTANT_GREETING, EXIT_KEYWORDS, LISTEN_SECONDS
from voice import VoiceEngine


class VoiceAssistant:
    def __init__(self):
        print("Initializing Voice Assistant...")
        self.voice = VoiceEngine()
        self.ai = AIEngine()

    def run(self):
        self.voice.speak(ASSISTANT_GREETING)
        while True:
            try:
                audio_data = self.voice.listen(LISTEN_SECONDS)
                transcript = self.voice.transcribe(audio_data)

                if not transcript or len(transcript) < 2:
                    print("No clear speech detected.")
                    continue

                print(f"You: {transcript}")

                if any(word in transcript.lower() for word in EXIT_KEYWORDS):
                    self.voice.speak("Goodbye!")
                    break

                response, handled = handle_command(transcript)
                if not handled:
                    response = self.ai.generate_response(transcript)

                self.voice.speak(response)
            except KeyboardInterrupt:
                break
            except Exception as exc:
                print(f"Error: {exc}")
                continue


if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
