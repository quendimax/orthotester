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

# pylint: disable=missing-docstring

import os
import re
import sys
import time
import random
import argparse
import datetime
import traceback


__author__ = 'Maksim Tomkowicz'


PARSER = argparse.ArgumentParser(description='Helper for training for central testing')
PARSER.add_argument('input', nargs='+', type=str, help='the list of test files')
PARSER.add_argument('--check', action='store_true', help='just check all tests for correct (it ignores -n)')
PARSER.add_argument('--no-random', action='store_true', help='switch off random of tests')
PARSER.add_argument('-n', '--number-of-tests', type=int, metavar='N', default=0,
                    help='how many tests you want to pass. 0 means every test.')
CONFIG = PARSER.parse_args()


class AnswerStatistic:

    def __init__(self):
        self.right = 0
        self.wrong = 0
        self.quantity = 0
        self.all = 0
        self.done = 0
        self.time = 0.0


ANSWER_STAT = AnswerStatistic()


# enable ANSI escape sequences support in Windows
if sys.platform == 'win32':
    os.system('color')


class TextProp:
    HIGHLIGHT = '\x1b[4;31m'
    COMMENT = '\x1b[34m'
    RIGHT = '\x1b[1;32m'   # bold green
    WRONG = '\x1b[1;31m'   # bold red
    NORMAL = '\x1b[0m'
    BOLD = '\x1b[1m'


def parse_sentence(sentence, snaps):
    original = ''
    question = ''
    cur_pos = 0
    for snap in snaps:
        original += sentence[cur_pos:snap[0]]
        question += sentence[cur_pos:snap[0]]
        word = sentence[snap[0]:snap[1]].strip('[]')
        if (i := word.find(':')) != -1:
            original += word[:i].strip()
            question += '...' + TextProp.COMMENT + '(' + word[i+1:].strip() + ')' + TextProp.NORMAL
        else:
            original += word
            question += '_'
        cur_pos = snap[1]
    original += sentence[cur_pos:]
    question += sentence[cur_pos:]
    return original, question


def read_answer(comment=''):
    answer = input(comment)
    return answer.strip()


def print_comment(comment):
    if comment:
        message = '    ' + TextProp.COMMENT + '(' + comment + ')' + TextProp.NORMAL
        print(message)
    else:
        print()


def print_right():
    msg = ' ---> ' + TextProp.RIGHT + 'Right' + TextProp.NORMAL
    print(msg)


def print_wrong(right_answer, wrong_position, answer_marks, right_marks):
    msg = ' ---> ' + TextProp.WRONG + 'Wrong' + (' ' * wrong_position) + answer_marks + TextProp.NORMAL
    print(msg)
    msg = ' ---> Right:  ' + TextProp.BOLD + right_answer + TextProp.NORMAL
    print(msg)
    msg = '              ' + TextProp.RIGHT + right_marks + TextProp.NORMAL
    print(msg)


def get_diff(answer, right):
    matrix = []
    for _ in range(len(answer) + 1):
        matrix.append([0] * (len(right) + 1))

    for i, answer_char in enumerate(answer):
        for j, right_char in enumerate(right):
            if answer_char == right_char:
                matrix[i + 1][j + 1] = matrix[i][j] + 1
            else:
                matrix[i + 1][j + 1] = max(matrix[i][j + 1], matrix[i + 1][j])

    answer_marks = ''
    right_marks = ''
    i = len(answer)
    j = len(right)
    while i > 0 or j > 0:
        if i > 0 and j > 0 and answer[i - 1] == right[j - 1]:
            answer_marks = ' ' + answer_marks
            right_marks = ' ' + right_marks
            i, j = i - 1, j - 1
        elif i > 0 and (j == 0 or matrix[i - 1][j] >= matrix[i][j - 1]):
            answer_marks = '-' + answer_marks
            i -= 1
        elif j > 0 and (i == 0 or matrix[i - 1][j] < matrix[i][j - 1]):
            right_marks = '+' + right_marks
            j -= 1

    return answer_marks, right_marks


def check_answer(answer, right_answer, extra_indent=0):
    if answer != right_answer:
        answer_marks, right_marks = get_diff(answer, right_answer)
        print_wrong(right_answer, extra_indent, answer_marks, right_marks)
        return False
    print_right()
    return True


def read_test_words(file_name):
    lines = []
    comment_checker = re.compile(r'^\s*#')
    empty_checker = re.compile(r'^\s*$')
    description = ''
    with open(file_name, 'rt', encoding='utf-8') as fd:
        the_first_line = True
        for line in fd.readlines():
            if the_first_line and comment_checker.match(line):
                description += line.lstrip(' \t#')
            else:
                the_first_line = False
            if comment_checker.match(line) or empty_checker.match(line):
                continue
            line_comment = line.split('#', 1)
            line, comment = line_comment if len(line_comment) == 2 else (line_comment[0], '')
            lines.append((line.strip(), comment.strip()))
    return lines, description


