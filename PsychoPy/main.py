#!/usr/bin/env python
# -*- coding: latin-1 -*-
import atexit
import codecs
import csv
import random
from os.path import join

import yaml
from psychopy import visual, event, logging, gui, core

from misc.screen_misc import get_screen_res, get_frame_rate


@atexit.register
def save_beh_results():
    """
    Save results of experiment. Decorated with @atexit in order to make sure, that intermediate
    results will be saved even if interpreter will break.
    """
    with open(join('results', PART_ID + '_' + str(random.choice(range(100, 1000))) + '_beh.csv'), 'w',
              encoding='utf-8') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()


def read_text_from_file(file_name, insert=''):
    """
    Method that read message from text file, and optionally add some
    dynamically generated info.
    :param file_name: Name of file to read
    :param insert:
    :return: message
    """
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key='f7'):
    """
    Check (during procedure) if experimentator doesn't want to terminate.
    """
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error(
            'Experiment finished by user! {} pressed.'.format(key))


def abort_with_error(err):
    """
    Call if an error occurred.
    """
    logging.critical(err)
    raise Exception(err)


def show_info(win, file_name, insert=''):
    """
    Clear way to show info message into screen.
    """
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='black', text=msg,
                          height=30, wrapWidth=SCREEN_RES['width'])
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'return', 'space'])
    if key == ['f7']:
        abort_with_error(
            'Experiment finished by user on info screen! F7 pressed.')
    win.flip()

def create_stimuli_list(n):
    """
    In this function we create a list of stimuli.
    x and y - to make a proper number of stimuli of each type
    """
    
    if n%10 != 0:
        abort_with_error('NO_TRIALS must be divisible by 10')
    
    x = int(n*0.2)
    y = int(n*0.1)
    
    stim1 = (['<<<<<', '<<><<', '>>>>>', '>><>>'] * x) + (['OO>OO', 'OO<OO'] * y)

    random.shuffle(stim1)

    return stim1


def training(win, conf, clock, fix_cross, list_of_stimuli, ntt=1):
    """
    This function lets us make a training session, which differs a bit from experimental session.
    feedb - Feedback, which shows to a participant if his/her reactions are correct.
    nnt - an abbreviation for NO_TRAINING_TRIALS
        if ntt = 1 it means that it is first training
        if ntt = 2 it means that it is second training which is shorter than the first one.  
    """
    block_no = 0
    trial_no = 0
    if ntt == 1:
        for trial in range(conf['NO_TRAINING_TRIALS']):
            key_pressed, corr, ctype, stim_type, rt, our_stim = run_trial(win, conf, clock, fix_cross, list_of_stimuli)
            RESULTS.append([PART_ID, trial_no, 'Sesja Treningowa', block_no, ctype, stim_type, key_pressed, rt, corr])

            feedb = 'Poprawnie' if corr else 'Niepoprawnie'
            feedb = visual.TextStim(win, text=feedb, height=conf['TEXT_HEIGHT'], color=conf['FIX_CROSS_COLOR'])
            feedb.draw()
            win.flip()
            core.wait(1)
            win.flip()
    elif ntt == 2:
        for trial in range(conf['NO_TRAINING2_TRIALS']):
            key_pressed, corr, ctype, stim_type, rt, our_stim = run_trial(win, conf, clock, fix_cross, list_of_stimuli)
            RESULTS.append([PART_ID, trial_no, 'Sesja Treningowa 2', block_no, ctype, stim_type, key_pressed, rt, corr])

            feedb = 'Poprawnie' if corr else 'Niepoprawnie'
            feedb = visual.TextStim(win, text=feedb, height=conf['TEXT_HEIGHT'], color=conf['FIX_CROSS_COLOR'])
            feedb.draw()
            win.flip()
            core.wait(1)
            win.flip()


def second_training(win, conf, clock, fix_cross, list_of_stimuli):
    """
    In this part we ask a participant if he/she needs second training session.
    If yes, the function calls training function. If no, we skip to an experimental session
    """
    
    question = visual.TextStim(win, color='black',
                               text='Potrzebujesz jeszcze jednego treningu?\n Wybierz t - tak, n - nie',
                               height=conf['TEXT_HEIGHT'], wrapWidth=SCREEN_RES['width'])
    question.draw()
    win.flip()
    key = event.waitKeys(keyList=['t', 'n'])
    for _ in range(1):
        if key == ['t']:
            training(win, conf, clock, fix_cross, list_of_stimuli, ntt=2)
        elif key == ['n']:
            break


def type_of_stim(our_stim):
    """
    This function returns:
    a) ctype - data if our stimulus is congruent, incongruent or neutral
    b) stim_type - data if our stimulus is a right/left arrow
    """
    if our_stim == '>>>>>' or our_stim == '<<<<<':
        ctype = '1'
    elif our_stim == '>><>>' or our_stim == '<<><<':
        ctype = '2'
    else:
        ctype = '0'

    if our_stim[2] == '>':
        stim_type = 'P'
    elif our_stim[2] == '<':
        stim_type = 'L'
    else:
        stim_type = 'Error'

    return ctype, stim_type


