#!/usr/bin/env python3

# A little program for testing orthography knowledge.
# Copyright (C) 2015  Maksim Tomkowicz
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


__author__ = 'Maksim Tomkowicz'


import re
import sys
import time
import random
import argparse
import datetime
import traceback


parser = argparse.ArgumentParser(description='Helper for training for central testing')
parser.add_argument('input', nargs='+', type=str, help='the list of test files')
parser.add_argument('--check', action='store_true', help='just check all tests for correct (it ignores -n)')
parser.add_argument('--no-random', action='store_true', help='switch off random of tests')
parser.add_argument('-n', '--number-of-tests', type=int, metavar='N', default=0,
                    help='how many tests you want to pass. 0 means every test.')
config = parser.parse_args()


class AnswerStatistic:

    def __init__(self):
        self.right = 0
        self.wrong = 0
        self.quantity = 0
        self.all = 0
        self.done = 0
        self.time = 0


answer_stat = AnswerStatistic()

HIGHLIGHT_TEXT = '\x1b[4;31m'
COMMENT_TEXT = '\x1b[34m'
RIGHT_TEXT = '\x1b[1;32m'   # bold green
WRONG_TEXT = '\x1b[1;31m'   # bold red
NORMAL_TEXT = '\x1b[0m'
BOLD_TEXT = '\x1b[1m'


def get_original_word(line, exclusions):
    orig_word = ''
    cur_pos = 0
    for exclusion in exclusions:
        orig_word += line[cur_pos:exclusion[0]]
        excl_str = line[exclusion[0]:exclusion[1]].strip('[]')
        orig_word += excl_str
        cur_pos = exclusion[1]
    orig_word += line[cur_pos:]
    return orig_word


def get_quest_word(line, exclusions):
    orig_word = ''
    cur_pos = 0
    for exclusion in exclusions:
        orig_word += line[cur_pos:exclusion[0]]
        orig_word += '_'
        cur_pos = exclusion[1]
    orig_word += line[cur_pos:]
    return orig_word


def read_answer(comment=''):
    answer = input(comment)
    return answer.strip()


def print_comment(comment):
    if comment:
        message = '    ' + COMMENT_TEXT + '(' + comment + ')' + NORMAL_TEXT
        print(message)
    else:
        print()


def print_right():
    msg = ' ---> ' + RIGHT_TEXT + 'Right' + NORMAL_TEXT
    print(msg)


def print_wrong(right_answer):
    msg = ' ---> ' + WRONG_TEXT + 'Wrong' + NORMAL_TEXT
    print(msg)
    msg = ' ---> Right answer: ' + BOLD_TEXT + right_answer + NORMAL_TEXT
    print(msg)


def read_test_words(file_name):
    lines = []
    comment_checker = re.compile(r'^\s*#')
    empty_checker = re.compile(r'^\s*$')
    description = ''
    with open(file_name, 'rt', encoding='utf-8') as f:
        the_first_line = True
        for line in f.readlines():
            if the_first_line and comment_checker.match(line):
                description += line.lstrip(' \t#')
            else:
                the_first_line = False
            if comment_checker.match(line)\
                    or empty_checker.match(line):
                continue
            line_comment = line.split('#', 1)
            line, comment = line_comment if len(line_comment) == 2 else (line_comment[0], '')
            lines.append((line.strip(), comment.strip()))
    return lines, description


def get_random_lines(lines, random_on=True):
    if config.number_of_tests == 0:
        config.number_of_tests = len(lines)
    else:
        config.number_of_tests = min(config.number_of_tests, len(lines))

    if random_on:
        rand = random.SystemRandom()
        lines = rand.sample(lines, config.number_of_tests)
    else:
        lines = lines[:config.number_of_tests]
    return lines


def check_test(func):
    if config.check:
        return lambda word, comment='': True
    else:
        return func


@check_test
def test_with_gaps(test_word, comment=''):
    checker = re.compile(r'\[[^\[\]\|]*\]')
    exclusions = [m.span() for m in checker.finditer(test_word)]

    orig_word = get_original_word(test_word, exclusions)
    quest_word = get_quest_word(test_word, exclusions)

    print('Question:     %s' % quest_word, end='')
    print_comment(comment)
    answer = read_answer('Your answer:  ')
    if answer == orig_word:
        print_right()
        return True
    else:
        print_wrong(orig_word)
        return False


@check_test
def test_with_choice(line, comment=''):
    if comment:
        comment = COMMENT_TEXT + ' ({})'.format(comment) + NORMAL_TEXT
    print('Choose right variant{}:'.format(comment))
    checker = re.compile(r'[^\[\]\|]+')
    answers = [line[m.span()[0]:m.span()[1]].strip() for m in checker.finditer(line)]
    right_answer = answers[0]
    random.shuffle(answers)
    for i, answer in enumerate(answers):
        print('{}. {}'.format(i+1, answer))
    answer = read_answer('Your answer: ')
    try:
        answer = answers[int(answer) - 1]
    except ValueError:
        pass
    if answer == right_answer:
        print_right()
        return True
    else:
        print_wrong(right_answer)
        return False