def get_random_lines(lines, random_on=True):
    if CONFIG.number_of_tests == 0:
        CONFIG.number_of_tests = len(lines)
    else:
        CONFIG.number_of_tests = min(CONFIG.number_of_tests, len(lines))

    if random_on:
        rand = random.SystemRandom()
        lines = rand.sample(lines, CONFIG.number_of_tests)
    else:
        lines = lines[:CONFIG.number_of_tests]
    return lines


def check_test(func):
    if CONFIG.check:
        return lambda word, comment='': True
    return func


@check_test
def test_with_gaps(test_word, comment=''):
    checker = re.compile(r'\[[^\[\]|]*]')
    exclusions = [m.span() for m in checker.finditer(test_word)]

    orig_word, quest_word = parse_sentence(test_word, exclusions)

    print('Question:     %s' % quest_word, end='')
    print_comment(comment)
    answer = read_answer('Your answer:  ')
    return check_answer(answer, orig_word, 3)


@check_test
def test_with_choice(line, comment=''):
    if comment:
        comment = TextProp.COMMENT + ' ({})'.format(comment) + TextProp.NORMAL
    print('Choose right variant{}:'.format(comment))
    checker = re.compile(r'[^\[\]|]+')
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
    return check_answer(answer, right_answer)


@check_test
def test_with_small_choice(test_word, comment=''):
    checker = re.compile(r'\[[^\[\]]+]')
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
        quest_word += TextProp.HIGHLIGHT + '/'.join(letters) + TextProp.NORMAL
        cur = j
    orig_word += test_word[cur:]
    quest_word += test_word[cur:]

    print('Question:     %s' % quest_word, end='')
    print_comment(comment)
    answer = read_answer('Your answer:  ')
    return check_answer(answer, orig_word, 3)


@check_test
def test_with_stress(test_word, comment=''):
    test_word = test_word.strip()
    checker = re.compile(r'([аоыэуяёіею])ʼ')
    quest_word = ''.join(checker.split(test_word))
    orig_word = test_word
    print('Put the stress: {}'.format(quest_word), end='')
    print_comment(comment)
    answer = read_answer('Your answer:    ')
    return check_answer(answer, orig_word, 5)


@check_test
def test_with_translation(line, comment=''):
    checker = re.compile(r'->')
    match = checker.search(line)
    if match:
        orig_word = line[:match.span()[0]].strip()
        translation = line[match.span()[1]:].strip()
    else:
        raise SyntaxError("cannot find `->` in the sentence: %s" % line)

    print('Translate:   {}'.format(orig_word), end='')
    print_comment(comment)
    answer = read_answer('Your answer: ')
    return check_answer(answer, translation, 2)


def print_results():
    elapsed_time = datetime.timedelta(seconds=time.time() - ANSWER_STAT.time)
    print('=' * 80)
    print('Done {} tests from {}'.format(ANSWER_STAT.done, ANSWER_STAT.quantity))
    print('Elapsed time: {}'.format(elapsed_time))
    print('\nRight answers: {:d} ({:.1%})'.format(ANSWER_STAT.right, ANSWER_STAT.right / ANSWER_STAT.done))
    print('Wrong answers: {:d} ({:.1%})'.format(ANSWER_STAT.wrong, ANSWER_STAT.wrong / ANSWER_STAT.done))
    print('=' * 80)


def main():
    print('=' * 80)
    lines = []
    for file_input in CONFIG.input:
        cur_lines, description = read_test_words(file_input)
        lines += cur_lines
        description = '* ' + description.strip('\n').replace('\n', '\n  ')
        print(description)

    ANSWER_STAT.right = 0
    ANSWER_STAT.wrong = 0
    ANSWER_STAT.done = 0
    ANSWER_STAT.all = len(lines)

    if not CONFIG.check:
        lines = get_random_lines(lines, random_on=not CONFIG.no_random)
    ANSWER_STAT.quantity = len(lines)

    print('Starting of {n} tests from {all}'.format(n=ANSWER_STAT.quantity, all=ANSWER_STAT.all))
    print('=' * 80)

    gaps_checker = re.compile(r'\[[^\[\]|]*]')
    small_choice_checker = re.compile(r'\[[^\[\]]+]')
    stress_checker = re.compile(r'[аоыэуяёіею]ʼ')
    translate_checker = re.compile(r'->')
    ANSWER_STAT.time = time.time()

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
        ANSWER_STAT.right += int(is_right)
        ANSWER_STAT.wrong += int(not is_right)
        ANSWER_STAT.done += 1
        if not CONFIG.check:
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
