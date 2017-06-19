import numpy as np
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
import termcolor

pd.set_option('display.max_colwidth', -1)
pd.set_option('display.colheader_justify', 'left')


def log_time(kind='general', color_str=None):
    if color_str is None:
        if kind == 'error' or kind.startswith('e'):
            color_str = 'red'
        elif kind == 'info' or kind.startswith('i'):
            color_str = 'yellow'
        elif kind == 'overwrite' or kind.startswith('o'):
            color_str = 'magenta'
        elif kind == 'write' or kind.startswith('w'):
            color_str = 'cyan'
        elif kind == 'highlight' or kind.startswith('h'):
            color_str = 'green'
        else:
            color_str = 'white'

    print termcolor.colored(datetime.datetime.now(), color_str),


def calc_pause(base_seconds=3., variable_seconds=5.):
    return base_seconds + random.random() * variable_seconds


def set_pause(kind=1, t=None):
    log_time('info')
    if t is not None:
        kind_str = 'specific'
    else:
        if kind == 5:
            kind_str = 'ultra long'
            t = calc_pause(base_seconds=1000, variable_seconds=1000)
        elif kind == 4:
            kind_str = 'very long'
            t = calc_pause(base_seconds=100, variable_seconds=100)
        elif kind == 3:
            kind_str = 'long'
            t = calc_pause(base_seconds=10, variable_seconds=10)
        elif kind == 2:
            kind_str = 'short'
            t = calc_pause(base_seconds=3., variable_seconds=3.)
        else:
            kind_str = 'very short'
            t = calc_pause(base_seconds=0.5, variable_seconds=0.5)

    print '{} pause: {}s...'.format(kind_str, t)

    time.sleep(t)


def init_driver(driver_type='Phatom'):
    log_time('info')
    print 'initiating driver: {}'.format(driver_type)
    if driver_type == 'Chrome':
        dr = webdriver.Chrome()
    elif driver_type.startswith('Pha'):
        dr = webdriver.PhantomJS()
    elif driver_type.startswith('Fi'):
        dr = webdriver.Firefox()
    else:
        assert False
    dr.set_window_size(1920, 600)
    dr.wait = WebDriverWait(dr, 5)
    dr.set_page_load_timeout(25)
    return dr


def quit_driver(dr):
    log_time('info')
    print 'closing driver...'
    dr.quit()