def data_to_be_sent(reaction, stim_type):
    """
    This function:
    a) checks the correctness of the response
    b) returns the rest of the data we need to collect
    """
    key_pressed = reaction[0][0]
    rt = reaction[0][1]

    if ((key_pressed == 'k' or key_pressed == 'K') and stim_type == 'P') or \
            ((key_pressed == 'a' or key_pressed == 'A') and stim_type == 'L'):
        corr = True

    elif ((key_pressed == 'k' or key_pressed == 'K') and stim_type == 'L') or \
            ((key_pressed == 'a' or key_pressed == 'A') and stim_type == 'P'):
        corr = False
    elif ~(key_pressed == 'k') and ~(key_pressed == 'K') \
            and ~(key_pressed == 'a') and ~(key_pressed == 'A'):
        corr = False
    else:
        key_pressed = 'brak'
        corr = False
        rt = -1.0

    return key_pressed, corr, rt


# GLOBALS

RESULTS = list()
RESULTS.append(['Identyfikator', 'Numer proby', 'Sesja', 'Numer bloku', 'Rodzaj bodzca',
                'Bodziec', 'Nacisniety klawisz', 'Czas reakcji', 'Poprawnosc'])


def main():
    global PART_ID

    # === Dialog popup ===
    info = {'IDENTYFIKATOR': ''}
    dictDlg = gui.DlgFromDict(
        dictionary=info, title='Flanker Task - Hobot, Opalinska, Opar')
    if not dictDlg.OK:
        abort_with_error('Info dialog terminated.')

    clock = core.Clock()

    conf = yaml.load(open('config.yaml', encoding='utf-8'), Loader=yaml.Loader)

    # === Scene init ===
    win = visual.Window(list(SCREEN_RES.values()), fullscr=True, monitor="testMonitor",
                        units='pix', color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, win=win)
    FRAME_RATE = get_frame_rate(win)

    if FRAME_RATE != conf['FRAME_RATE']:
        dlg = gui.Dlg(title="Critical error")
        dlg.addText(
            'Wrong no of frames detected: {}. Experiment terminated.'.format(FRAME_RATE))
        dlg.show()
        return None

    PART_ID = info['IDENTYFIKATOR']
    logging.LogFile(join('results', PART_ID + '.log'),
                    level=logging.INFO)  # errors logging
    logging.info('FRAME RATE: {}'.format(FRAME_RATE))
    logging.info('SCREEN RES: {}'.format(SCREEN_RES.values()))

    # === Fixation cross and stimuli ===
    fix_cross = visual.TextStim(win, text='+', height=conf['STIM_HEIGHT'], color=conf['FIX_CROSS_COLOR'])
    stim_list  = [create_stimuli_list(conf['NO_TRIALS']) for _ in range(conf['NO_BLOCKS'])] 
    stim_list_t1 = create_stimuli_list(int(conf['NO_TRAINING_TRIALS']))
    stim_list_t2 = create_stimuli_list(int(conf['NO_TRAINING2_TRIALS']))

    # === Training ===
    show_info(win, join('.', 'messages', 'hello.txt'))
    show_info(win, join('.', 'messages', 'hello2.txt'))
    show_info(win, join('.', 'messages', 'hello3.txt'))
    show_info(win, join('.', 'messages', 'hello4.txt'))

    show_info(win, join('.', 'messages', 'before_training.txt'))
    training(win, conf, clock, fix_cross, stim_list_t1, 1)

    # === Second training ===
    second_training(win, conf, clock, fix_cross, stim_list_t2)

    # === Experiment ===
    show_info(win, join('.', 'messages', 'before_experiment.txt'))

    for block in range(int(conf['NO_BLOCKS'])):
        for trial in range(conf['NO_TRIALS']):
            key_pressed, corr, ctype, stim_type, rt, our_stim = run_trial(win, conf, clock, fix_cross, stim_list[block])
            trial_no = trial + 1
            block_no = block + 1
            RESULTS.append([PART_ID, trial_no, 'Sesja eksperymentalna', block_no, ctype, stim_type,
                            key_pressed, rt, corr])

        show_info(win, join('.', 'messages', 'break.txt'))

    # === Cleaning time ===
    save_beh_results()
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt'))
    win.close()
    core.quit()


def run_trial(win, conf, clock, fix_cross, list_of_stimuli):
    # === Prepare trial-related stimulus ===
    our_stim = list_of_stimuli.pop()
    ctype, stim_type = type_of_stim(our_stim)
    stim = visual.TextStim(win, text=our_stim, height=conf['STIM_HEIGHT'], color=conf['STIM_COLOR'])

    # === Start pre-trial stuff===
    for _ in range(conf['FIX_CROSS_TIME']):
        fix_cross.draw()
        win.flip()

    # === Start trial ===
    event.clearEvents()
    win.callOnFlip(clock.reset)

    for _ in range(conf['STIM_TIME']):
        reaction = event.getKeys(keyList=list(conf['REACTION_KEYS']), timeStamped=clock)
        if reaction:
            key_pressed, corr, rt = data_to_be_sent(reaction, stim_type)
            break
        stim.draw()
        win.flip()

        if reaction:
            timer = clock.getTime()
            rt = timer - reaction[0][1]

        if not reaction:
            key_pressed = 'brak'
            corr = False
            rt = -1.0

    # === Trial ended, prepare data for send  ===
    return key_pressed, corr, ctype, stim_type, rt, our_stim


if __name__ == '__main__':
    PART_ID = ''
    SCREEN_RES = get_screen_res()
    main()