@check_test
def test_with_small_choice(test_word, comment=''):
    checker = re.compile(r'\[[^\[\]]+\]')
    exclusions = [m.span() for m in checker.finditer(test_word)]

    orig_word = ''
    quest_word = ''
    cur = 0
    for i, j in exclusions:
        orig_word += test_word[cur:i]
        quest_word += test_word[cur:i]
        letters = test_word[i:j].strip('[]').split('|')
        orig_word += letters[0]
        random.shuffle(letters)
        quest_word += HIGHLIGHT_TEXT + '/'.join(letters) + NORMAL_TEXT
        cur = j
    orig_word += test_word[cur:]
    quest_word += test_word[cur:]

    print('Question:     %s' % quest_word, end='')
    print_comment(comment)
    answer = read_answer('Your answer:  ')
    if answer == orig_word:
        print_right()
        return True
    else:
        print_wrong(orig_word)
        return False


@check_test
def test_with_stress(test_word, comment=''):
    test_word = test_word.strip()
    checker = re.compile(r'([аоыэуяёіею])ʼ')
    quest_word = ''.join(checker.split(test_word))
    orig_word = test_word
    print('Put the stress: {}'.format(quest_word), end='')
    print_comment(comment)
    answer = read_answer('Your answer:    ')
    if answer == orig_word:
        print_right()
        return True
    else:
        print_wrong(orig_word)
        return False


@check_test
def test_with_translation(line, comment=''):
    checker = re.compile(r'->')
    match = checker.search(line)
    orig_word = line[:match.span()[0]].strip()
    translation = line[match.span()[1]:].strip()

    print('Translate:  {}'.format(orig_word), end='')
    print_comment(comment)
    answer = read_answer('You answer: ')
    if answer == translation:
        print_right()
        return True
    else:
        print_wrong(translation)
        return False


def print_results():
    elapsed_time = datetime.timedelta(seconds=time.time()-answer_stat.time)
    print()
    print('=' * 80)
    print('Done {} tests from {}'.format(answer_stat.done, answer_stat.quantity))
    print('Elapsed time: {}'.format(elapsed_time))
    print('\nRight answers: {:d} ({:.1%})'.format(answer_stat.right, answer_stat.right / answer_stat.done))
    print('Wrong answers: {:d} ({:.1%})'.format(answer_stat.wrong, answer_stat.wrong / answer_stat.done))
    print('=' * 80)


def main():
    print('=' * 80)
    lines = []
    for file_input in config.input:
        cur_lines, description = read_test_words(file_input)
        lines += cur_lines
        description = '* ' + description.strip('\n').replace('\n', '\n  ')
        print(description)

    answer_stat.right = 0
    answer_stat.wrong = 0
    answer_stat.done = 0
    answer_stat.all = len(lines)

    if not config.check:
        lines = get_random_lines(lines, random_on=not config.no_random)
    answer_stat.quantity = len(lines)

    print('Starting of {n} tests from {all}'.format(n=answer_stat.quantity, all=answer_stat.all))
    print('=' * 80)

    gaps_checker = re.compile(r'\[[^\[\]\|]*\]')
    small_choice_checker = re.compile(r'\[[^\[\]\|]+\|[^\[\]\|]+\]')
    stress_checker = re.compile(r'[аоыэуяёіею]ʼ')
    translate_checker = re.compile(r'->')
    answer_stat.time = time.time()

    for line, comment in lines:
        if gaps_checker.search(line):
            is_right = test_with_gaps(line, comment)
        elif '[' not in line and ']' not in line and '|' in line:
            is_right = test_with_choice(line, comment)
        elif small_choice_checker.search(line):
            is_right = test_with_small_choice(line, comment)
        elif stress_checker.search(line):
            is_right = test_with_stress(line, comment)
        elif translate_checker.search(line):
            is_right = test_with_translation(line, comment)
        else:
            raise Exception('Unknown test: "{}"'.format(line))
        answer_stat.right += int(is_right)
        answer_stat.wrong += int(not is_right)
        answer_stat.done += 1
        if not config.check:
            print('_' * 80, end='\n\n')

    print_results()


if __name__ == '__main__':
    try:
        main()
    except UnicodeEncodeError:
        traceback.print_exc()
        print('\n\nPlease! Launch command "chcp 1251" before the program is started\n')
        sys.exit(1)
    except KeyboardInterrupt:
        print_results()
        sys.exit(0)
