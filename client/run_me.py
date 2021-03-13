#! python3
import sys, os
import argparse
# pleer
from utils.pleer import Pleer, PleerMode

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

# taken from sounddevice example
# simple argument parser
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='output device (numeric ID or substring): music server or sound'
    ' server')
parser.add_argument(
    '-o', '--outfile', type=str, default='/dev/rfcomm0',
    help='device to which output control sequences (serial port)')
parser.add_argument(
    '-m', '--musicdir', type=str, default='sandbox/music/',
    help='music dir containing mono float32 wav files')
parser.add_argument(
    '-b', '--blocksize', type=int, default=2048,
    help='block size (default: %(default)s)')
parser.add_argument(
    '-q', '--buffersize', type=int, default=20,
    help='number of blocks used for buffering (default: %(default)s)')
parser.add_argument(
    '-u', '--loudness', type=float, default=0.5,
    help='how loud music is')
args = parser.parse_args(remaining)
if args.blocksize == 0:
    parser.error('blocksize must not be zero')
if args.buffersize < 1:
    parser.error('buffersize must be at least 1')

# if len(sys.argv) == 1:
#     parser.print_help(sys.stderr)
#     sys.exit(1)

class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self):
        return self.impl()

class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

getch = _Getch()

# reminder for user
actions = {
    " ":  "pause/unpause",
    "<enter>": "stop/play (will start song from beginning)",
    "<S-s>":   "set music for playing (interrupt current song)",
    # TODO: output here v real PleerMode class instances
    "c": "change mode",
    "<arrows>/h/l":  "next/previous song",
    "+/-": "make music louder/more quite",
    "e":  "exit program",
}

def print_help():
    # show on HELP command
    for key, val in actions.items():
        print("'{}'\t- {}".format(key,val))


# if this file is running as main file
if __name__ == "__main__":
    # create instance of pleer (must be only one)
    pleer = Pleer(args.device, args.outfile,
                  PleerMode.SERIAL, args.blocksize,
                  args.loudness)
    # add music folder passed as argument
    pleer.add_folder(args.musicdir)
    print(f'num of songs added {len(pleer.songs)}')

    # pick rundom music and play
    pleer.set_mode(PleerMode.RANDOM)
    # start endless loop and wait for keyboard events
    # (all the actions deticated to pleer are executed on another thread)
    pleer.control()

    # print key bindings
    print_help()

    # created endless circle, now out thread are waiting for event to set
    while True:
        char = getch()
        key_code = ord(char)
        print("\r", end="")   # not output char on screen
        if key_code == 32:      # space - pause/unpause
            print("pausing/unpausing")
            pleer.pause_unpause()
        elif key_code == 13:    # enter key
            print("stop/play song")
            pleer.stop_play()
        elif key_code == 83:    # <S-s> key
            print("set song")
            # output list of songs
            for c, song in enumerate(pleer.songs, start=1):
                print(f"{c}. {song.split('/')[-1]}")
            # -1 becouse counting is from 1
            try:
                song_ind = int(input("choose song to play: ")) - 1
                # play specific song
                pleer.set_ind(song_ind)
            except KeyboardInterrupt:
                pass
        elif key_code == 104:   # 'h' key
            print("previous song...")
            pleer.previous_song()
        elif key_code == 108:   # 'l' key
            print("next song...")
            pleer.next_song()
        elif key_code == 99:    # 'c' key
            pleer.next_mode()
        elif key_code == 45:    # minus sign
            # make music more quite
            pleer.make_more_quite()
        elif key_code == 43:    # plus sign
            # make music louder
            pleer.make_louder()
        # 'q', 'e', <C-c>, and <C-d> chars
        elif key_code == 113 or key_code == 101 or key_code == 3 or key_code == 4:
            print("bye")
            pleer.exit()
            break
        print("{}".format(key_code))
        print("=" * 20)
        print_help()
