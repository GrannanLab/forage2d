from psychopy import visual, core, event
from psychopy.event import Mouse
import numpy as np
import os
import pyaudio
import wave
from datetime import datetime
from serial import Serial

class Session:

    def __init__(self, participant_id, nb_boards=10, nb_trials_per_board=7, 
                 time_per_trial=20, trigger_port=None):
        self.win = visual.Window([800, 800], monitor="testMonitor", units="pix", 
                    color='black')
        self.participant_id = participant_id
        self.m = Mouse()
        self.color_schemes = {1: ('gainsboro', 'darkorange', 'chestnut'),
                       2: ('midnightblue', 'linen', 'orchid'),
                       3: ('palegreen', 'tan', 'yellow'),
                       4: ('seagreen', 'salmon', 'plum'),
                       5: ('whitesmoke', 'maroon', 'peru'),
                       6: ('mediumslateblue', 'magenta', 'limegreen'),
                       7: ('honeydew', 'fuchsia', 'dodgerblue'),
                       8: ('red','blue','green'), 
                       9: ('gold', 'lightgreen', 'mistyrose'),
                       10: ('thistle', 'tomato', 'moccasin')}
        self.nb_boards = nb_boards
        self.nb_trials_per_board = nb_trials_per_board
        self.time_per_trial = time_per_trial
        self.results_str = self.get_results_str()
        self.session_clock = core.Clock()
        if trigger_port is not None:
            self.ser = Serial(port=trigger_port, baudrate=50)
        self.trigger_port = trigger_port

    def run_task(self):
        ## start screen
        start_fix = visual.Circle(win=self.win,
                                    size=self.win.size[0]/20,
                                    pos=[0,0],
                                    fillColor='white') 
        text = visual.TextBox2(win=self.win, text="click circle to begin",
                               alignment="center", pos=[0,200])
        start_fix.draw()
        text.draw()
        self.win.flip()
        self.send_trigger()
                
        while True:
            pressed = self.m.getPressed()
            if any(pressed) and start_fix.contains(self.m):
                break
    
        ## run trials 
        board_counter = 1
        while board_counter <= self.nb_boards:
            trial_counter = 1
            while trial_counter <= self.nb_trials_per_board:
                self.send_trigger()
                b = Board(self.win, self.m, self.session_clock, trial_counter,
                        board_counter = board_counter,
                        colors=self.color_schemes[board_counter],
                        results_str=self.results_str)
                trial_timer = core.CountdownTimer(self.time_per_trial)
                while trial_timer.getTime()>0:
                    b.update_trial_data()
                    b.update_targets()
                    core.wait(0.01)
                print("Board {}, trial {} complete".format(board_counter,
                                                            trial_counter))
                b.write_data_buffer_to_file()
                b.write_fixations_to_file()
                trial_counter+=1
                
                ## inter-trial screen
                intertrial_fix = visual.Circle(win=self.win,
                                size=self.win.size[0]/20,
                                pos=[0,100],
                                fillColor='white') 
                exit_fix = visual.Circle(win=self.win,
                                size=self.win.size[0]/20,
                                pos=[0,-200],
                                fillColor='red') 
                intertrial_text = visual.TextBox2(win=self.win, 
                                    text="You earned {} points! Click white circle to continue".format(b.trial_points),
                                    alignment="center", pos=[0,200])
                exit_text = visual.TextBox2(win=self.win, 
                        text="Click red circle to exit".format(b.trial_points),
                        alignment="center", pos=[0,-100])
                intertrial_fix.draw()
                exit_fix.draw()
                intertrial_text.draw()
                exit_text.draw()
                self.win.flip()
                self.send_trigger()

                while True:
                    pressed = self.m.getPressed()
                    if any(pressed) and intertrial_fix.contains(self.m):
                        break
                    if any(pressed) and exit_fix.contains(self.m):
                        self.win.close()
                        core.quit()
            board_counter += 1
        
    def send_trigger(self):
        if self.trigger_port:
            time = self.session_clock.getTime()
            self.ser.write(b'\xFF')
            file_path = self.results_str+"_triggers.txt"
            res_ = '{}\n'.format(time)
            if os.path.isfile(file_path):
                with open(file_path, 'a') as ff:
                    ff.write(res_)
            else:
                with open(file_path, 'w') as ff:
                    ff.write(res_) 
        else:
            return

    def get_results_str(self):
        dt = datetime.now()
        session_str = '{}-{}-{}_{}-{}-{}-{}'.format(self.participant_id,
                dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        session_str = os.path.join('results', session_str)
        return session_str

class Board:
    
    def __init__(self, window, mouse, session_clock, trial_counter, 
                 board_counter = None, nb_targets=16, target_size=30, 
                 colors=('red','blue','green'), 
                 results_str=os.path.join('results','trial_data.txt')):
        self.window = window
        self.mouse = mouse
        assert nb_targets in  [4, 9, 16, 25], "# targets must be a square"
        assert len(colors) == 3, "must use exactly 3 colors"
        self.nb_targets = nb_targets
        self.nb_edge =  np.sqrt(self.nb_targets).astype('int')
        self.target_size = target_size
        self.colors = colors
        self.color_points = {}
        self.set_points()
        self.trial_points = 0
        self.session_clock = session_clock
        self.trial_counter = trial_counter
        self.board_counter = board_counter
        self.trial_data_buffer = []
        self.results_str = results_str
        self.trial_fixations = []
        self.targets = []
        self.p = pyaudio.PyAudio()
        self.initialize()

    def initialize(self):
        # set target locations
        self.set_location_array()

        # set colors
        self.set_color_array()    

        # make targets
        for pos, color in zip(self.location_array, self.color_array): 
            target = visual.Circle(win=self.window,
                                            size=self.window.size[0]/20,
                                            pos=list(pos),
                                            fillColor=color)
            target.points = self.color_points[color]    
            target.draw()                    
            self.targets.append(target)
        self.window.flip()
        self.write_board_params_to_file()

    def update_targets(self):
        for t in self.targets:
            t.draw()
        self.window.flip()

    def set_location_array(self):
        dimx, dimy = self.window.size[0], self.window.size[1]
        x_pos = [np.divide(dimx,(self.nb_edge+1))*(i+1)-np.divide(dimx,2) \
                    for i in range(self.nb_edge)]
        y_pos = [np.divide(dimy,(self.nb_edge+1))*(i+1)-np.divide(dimy,2) \
                    for i in range(self.nb_edge)]
        locs = []
        for x in x_pos:
            for y in y_pos:
                locs.append((x,y))
        self.location_array = locs

    def set_color_array(self):
        nb_per_color = np.floor(np.divide(self.nb_targets, len(self.colors)))
        nb_leftover = np.mod(self.nb_targets, len(self.colors))
        colors = []
        for color in self.colors:
            colors = colors + [color]*int(nb_per_color)
        for i in range(nb_leftover):
            colors = colors + [self.colors[i]]
        colors = np.array(colors)
        np.random.shuffle(colors)
        self.color_array = colors

    def set_points(self):
        self.color_points[self.colors[0]] = 3
        self.color_points[self.colors[1]] = 2
        self.color_points[self.colors[2]] = 1

    def get_points(self, color):
        return self.points['color']

    def get_hovering_status(self): 
        for t in self.targets:
            if t.contains(self.mouse):
                return t
        return None
    
    def write_data_buffer_to_file(self):
        file_path = self.results_str+"_trial_data.txt"
        for res in self.trial_data_buffer:
            res_ = [str(i) for i in res]
            res_ = ','.join(res_)+'\n'
            if os.path.isfile(file_path):
                with open(file_path, 'a') as ff:
                    ff.write(res_)
            else:
                with open(file_path, 'w') as ff:
                    ff.write(res_) 
        self.trial_data_buffer = []

    def write_fixations_to_file(self):
        file_path = self.results_str+"_fixations.txt"
        for res in self.trial_fixations:
            res_ = [str(i) for i in res]
            res_ = ','.join(res_)+'\n'
            if os.path.isfile(file_path):
                with open(file_path, 'a') as ff:
                    ff.write(res_)
            else:
                with open(file_path, 'w') as ff:
                    ff.write(res_) 
        self.trial_fixations = []

    def write_board_params_to_file(self):
        file_path = self.results_str+"_board_parameters.txt"
        trial_ = 'Board{},Trial{}\n'.format(self.board_counter, self.trial_counter)
        loc_ = [str(i) for i in self.location_array]
        loc_ = ','.join(loc_)+'\n'
        col_ = [str(i) for i in self.color_array]
        col_ = ','.join(col_)+'\n'
        if os.path.isfile(file_path):
            with open(file_path, 'a') as ff:
                ff.write(trial_)
                ff.write(loc_)
                ff.write(col_)
        else:
            with open(file_path, 'w') as ff:
                ff.write(trial_)
                ff.write(loc_)
                ff.write(col_)

    def update_trial_data(self):
        time = self.session_clock.getTime()
        mouse_x, mouse_y = self.mouse.getPos()
        hovered_x = -9999
        hovered_y = -9999
        target_hovered = self.get_hovering_status()
        if target_hovered:
            hovered_x, hovered_y = target_hovered.pos[0], target_hovered.pos[1]
        self.trial_data_buffer.append([self.board_counter, self.trial_counter, 
                                       time, mouse_x, mouse_y, 
                                       hovered_x, hovered_y])
        if target_hovered: 
            # check fixation
            if self.check_fixation():
                self.trial_points += target_hovered.points
                self.trial_fixations.append([self.board_counter, 
                                             self.trial_counter, time, 
                                             hovered_x, hovered_y,
                                             target_hovered.points,
                                             self.trial_points])
                audio_path = 'ding{}.wav'.format(target_hovered.points)
                self.targets.remove(target_hovered)
                play_audio(audio_path, self.p)
            
    def check_fixation(self, thresh=0.5):
        # reviews trial_data_buffer to see if fixation has exceeded threshold
        buffer_length = len(self.trial_data_buffer)
        if buffer_length == 0:
            return
        else: 
            time_now = self.trial_data_buffer[-1][2]
            posx_now = self.trial_data_buffer[-1][3]
            posy_now = self.trial_data_buffer[-1][4]
        for i in range(buffer_length):
            time = self.trial_data_buffer[(i+1)*-1][2]
            posx = self.trial_data_buffer[(i+1)*-1][3]
            posy = self.trial_data_buffer[(i+1)*-1][4]
            if (posx == posx_now) and (posy == posy_now):
                if (time_now-time) > thresh:
                    return True
            else: 
                return False  
            
            
def play_audio(f, p, chunk=1024):
    ff = wave.open(f, 'rb')
    stream = p.open(format = p.get_format_from_width(ff.getsampwidth()),
                    channels = ff.getnchannels(),
                    rate = ff.getframerate(),
                    output = True)
    data = ff.readframes(chunk)
    while data:
        stream.write(data)
        data = ff.readframes(chunk)  
    stream.stop_stream()
    stream.close()
    ff.close()

if __name__ == '__main__':

    pid = "test123"
    trigger_port = "COM4"
    s = Session(participant_id=pid, trigger_port=trigger_port)
    s.run_task()