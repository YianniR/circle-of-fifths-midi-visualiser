import pygame
import pygame.midi
import pygame.sndarray
import numpy as np
import colorsys
import math

# Constants
WIDTH, HEIGHT = 1000, 800
CIRCLE_WIDTH, CIRCLE_HEIGHT = 800, 800
SIDEBAR_WIDTH = 200
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
LIGHT_BLUE = (173, 216, 230)
SCALE_COLOR = (100, 255, 100)

NOTES = ['C', 'G', 'D', 'A', 'E', 'B', 'F#/Gb', 'C#/Db', 'G#/Ab', 'D#/Eb', 'A#/Bb', 'F']
MIDI_TO_CIRCLE = {0: 0, 1: 7, 2: 2, 3: 9, 4: 4, 5: 11, 6: 6, 7: 1, 8: 8, 9: 3, 10: 10, 11: 5}
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
NATURAL_MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]
HARMONIC_MINOR_SCALE = [0, 2, 3, 5, 7, 8, 11]
PENTATONIC_SCALE = [0, 2, 4, 7, 9]

CHORD_TYPES = {
    (0, 4, 7): "Major",
    (0, 3, 7): "Minor",
    (0, 4, 7, 10): "Dominant 7th",
    (0, 3, 7, 10): "Minor 7th",
    (0, 4, 7, 11): "Major 7th",
    (0, 3, 6): "Diminished",
    (0, 3, 6, 9): "Diminished 7th",
    (0, 4, 8): "Augmented",
    (0, 2, 7): "Sus2",
    (0, 5, 7): "Sus4",
    (0, 4, 7, 9): "6th",
    (0, 3, 7, 9): "Minor 6th",
    (0, 4, 7, 10, 14): "9th",
    (0, 4, 7, 10, 14, 17): "11th",
    (0, 4, 7, 10, 14, 17, 21): "13th"
}

class Button:
    def __init__(self, x, y, width, height, text, color, text_color, toggle=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.toggle = toggle
        self.active = False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color if not self.active else LIGHT_BLUE, self.rect)
        font = pygame.font.Font(None, 24)
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.toggle:
                    self.active = not self.active
                return True
        return False

def setup_midi():
    pygame.midi.init()
    print("Available MIDI devices:")
    for i in range(pygame.midi.get_count()):
        info = pygame.midi.get_device_info(i)
        print(f"Device {i}: {info[1].decode()}, {'Input' if info[2] == 1 else 'Output'}")

    input_id = None
    for i in range(pygame.midi.get_count()):
        info = pygame.midi.get_device_info(i)
        if "APC Key 25" in info[1].decode() and info[2] == 1:  # 1 for input devices
            input_id = i
            break

    if input_id is None:
        print("APC Key 25 not found. Please connect the device and try again.")
        pygame.quit()
        exit()

    return pygame.midi.Input(input_id)

def generate_sine_wave(freq, duration=1.0, volume=0.3):
    sample_rate = 44100
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    wave = np.sin(2 * np.pi * freq * t) * volume
    stereo_wave = np.column_stack((wave, wave))
    return (stereo_wave * 32767).astype(np.int16)

def generate_note_sounds():
    note_sounds = {}
    for midi_note in range(128):
        freq = 440 * (2 ** ((midi_note - 69) / 12))
        sound_array = generate_sine_wave(freq)
        note_sounds[midi_note] = pygame.sndarray.make_sound(sound_array)
    return note_sounds

def note_to_color(note, is_major=True, is_seventh=False):
    hue = (note * 30) % 360 / 360.0
    saturation = 0.7 if is_major else 0.5
    value = 0.9 if not is_seventh else 0.7
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    return (int(r * 255), int(g * 255), int(b * 255))

def recognize_chord(pressed_notes):
    if len(pressed_notes) < 3:
        return None
    
    root = min(pressed_notes)
    intervals = tuple(sorted((note - root) % 12 for note in pressed_notes))
    
    chord_type = CHORD_TYPES.get(intervals, "Complex")
    root_name = NOTES[MIDI_TO_CIRCLE[root % 12]]
    return f"{root_name} {chord_type}", root % 12, chord_type

def get_scale(root, scale_type):
    if scale_type == "Major":
        return [(root + interval) % 12 for interval in MAJOR_SCALE]
    elif scale_type == "Natural Minor":
        return [(root + interval) % 12 for interval in NATURAL_MINOR_SCALE]
    elif scale_type == "Harmonic Minor":
        return [(root + interval) % 12 for interval in HARMONIC_MINOR_SCALE]
    elif scale_type == "Pentatonic":
        return [(root + interval) % 12 for interval in PENTATONIC_SCALE]
    return []