class AngelScraper:
    def __init__(self,
                 skip_market_filter=True,
                 skip_location_filter=False,
                 skip_raised_filter=False,
                 skip_stage_filter=False,
                 skip_signal_filter=True,
                 skip_featured_filter=False,
                 market_label_file='market_labels.txt'
                 ):

        self.root_url = 'https://angel.co/companies?'

        self.working_dir = '/Users/dingran/github/angellist-webscrape'
        self.code_dir = os.path.join(self.working_dir, 'code')
        self.output_dir = os.path.join(self.working_dir, 'output')
        self.url_list_folder = os.path.join(self.output_dir, 'url_lists')
        self.results_folder = os.path.join(self.output_dir, 'results')
        self.company_page_folder = os.path.join(self.output_dir, 'company_pages')
        self.index_page_folder = os.path.join(self.output_dir, 'index_pages')
        self.market_label_size_file_dir = os.path.join(self.output_dir, 'market_label_size')
        self.debug_dir = os.path.join(self.output_dir, 'debug')

        self.parser = 'lxml'
        self.visit_inner = True
        self.mute_display = False

        # markets
        if market_label_file is None:
            market_labels = []
        else:
            with open(os.path.join(self.code_dir, os.path.basename(market_label_file)), 'r') as f:
                m = f.readlines()
            market_labels = [x.strip() for x in m]

        if not market_labels or skip_market_filter:
            self.market_filters = ['']
        else:
            self.market_filters = ['&markets[]={}'.format(x.replace(' ', '+')).replace('+++', '+') for x in
                                   market_labels]
            # self.market_filters.append('')
            self.market_filters.insert(0, '')

        # locations
        locations = ['United States', 'Europe', 'Silicon Valley', 'Asia', 'London', 'New York', 'California']
        if not locations or skip_location_filter:
            self.location_filters = ['']
        else:
            self.location_filters = ['&locations[]={}'.format(x.replace(' ', '+')) for x in locations]
            # self.location_filters.append('')
            self.location_filters.insert(0, '')

        # signal levels
        signal_pair_list = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10)]
        signal_pair_list.reverse()
        if skip_signal_filter or not signal_pair_list:
            # signal_pair_list = [(8, 9), (9, 10)]
            signal_pair_list = [(7, 8)]
        self.signal_filters = [
            '&signal[min]={signal_min}&signal[max]={signal_max}'.format(signal_min=x[0], signal_max=x[1]) for x in
            signal_pair_list]

        self.signal_filters = zip(self.signal_filters, signal_pair_list)

        # featured flag
        if skip_featured_filter:
            self.featured_filters = ['']
        else:
            self.featured_filters = ['', '&featured=Featured']

        # raised money
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
        if not raised_pair_list or skip_raised_filter:
            self.raised_filters = ['']
        else:
            self.raised_filters = [
                '&raised[min]={raised_min}&raised[max]={raised_max}'.format(raised_min=x[0], raised_max=x[1]) for x in
                raised_pair_list]
            # self.raised_filters.append('')
            self.raised_filters.insert(0, '')

        # stage
        stage_list = [
            'Series+A',
            'Series+B',
            'Acquired',
            'Series+C',
            'Series+D',
            'Seed',
            'IPO',
        ]
        if skip_stage_filter or not stage_list:
            self.stage_filters = ['']
        else:
            self.stage_filters = ['&stage={}'.format(x) for x in stage_list]
            # self.stage_filters.append('')
            self.stage_filters.insert(0, '')

        self.url_df = None
        self.index_url_list_file = os.path.join(self.url_list_folder,
                                                'url_list_{}.csv'.format(datetime.date.today()))

    def generate_url_list(self, use_existing_url_list=False):

        tmp_raised_filters = self.raised_filters
        tmp_stage_filters = self.stage_filters

        if not use_existing_url_list:

            url_list = []
            for mf in self.market_filters:
                for ff in self.featured_filters:
                    for lf in self.location_filters:
                        for sf in self.signal_filters:
                            target_url = self.root_url + mf + ff + lf + sf[0]
                            company_count = self.get_company_count_on_index_page(url=target_url)
                            if company_count > 0:
                                url_list.append(dict(url=target_url,
                                                     fname=self.url_to_base_fname(target_url),
                                                     company_count=company_count,
                                                     featured=ff,
                                                     signal=sf[1][1]))
                            else:
                                log_time()
                                print 'empty list, not adding to the url_list: {}'.format(target_url)

                            if random.random() < .6:
                                set_pause(2)
                            elif random.random() < .95:
                                set_pause(1)

                            if company_count > 400:
                                log_time()
                                print 'index page too long (>400), further dividing...'

                                for tsf in tmp_stage_filters:
                                    url_div1 = target_url + tsf
                                    company_count_div1 = self.get_company_count_on_index_page(url=url_div1)
                                    if random.random() < .6:
                                        set_pause(2)
                                    elif random.random() < .95:
                                        set_pause(1)
                                    if company_count_div1 > 0:
                                        url_list.append(dict(url=url_div1,
                                                             fname=self.url_to_base_fname(url_div1),
                                                             company_count=company_count_div1,
                                                             featured=ff,
                                                             signal=sf[1][1]))
                                    else:
                                        log_time()
                                        print 'empty list, not adding to the url_list: {}'.format(url_div1)

                                    if company_count_div1 > 400:
                                        log_time()
                                        print 'index page still too long (>400), further further dividing...'

                                        for trf in tmp_raised_filters:
                                            url_div1_div1 = url_div1 + trf
                                            company_count_div1_div1 = self.get_company_count_on_index_page(
                                                url=url_div1_div1)
                                            if random.random() < .6:
                                                set_pause(2)
                                            elif random.random() < .95:
                                                set_pause(1)
                                            if company_count_div1_div1 > 0:
                                                url_list.append(dict(url=url_div1_div1,
                                                                     fname=self.url_to_base_fname(url_div1_div1),
                                                                     company_count=company_count_div1_div1,
                                                                     featured=ff,
                                                                     signal=sf[1][1]))
                                            else:
                                                log_time()
                                                print 'empty list, not adding to the url_list: {}'.format(url_div1_div1)

                                for trf in tmp_raised_filters:
                                    url_div2 = target_url + trf
                                    company_count_div2 = self.get_company_count_on_index_page(url=url_div2)
                                    if random.random() < .6:
                                        set_pause(2)
                                    elif random.random() < .95:
                                        set_pause(1)
                                    if company_count_div2 > 0:
                                        url_list.append(dict(url=url_div2,
                                                             fname=self.url_to_base_fname(url_div2),
                                                             company_count=company_count_div2,
                                                             featured=ff,
                                                             signal=sf[1][1]))
                                    else:
                                        log_time()
                                        print 'empty list, not adding to the url_list: {}'.format(url_div2)

            self.url_df = pd.DataFrame(url_list).drop_duplicates()

            log_time()
            print 'Writing url list file: {}'.format(self.index_url_list_file)
            self.url_df.to_csv(self.index_url_list_file)
        else:
            log_time()
            print 'Reading url list file: {}'.format(self.index_url_list_file)
            self.url_df = pd.read_csv(self.index_url_list_file)

        log_time()
        print 'Length of url_list: {}'.format(len(self.url_df))

    def url_to_base_fname(self, url):
        fname = 'results_' + url.replace(self.root_url, '').replace('&', '_') + '.csv'
        return fname

    def get_company_count_on_index_page(self, driver_in=None, url=None):
        log_time('highlight')
        print '*** New search, url: {}'.format(url)

        if driver_in is None:
            driver = init_driver()
        else:
            driver = driver_in

        if not self.load_url(driver, url):
            return None

        page = driver.page_source
        if driver_in is None:
            quit_driver(driver)
        soup = BeautifulSoup(page, self.parser)
        parser_count = re.compile(r'([\d,]+)')
        company_count = soup.select('div.top div.count')[0].get_text().replace(',', '')
        company_count = int(parser_count.search(company_count).group(1))

        log_time('highlight')
        print '*** found {} companies'.format(company_count)

        return company_count

    def load_url(self, driver=None, url=None, n_attempts_limit=3):
        n_attempts = 0
        page_loaded = False
        while n_attempts < n_attempts_limit and not page_loaded:
            try:
                driver.get(url)
                page_loaded = True
                log_time()
                print 'page loaded successfully: {}'.format(url)
            except TimeoutException:
                n_attempts += 1
                log_time('error')
                print 'loading page timeout', url, 'attempt {}'.format(n_attempts)
                set_pause(1)
            except:
                n_attempts += 1
                log_time('error')
                print 'loading page unknown error', url, 'attempt {}'.format(n_attempts)
                set_pause(1)

        if n_attempts == n_attempts_limit:
            driver.quit()
            log_time('error')
            print 'loading page failed after {} attempts, now give up:'.format(n_attempts_limit), url
            return False

        return True

    def parse_all_index_pages(self, use_file=None):
        self.url_df = self.url_df.iloc[np.random.permutation(len(self.url_df))]
        if use_file is None:  # then use self.url_df
            for idx, row in self.url_df.iterrows():
                self.parse_one_index_page(url_dict=row)
        else:
            assert 0

    def parse_one_index_page(self, url_dict=None):
        assert url_dict is not None

        log_time('highlight')
        print 'parsing single page'
        print url_dict
        url = url_dict['url']
        result_fname_tempalte = os.path.join(self.results_folder, url_dict['fname']).replace('.csv',
                                                                                             '_sort=<sort_key>_click={'
                                                                                             '}.csv')
        company_count = url_dict['company_count']
        signal_score = url_dict['signal']
        featured = url_dict['featured']

        if company_count > 400:
            click_sort_list = ['signal', 'joined', 'raised']
        else:
            click_sort_list = ['signal']

        for click_sort in click_sort_list:
            result_fname = result_fname_tempalte.replace('<sort_key>', click_sort)
            driver = init_driver()
            self.load_url(driver=driver, url=url)

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
                    log_time('error')
                    print 'exhausted page length, with N_click == {}'.format(N_click)

                if click_sort != 'signal':
                    css_selector_str = 'div.column.{}.sortable'.format(click_sort)
                    log_time('info')
                    print 'clicking sort button: {}'.format(css_selector_str)
                    try:
                        sort_button = driver.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector_str)))
                        sort_button.click()
                        driver.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector_str)))
                    except:
                        log_time('error')
                        print 'failed to click click_sort={} at {}'.format(click_sort, url)

                page = driver.page_source
                soup = BeautifulSoup(page, self.parser)

                try:
                    results = soup(class_='results')[0]('div', attrs={'data-_tn': 'companies/row'})
                    N_rows_new = len(results)
                except:
                    failed_case_fname = os.path.join(self.debug_dir,
                                                     'failed_{}.html'.format(str(datetime.datetime.now())))
                    log_time('error')
                    print 'failed to get results from page, saving page as {}'.format(failed_case_fname)
                    with open(failed_case_fname, 'w') as failed_f:
                        failed_f.write(page.encode('utf-8'))
                    quit_driver(driver)
                    set_pause(1)
                    continue
            else:
                log_time('error')
                print 'empty search result with target_url=={}'.format(url)
                quit_driver(driver)
                set_pause(1)
                continue

            entries = []

            while N_click < N_click_max:
                output_fname = result_fname.format(N_click)
                start_row = N_rows
                N_rows = N_rows_new

                if os.path.exists(output_fname):
                    log_time('overwrite')
                    print output_fname, 'exsits, skipping'
                else:
                    for i in range(start_row, N_rows):
                        entry = dict()
                        a = results[i]
                        title = a.select('a.startup-link')[0]['title']
                        title = title.encode('ascii', errors='replace')
                        entry['featured'] = featured
                        entry['score'] = signal_score
                        entry['title'] = title
                        print datetime.datetime.now(),
                        print 'N_click = {}, row = {}/{}, {}'.format(N_click, i, N_rows - 1, title)

                        inner_url = a.select('a.startup-link')[0]['href']
                        entry['al_link'] = inner_url
                        entry['signal'] = a.select('div.column.signal')[0]('img')[0]['alt']

                        date_obj = a.select('div.column.joined > div.value')
                        if date_obj:
                            date_str = date_obj[0].get_text().encode('ascii', errors='replace').strip().replace(
                                '?',
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

                        inner_page_filename = os.path.join(self.company_page_folder,
                                                           inner_url.replace('/', ']]]') + '.html')
                        if self.visit_inner:
                            inner_page = None

                            if os.path.exists(inner_page_filename):
                                log_time('overwrite')
                                print '{} exists, wont re-download'.format(inner_page_filename)
                                with open(inner_page_filename, 'r') as fi:
                                    inner_page = fi.read()
                            else:
                                inner_driver = init_driver()
                                if self.load_url(driver=inner_driver, url=inner_url):

                                    inner_page = inner_driver.page_source
                                    inner_driver.quit()
                                    with open(inner_page_filename, 'w') as p:
                                        if type(inner_page) is unicode:
                                            p.write(inner_page.encode('utf-8'))
                                        else:
                                            p.write(inner_page)

                                    if random.random() < 0.1:
                                        set_pause(3)
                                    elif random.random() < .6:
                                        set_pause(2)
                                    elif random.random() < .95:
                                        set_pause(1)

                                else:
                                    quit_driver(inner_driver)
                                    continue

                            if inner_page is not None:
                                inner_soup = BeautifulSoup(inner_page, self.parser)
                                try:
                                    product_desc = inner_soup.select('div.product_desc div.content')[
                                        0].get_text().strip()
                                    # print product_desc
                                    entry['product_desc'] = product_desc
                                except:
                                    log_time('error')
                                    print 'cannnot get product_desc'

                        with open(inner_page_filename.replace('.html', '.txt'), 'w') as f_record:
                            # print entry
                            f_record.write(str(entry))

                        entries.append(entry)

                    df_entries = pd.DataFrame(entries)
                    log_time('write')
                    print 'Writing {}'.format(output_fname)
                    df_entries.to_csv(output_fname, index=False, encoding='utf-8')

                    if last_page_flag:
                        log_time('error')
                        print 'stopping'
                        set_pause(1)
                        break

                if random.random() < 0.01:
                    set_pause(5)
                elif random.random() < 0.05:
                    set_pause(4)
                elif random.random() < 0.1:
                    set_pause(3)
                elif random.random() < .9:
                    set_pause(2)
                else:
                    set_pause(1)

                N_click += 1
                try:
                    more_button.click()
                except:
                    log_time('error')
                    print 'more button not clickable, N_click = {}'.format(N_click)
                    set_pause(1)
                    break

                page_loaded = False
                N_tries = 0
                while not page_loaded and N_tries < 10:
                    N_tries += 1
                    page = driver.page_source
                    page_filename = os.path.join(self.index_page_folder,
                                                 url.replace('/', ']]]') + '_click_{}.html'.format(
                                                     N_click))
                    with open(page_filename, 'w') as p:
                        if type(page) is unicode:
                            p.write(page.encode('ascii', errors='ignore'))
                        else:
                            p.write(page)
                    soup = BeautifulSoup(page, self.parser)
                    results = soup(class_='results')[0]('div', attrs={'data-_tn': 'companies/row'})
                    N_rows_new = len(results)
                    if N_rows_new > N_rows:
                        page_loaded = True

                    time.sleep(0.5)
                try:
                    more_button = driver.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'more')))
                except TimeoutException:
                    last_page_flag = True
                    log_time('error')
                    print 'exhausted page length, with N_click == {}'.format(N_click)

            quit_driver(driver)
