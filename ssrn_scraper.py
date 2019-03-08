import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

def blank_data_frame():
    labels = ['Title', 'Link', 'Date', 'Author(s)', 'Downloads']
    papers = pd.DataFrame(columns=labels)
    return papers

def get_last_page(journal_id):
    url = "https://papers.ssrn.com/sol3/Jeljour_results.cfm?npage={0}&form_name=journalBrowse&journal_id={1}".format(page_number, journal_id)
    page = requests.get(url, timeout=10)
    soup = BeautifulSoup(page.content, 'html.parser')
    last_page = soup.find(class_='total').get_text()
    last_page = int(last_page)
    return last_page

def get_results_html(page_number, journal_id):
    url = "https://papers.ssrn.com/sol3/Jeljour_results.cfm?npage={0}&form_name=journalBrowse&journal_id={1}".format(page_number, journal_id)
    page = requests.get(url, timeout=10)
    soup = BeautifulSoup(page.content, 'html.parser')
    table = soup.find(id='maincontent')
    html = table.select("div[class^=trow]")
    return html

def get_paper_html(results_html, result_number):
    html = results_html[result_number]
    return html

def get_title(paper_html):
    title_html = paper_html.find(class_="title optClickTitle")
    title = title_html.get_text()
    return title

def get_link(paper_html):
    title_html = paper_html.find(class_="title optClickTitle")
    link = title_html.get('href')
    return link

def get_post_date(paper_html):
    date_html = paper_html.find(class_="note note-list")
    notes = date_html.find_all('span')
    for note in notes:
        if 'Posted' in note.get_text():
            date_str = note.get_text().replace('Posted:', '').strip()
        else:
            pass
    date = datetime.strptime(date_str, '%d %b %Y')
    return date

def get_authors(paper_html):
    authors_html = paper_html.find(class_='authors-list')
    authors = authors_html.get_text().replace('\n','')
    return authors

def get_downloads(paper_html):
    downloads_html = paper_html.find(class_='downloads')
    downloads = downloads_html.get_text().replace('\n','').replace('Downloads','').strip()
    try:
        downloads = int(downloads.replace(',',''))
    except ValueError:
        downloads = 0
    return downloads

def get_paper_info(results_html, result_number):
    paper_html = get_paper_html(papers_html, result_number)
    if paper_html.find(class_='authors-list') == None:
        paper = None
    else:
        title = get_title(paper_html)
        link = get_link(paper_html)
        date = get_post_date(paper_html)
        authors = get_authors(paper_html)
        downloads = get_downloads(paper_html)
        paper_data = [(title, link, date, authors, downloads)]
        paper = pd.DataFrame(paper_data, columns=labels)
    return paper    

def summary_to_html(papers):
    date_cutoff = datetime.today() + pd.DateOffset(days=-7, normalize=True)
    papers = papers[papers['Date'] > date_cutoff]
    papers = papers.sort_values(by=['Downloads'], ascending=False)
    papers = papers.reset_index(drop=True)
    with pd.option_context('display.max_colwidth',-1):
        html = papers.to_html(index=False)
    return html

def send_email(sender, recipient, html_content, user_name, password):
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "SSRN Papers"
    msg['From'] = sender
    msg['To'] = recipient
    # Create the body of the message (a plain-text and an HTML version).
    text = "This is an HTML email. Allow HTML content to view."
    html = html_content
    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)
    # Send the message via local SMTP server.
    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()
    mail.login(user_name, password)
    mail.sendmail(me, you, msg.as_string())
    mail.quit()
    return

if __name__ == '__main__':
    journal_id = 1175282
    sender = 'email@gmail.com'
    recipient = 'email@gmail.com'
    user_name = 'gmail_username'
    password = 'gmail_password'
    papers = blank_data_frame()
    last_page = get_last_page(journal_id)
    for page in range(1, last_page+1):
        papers_html = get_results_html(page, journal_id)
        for result in range(0,len(papers_html)):
            paper = get_paper_info(papers_html, result)
            papers = papers.append(paper)
    html_table = summary_to_html(papers)
    send_email(sender, recipient, html_table, user_name, password)
