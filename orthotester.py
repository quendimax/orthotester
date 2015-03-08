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


class AnswerStatistic:

    def __init__(self):
        self.right = 0
        self.wrong = 0
        self.quantity = 0
        self.all = 0
        self.done = 0
        self.time = 0


config = None
answer_stat = AnswerStatistic()


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
        excl_str = line[exclusion[0]:exclusion[1]].strip('[]')
        orig_word += '_' * max(len(excl_str), 1)
        cur_pos = exclusion[1]
    orig_word += line[cur_pos:]
    return orig_word


def read_test_words(file_name, random_on=True):
    lines = []
    comment_checker = re.compile(r'^\s*#')
    empty_checker = re.compile(r'^\s*$')
    description = ''
    with open(file_name, 'rt', encoding='utf-8') as f:
        the_first_line = True
        for line in f.readlines():
            if the_first_line and comment_checker.match(line):
                description += line.strip(' \t').strip('#')
            else:
                the_first_line = False
            if comment_checker.match(line)\
                    or empty_checker.match(line):
                continue
            lines.append(line.strip())
    answer_stat.all = len(lines)

    if config.number_of_tests == 0:
        config.number_of_tests = len(lines)
    else:
        config.number_of_tests = min(config.number_of_tests, len(lines))

    if random_on:
        rand = random.SystemRandom()
        lines = rand.sample(lines, config.number_of_tests)
    return lines, description


def test_with_gaps(test_word):
    checker = re.compile(r'\[[^\[\]\|]*\]')
    exclusions = [m.span() for m in checker.finditer(test_word)]

    orig_word = get_original_word(test_word, exclusions)
    quest_word = get_quest_word(test_word, exclusions)

    print('Question:     %s' % quest_word)
    answer = input('Your answer:  ').strip()
    if answer == orig_word:
        print('Right\n')
        return True
    else:
        print('Mistake!\nRight answer: %s\n' % orig_word)
        return False


def test_with_choice(line):
    print('Choose right variant:')
    checker = re.compile(r'[^\[\]\|]+')
    answers = [line[m.span()[0]:m.span()[1]].strip() for m in checker.finditer(line)]
    right_answer = answers[0]
    random.shuffle(answers)
    for i, answer in enumerate(answers):
        print('{}. {}'.format(i+1, answer))
    answer = input('Your answer: ')
    try:
        answer = answers[int(answer) - 1]
    except ValueError:
        pass
    if answer == right_answer:
        print('Right\n')
        return True
    else:
        print('Mistake!\nRight answer: %s\n' % right_answer)
        return False


def test_with_stress(test_word):
    test_word = test_word.strip()
    checker = re.compile(r'([аоыэуяёіею])ʼ')
    quest_word = ''.join(checker.split(test_word))
    orig_word = test_word
    print('Put the stress: {}'.format(quest_word))
    answer = input('Your answer:    ')
    if answer == orig_word:
        print('Right\n')
        return True
    else:
        print('Mistake!\nRight answer: %s\n' % orig_word)
        return False


def test_with_translation(line):
    checker = re.compile(r'->')
    match = checker.search(line)
    orig_word = line[:match.span()[0]].strip()
    translation = line[match.span()[1]:].strip()

    print('Translate: {}'.format(orig_word))
    answer = input('You answer: ')
    if answer == translation:
        print('Right\n')
        return True
    else:
        print('Mistake!\nRight answer: %s\n' % translation)
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
    gaps_checker = re.compile(r'\[[^\[\]\|]*\]')
    choice_checker = re.compile(r'[^\[\]\|]+\|[^\[\]\|]+')
    stress_checker = re.compile(r'[аоыэуяёіею]ʼ')
    translate_checker = re.compile(r'->')

    for file_input in config.input:
        answer_stat.time = time.time()
        answer_stat.right = 0
        answer_stat.wrong = 0
        answer_stat.done = 0
        lines, description = read_test_words(file_input)
        answer_stat.quantity = len(lines)

        print('=' * 80)
        print(description)
        print('Reading the {} file'.format(file_input))
        print('Starting of {n} tests from {all}'.format(n=answer_stat.quantity, all=answer_stat.all))
        print('=' * 80)

        for line in lines:
            if gaps_checker.search(line):
                is_right = test_with_gaps(line)
            elif choice_checker.search(line):
                is_right = test_with_choice(line)
            elif stress_checker.search(line):
                is_right = test_with_stress(line)
            elif translate_checker.search(line):
                is_right = test_with_translation(line)
            else:
                raise Exception('Unknown test: "{}"'.format(line))
            answer_stat.right += int(is_right)
            answer_stat.wrong += int(not is_right)
            answer_stat.done += 1

        print_results()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Helper for training for central testing')
    parser.add_argument('input', nargs='+', type=str, help='the list of test files')
    parser.add_argument('-n', '--number-of-tests', type=int, metavar='N', default=0,
                        help='how many tests you want to pass. 0 means every test.')
    config = parser.parse_args()
    try:
        main()
    except UnicodeEncodeError:
        traceback.print_exc()
        print('\n\nPlease! Launch command "chcp 1251" before the program is started\n')
        sys.exit(1)
    except KeyboardInterrupt:
        print_results()
        sys.exit(0)
