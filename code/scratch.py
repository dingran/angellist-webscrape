# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 09:58:32 2016

@author: ran
"""

import os
import re
import sys
import glob
import time
import shutil
import random
import urllib2
import logging
import urlparse
import platform
import datetime
import pandas as pd
from random import shuffle
from bs4 import BeautifulSoup
from contextlib import closing
from pyvirtualdisplay import Display
from progressbar import Bar, ETA, Percentage, ProgressBar, RotatingMarker, Timer

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

working_dir = '/Users/ran/Dropbox/angellist_webscrape'
if platform.system() == 'Linux':
    working_dir = '/home/dingran/Dropbox/angellist_webscrape'
output_dir = os.path.join(working_dir, 'output')
company_page_folder = os.path.join(output_dir, 'company_pages')
market_label_size_file_dir = os.path.join(output_dir, 'market_label_size')
debug_dir = os.path.join(output_dir, 'debug')

parser = 'lxml'
visit_inner = True
mute_display = True


def calc_pause(base_seconds=3., variable_seconds=5.):
    return base_seconds + random.random() * variable_seconds


def very_short_pause():
    t = calc_pause(base_seconds=0.5, variable_seconds=2.)
    print datetime.datetime.now(),
    print 'very short pause: {}s...'.format(t)
    time.sleep(t)


def short_pause():
    t = calc_pause()
    print datetime.datetime.now(),
    print 'short pause: {}s...'.format(t)
    time.sleep(t)


def long_pause():
    t = calc_pause(base_seconds=20, variable_seconds=10)
    print datetime.datetime.now(),
    print 'long pause: {}s...'.format(t)
    time.sleep(t)


def very_long_pause():
    t = calc_pause(base_seconds=200, variable_seconds=100)
    print datetime.datetime.now(),
    print 'very long pause: {}s...'.format(t)
    time.sleep(t)


def ultra_long_pause():
    t = calc_pause(base_seconds=2000, variable_seconds=1000)
    print datetime.datetime.now(),
    print 'very long pause: {}s...'.format(t)
    time.sleep(t)


def init_driver():
    # dr = webdriver.Firefox()
    dr = webdriver.Chrome()
    # dr= webdriver.PhantomJS()
    dr.set_window_size(1920, 600)
    dr.wait = WebDriverWait(dr, 5)
    dr.set_page_load_timeout(15)
    return dr


with open('market_labels_selected.txt', 'r') as f:
    m = f.readlines()
market_labels = [x.strip() for x in m]

# print market_labels

shuffle(market_labels)

if mute_display:
    display0 = Display(visible=0)
    print 'mute display'
    display0.start()
# selected_location = 'United States'
selected_location = ''
selected_signal_min = 9
selected_signal_max = 10

step_through_raised = True
# if True means we'll focus on a long list and do stepping through raised amount

if step_through_raised:
    N_iterations = 1
    featured_list = ['']
    market_labels = ['']
    raised_pair_list = [(0, 1),
                        (1, 400000),
                        (400000, 10000000),
                        (1000000, 1500000),
                        (1500000, 2000000),
                        (2000000, 2500000),
                        (2500000, 3500000),
                        (3500000, 5500000),
                        (5500000, 8500000),
                        (8500000, 12000000),
                        (12000000, 20000000),
                        (20000000, 30000000),
                        (30000000, 50000000),
                        (50000000, 100000000),
                        (100000000, 1000000000),
                        (1000000000, 1000000000000000)
                        ]
else:
    N_iterations = len(market_labels) / 1
    featured_list = ['featured=Featured', '']
    raised_pair_list = [None]

# for featured in ['featured=Featured', '']:
# for featured in ['']:
for featured in featured_list:
    for i_market_label in range(N_iterations):
        for click_sort in ['signal', 'joined', 'raised']:
            for raised_pair in raised_pair_list:

                selected_label = market_labels[i_market_label]

                url_template = 'https://angel.co/companies?'

                signal_filter = 'signal[min]={signal_min}&signal[max]={signal_max}'.format(
                    signal_min=selected_signal_min,
                    signal_max=selected_signal_max)
                market_filter = 'markets[]={}'.format(selected_label.replace(' ', '+')).replace('+++', '+')
                location_filter = 'locations[]={}'.format(selected_location.replace(' ', '+'))

                if len(raised_pair_list) == 1:  # not steping this
                    target_url = '{}{}&{}&{}&{}'.format(url_template, signal_filter, market_filter, location_filter,
                                                        featured)
                    output_fname_template = os.path.join(output_dir,
                                                         'output_{}_{}_{}_{}_sort={}_click{}.csv'.format(market_filter,
                                                                                                         location_filter,
                                                                                                         signal_filter,
                                                                                                         featured,
                                                                                                         click_sort,
                                                                                                         '{}'))
                else:
                    raised_filter = 'raised[min]={raised_min}&raised[max]={raised_max}'.format(
                        raised_min=raised_pair[0],
                        raised_max=raised_pair[1])
                    target_url = '{}{}&{}&{}&{}&{}'.format(url_template, signal_filter, market_filter, location_filter,
                                                           raised_filter, featured)
                    output_fname_template = os.path.join(output_dir,
                                                         'output_{}_{}_{}_{}_{}_sort={}_click{}.csv'.format(
                                                             market_filter,
                                                             location_filter,
                                                             signal_filter,
                                                             raised_filter,
                                                             featured,
                                                             click_sort,
                                                             '{}'))

                overall_serach_condition = 'featured_list_N={}, market_label_len_N={}, raised_pair_N={}'.format(
                    len(featured_list), N_iterations, len(raised_pair_list))
                print datetime.datetime.now(), '*' * 20, 'New search', '*' * 20
                print 'market_label: {}'.format(selected_label)
                print 'target_url: {}'.format(target_url)
                print 'output_fname_template: {}'.format(output_fname_template)

                driver = init_driver()

                try:
                    driver.get(target_url)
                except TimeoutException:
                    print datetime.datetime.now(),
                    print 'loading page timeout', target_url
                    driver.quit()
                    continue

                page = driver.page_source
                soup = BeautifulSoup(page, parser)
                parser_count = re.compile(r'([\d,]+)')
                company_count = soup.select('div.top div.count')[0].get_text().replace(',', '')
                company_count = int(parser_count.search(company_count).group(1))

                print datetime.datetime.now(),
                print '*' * 20 + ' market_label=={}, found {} companies'.format(selected_label, company_count)

                if click_sort == 'signal':
                    label_size_fname = os.path.join(market_label_size_file_dir,
                                                    os.path.basename(output_fname_template).
                                                    replace('output', 'labelsize{}'.format(company_count)).
                                                    replace('click{}.csv', '.txt'))

                with open(label_size_fname, 'w') as f_label:
                    f_label.write(str(datetime.datetime.now()))

                N_click_max = company_count / 20 + 2

                N_click = 1
                N_rows = 1
                N_rows_new = -1
                start_row = 1
                results = None
                last_page_flag = False

                more_button = None
                if company_count > 0:
                    try:
                        more_button = driver.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'more')))
                    except TimeoutException:
                        last_page_flag = True
                        print datetime.datetime.now(),
                        print 'exhausted page length, with N_click == {}'.format(N_click)

                    if company_count > 400 and click_sort != 'signal':
                        css_selector_str = 'div.column.{}.sortable'.format(click_sort)
                        print datetime.datetime.now(),
                        print 'clicking sort button: {}'.format(css_selector_str)
                        sort_button = driver.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector_str)))
                        sort_button.click()
                        driver.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector_str)))
                    else:
                        if click_sort != 'signal':
                            print datetime.datetime.now(),
                            print 'company count too small, not resorting, skipping click_sort=={}'.format(click_sort)
                            driver.quit()
                            continue

                    page = driver.page_source
                    soup = BeautifulSoup(page, parser)

                    try:
                        results = soup(class_='results')[0]('div', attrs={'data-_tn': 'companies/row'})
                        N_rows_new = len(results)
                    except:
                        failed_case_fname = os.path.join(debug_dir,
                                                         'failed_{}.html'.format(str(datetime.datetime.now())))
                        print 'failed to get results from page, saving page as {}'.format(failed_case_fname)
                        with open(failed_case_fname, 'w') as failed_f:
                            failed_f.write(page.encode('utf-8'))
                        driver.quit()
                        continue
                else:
                    print datetime.datetime.now(),
                    print 'empty search result with target_url=={}'.format(target_url)
                    driver.quit()
                    continue

                entries = []

                # aggregate existing files
                # list_of_record_files = glob.glob(os.path.join(company_page_folder, '*.txt'))
                # if len(list_of_record_files) > 100:
                #     for f in list_of_record_files:
                #         with open(f, 'r') as f_rec:
                #             entries.append(eval(f_rec.read()))
                #     df_entries = pd.DataFrame(entries)
                #     df_entries.to_csv(
                #         os.path.join(output_dir, 'output_{}.csv'.format(str(datetime.datetime.now()))),
                #         index=False,
                #         encoding='utf-8')

                while N_click < N_click_max:
                    output_fname = output_fname_template.format(N_click)
                    start_row = N_rows
                    N_rows = N_rows_new

                    if os.path.exists(output_fname):
                        print datetime.datetime.now(),
                        print output_fname, 'exsits, skipping'
                    else:
                        for i in range(start_row, N_rows):
                            entry = dict()
                            a = results[i]
                            title = a.select('a.startup-link')[0]['title']
                            title = title.encode('ascii', errors='replace')
                            entry['featured'] = featured
                            entry['title'] = title
                            print datetime.datetime.now(),
                            print 'N_click = {}, row = {}/{}, {}'.format(N_click, i, N_rows - 1, title)

                            inner_url = a.select('a.startup-link')[0]['href']
                            entry['al_link'] = inner_url
                            entry['signal'] = a.select('div.column.signal')[0]('img')[0]['alt']

                            date_obj = a.select('div.column.joined > div.value')
                            if date_obj:
                                date_str = date_obj[0].get_text().encode('ascii', errors='replace').strip().replace('?',
                                                                                                                    '')
                                entry['joined_date'] = datetime.datetime.strptime(date_str, '%b %y')
                            else:
                                entry['joined_date'] = None

                            location_obj = a.select('div.column.location div.tag')
                            if location_obj:
                                entry['location'] = location_obj[0].get_text().strip()

                            market_obj = a.select('div.column.market div.tag')
                            if market_obj:
                                entry['market'] = market_obj[0].get_text().strip()

                            try:
                                entry['website'] = a.select('div.column.website a')[0]['href']
                            except:
                                pass

                            entry['size'] = a.select('div.column.company_size div.value')[0].get_text().strip()
                            entry['stage'] = a.select('div.column.stage div.value')[0].get_text().strip()
                            money = a.select('div.column.raised div.value')[0].get_text().strip()
                            money = re.sub(r'[^\d.]', '', money)
                            if money:
                                entry['raised'] = float(money)

                            inner_page_filename = os.path.join(company_page_folder,
                                                               inner_url.replace('/', ']]]') + '.html')
                            if visit_inner:
                                inner_page = None

                                if os.path.exists(inner_page_filename):
                                    print datetime.datetime.now(),
                                    print '{} exists, wont re-download'.format(inner_page_filename)
                                    with open(inner_page_filename, 'r') as fi:
                                        inner_page = fi.read()
                                else:
                                    inner_page_load_success = False
                                    inner_driver = init_driver()
                                    try:
                                        inner_driver.get(inner_url)
                                        inner_page_load_success = True
                                    except TimeoutException:
                                        print datetime.datetime.now(),
                                        print 'loading page timeout', inner_url

                                    if inner_page_load_success:
                                        if random.random() < .95:
                                            very_short_pause()
                                        elif random.random() < .6:
                                            short_pause()
                                        elif random.random() < 0.1:
                                            long_pause()

                                        inner_page = inner_driver.page_source
                                        inner_driver.quit()
                                        with open(inner_page_filename, 'w') as p:
                                            if type(inner_page) is unicode:
                                                p.write(inner_page.encode('utf-8'))
                                            else:
                                                p.write(inner_page)
                                    else:
                                        inner_driver.quit()

                                if inner_page is not None:
                                    inner_soup = BeautifulSoup(inner_page, parser)
                                    try:
                                        product_desc = inner_soup.select('div.product_desc div.content')[
                                            0].get_text().strip()
                                        # print product_desc
                                        entry['product_desc'] = product_desc
                                    except:
                                        print datetime.datetime.now(),
                                        print 'cannnot get product_desc'

                            with open(inner_page_filename.replace('.html', '.txt'), 'w') as f_record:
                                # print entry
                                f_record.write(str(entry))

                            entries.append(entry)

                        df_entries = pd.DataFrame(entries)
                        print datetime.datetime.now(),
                        print 'Writing {}'.format(output_fname)
                        df_entries.to_csv(output_fname, index=False, encoding='utf-8')

                        if last_page_flag:
                            print datetime.datetime.now(),
                            print 'stopping'
                            break

                        if random.random() < .9:
                            short_pause()
                        else:
                            very_short_pause()

                        if random.random() < 0.1:
                            long_pause()

                        if random.random() < 0.05:
                            very_long_pause()

                        if random.random() < 0.01:
                            ultra_long_pause()

                    N_click += 1
                    try:
                        more_button.click()
                    except:
                        print 'more button not clickable, N_click = {}'.format(N_click)
                        break

                    page_loaded = False
                    N_tries = 0
                    while not page_loaded and N_tries < 10:
                        N_tries += 1
                        page = driver.page_source
                        page_filename = os.path.join(output_dir, 'index_pages',
                                                     target_url.replace('/', ']]]') + '_clock_{}.html'.format(N_click))
                        with open(page_filename, 'w') as p:
                            if type(page) is unicode:
                                p.write(page.encode('ascii', errors='ignore'))
                            else:
                                p.write(page)
                        soup = BeautifulSoup(page, parser)
                        results = soup(class_='results')[0]('div', attrs={'data-_tn': 'companies/row'})
                        N_rows_new = len(results)
                        if N_rows_new > N_rows:
                            page_loaded = True

                        time.sleep(0.5)
                    try:
                        more_button = driver.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'more')))
                    except TimeoutException:
                        last_page_flag = True
                        print datetime.datetime.now(),
                        print 'exhausted page length, with N_click == {}'.format(N_click)

                driver.quit()

if mute_display:
    display0.stop()