def draw_circle_of_fifths(screen, pressed_notes, chord_info, scale_root, scale_type, show_note_names):
    screen.fill(BLACK)
    center = (CIRCLE_WIDTH // 2, CIRCLE_HEIGHT // 2)
    radius = min(CIRCLE_WIDTH, CIRCLE_HEIGHT) // 2 - 50

    if chord_info:
        chord_name, root_note, chord_type = chord_info
        is_major = "Major" in chord_type or "Augmented" in chord_type or "Dominant" in chord_type
        is_seventh = "7th" in chord_type or "9th" in chord_type or "11th" in chord_type or "13th" in chord_type
        highlight_color = note_to_color(root_note, is_major, is_seventh)
        line_color = highlight_color
    else:
        highlight_color = WHITE
        line_color = WHITE

    scale_notes = get_scale(scale_root, scale_type) if scale_root is not None else []
    pressed_positions = []

    for i, note in enumerate(NOTES):
        angle = i * (2 * math.pi / 12) - math.pi / 2
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        
        color = highlight_color if note in pressed_notes else SCALE_COLOR if i in scale_notes else GRAY
        pygame.draw.circle(screen, color, (int(x), int(y)), 30)
        
        font = pygame.font.Font(None, 28)
        text = font.render(note if show_note_names else "", True, BLACK)
        text_rect = text.get_rect(center=(int(x), int(y)))
        screen.blit(text, text_rect)

        if note in pressed_notes:
            pressed_positions.append((x, y))

    if len(pressed_positions) > 1:
        pygame.draw.lines(screen, line_color, True, pressed_positions, 2)

    if chord_info:
        font = pygame.font.Font(None, 36)
        text = font.render(chord_info[0], True, WHITE)
        text_rect = text.get_rect(center=(CIRCLE_WIDTH // 2, CIRCLE_HEIGHT // 2))
        screen.blit(text, text_rect)

    if scale_root is not None:
        scale_name = f"{NOTES[MIDI_TO_CIRCLE[scale_root]]} {scale_type} Scale"
        font = pygame.font.Font(None, 30)
        text = font.render(scale_name, True, SCALE_COLOR)
        text_rect = text.get_rect(center=(CIRCLE_WIDTH // 2, CIRCLE_HEIGHT - 30))
        screen.blit(text, text_rect)

def draw_sidebar(screen, buttons):
    pygame.draw.rect(screen, GRAY, (CIRCLE_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT))
    for button in buttons:
        button.draw(screen)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Circle of Fifths MIDI Visualizer")

    midi_input = setup_midi()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2**12)
    note_sounds = generate_note_sounds()

    buttons = [
        Button(CIRCLE_WIDTH + 10, 50, 180, 40, "Toggle Scale Highlight", WHITE, BLACK, toggle=True),
        Button(CIRCLE_WIDTH + 10, 100, 180, 40, "Toggle Note Names", WHITE, BLACK, toggle=True),
        Button(CIRCLE_WIDTH + 10, 150, 180, 40, "Major Scale", WHITE, BLACK, toggle=True),
        Button(CIRCLE_WIDTH + 10, 200, 180, 40, "Natural Minor Scale", WHITE, BLACK, toggle=True),
        Button(CIRCLE_WIDTH + 10, 250, 180, 40, "Harmonic Minor Scale", WHITE, BLACK, toggle=True),
        Button(CIRCLE_WIDTH + 10, 300, 180, 40, "Pentatonic Scale", WHITE, BLACK, toggle=True),
    ]

    running = True
    pressed_midi_notes = set()
    pressed_circle_notes = set()
    active_sounds = {}
    scale_root = None
    scale_type = "Major"
    show_scale = False
    show_note_names = False

    print("Visualizer is running. Play notes on your MIDI device to see and hear them.")
    print("Close the window to exit.")

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            for button in buttons:
                if button.handle_event(event):
                    if button.text == "Toggle Scale Highlight":
                        show_scale = button.active
                    elif button.text == "Toggle Note Names":
                        show_note_names = button.active
                    elif "Scale" in button.text:
                        scale_type = button.text.replace(" Scale", "")
                        for b in buttons[2:]:
                            if b != button:
                                b.active = False

        if midi_input.poll():
            midi_events = midi_input.read(10)
            for event in midi_events:
                status = event[0][0] & 0xF0
                note = event[0][1]
                velocity = event[0][2]
                
                if status == 0x90 and velocity > 0:  # Note On
                    pressed_midi_notes.add(note)
                    note_index = MIDI_TO_CIRCLE[note % 12]
                    note_name = NOTES[note_index]
                    pressed_circle_notes.add(note_name)
                    if note not in active_sounds:
                        note_sounds[note].play(-1)  # Play indefinitely
                        active_sounds[note] = note_sounds[note]
                    print(f"Note On: MIDI {note}, Mapped to {note_name}")
                    if len(pressed_midi_notes) == 1:
                        scale_root = note % 12
                elif status == 0x80 or (status == 0x90 and velocity == 0):  # Note Off
                    pressed_midi_notes.discard(note)
                    note_index = MIDI_TO_CIRCLE[note % 12]
                    note_name = NOTES[note_index]
                    pressed_circle_notes.discard(note_name)
                    if note in active_sounds:
                        active_sounds[note].stop()
                        del active_sounds[note]
                    print(f"Note Off: MIDI {note}, Mapped to {note_name}")
                    if len(pressed_midi_notes) == 0:
                        scale_root = None

        chord_info = recognize_chord(pressed_midi_notes)
        draw_circle_of_fifths(screen, pressed_circle_notes, chord_info, 
                              scale_root if show_scale else None, 
                              scale_type, show_note_names)
        draw_sidebar(screen, buttons)
        pygame.display.flip()

    # Cleanup
    for sound in active_sounds.values():
        sound.stop()
    midi_input.close()
    pygame.midi.quit()
    pygame.quit()

if __name__ == "__main__":
    main()