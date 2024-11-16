from flask import Flask, render_template, request, redirect, url_for
from newspaper import Article
import nltk
import numpy as np 
import openai
from openai import OpenAI
from pathlib import Path
from datetime import datetime
import json 
import os

app = Flask(__name__)
	


def scan_paper(url):
	article = Article(url)
	article.download()
	article.parse()

	if article.is_valid_body() and article.is_valid_url():
		cont = article.title + "\n " + article.text
		authors = ""
		date = "Unknown"
		img = article.top_image
		#date_object = datetime(*(article.publish_date)).date()
		#date = date_object.strftime('%Y-%m-%d')
		for author in article.authors:
			authors += author + ", "
		return (cont, authors[:-2], date, img)
	else:
		print(f"Error checking URL:")
		return ""

def parse_text(text):

	#paragraphs = [p for p in text.split('\n') if p]
	paragraphs = [item for p in text.split('\n') for item in (p, 'br') if p]
	data = []

	for par in paragraphs:
		data = data+nltk.sent_tokenize(par)
	
	if data[1] == 'br':
		del data[1]
	
	formated_data = np.array2string(np.array(data))
	print(formated_data)
	return (data, formated_data)

def gpt_query(text):
	org = "Personal"
	key = os.environ['OPENAI_KEY']
	client = OpenAI(api_key = key)
	completion = client.chat.completions.create(
    model = "ft:gpt-3.5-turbo-1106:personal::8jyHHxLe",
    	messages = [
			{
				"role": "system", 
				"content": "analyze partisan bias, and rank as light, moderate, or extreme, identify every framing bias in the article"
			},
			{
				"role": "user", 
				"content": text
			}
		],
	)
	return completion


def display_article(json_file, article):

	analyzed_sents = json_file['sentence_analysis']
	sent_ind = 0
	br_count = 0
	html = []

	for i in range(0, len(article)):
		if article[i] == 'br':
			html = html + [(0, "")]
			br_count += 1
		elif (sent_ind < len(analyzed_sents) and (i-br_count) == (int(analyzed_sents[sent_ind]['index']))):
			html = html + [(1, article[i], analyzed_sents[sent_ind]['analysis'])]
			sent_ind = sent_ind + 1
		else:
			html = html + [(2, article[i])]

	return html
	





	

@app.route("/", methods=['GET'])
def home():

	try:
		err_status = request.args['error']
		err = "Please input valid news article link"
		return render_template('index.html', err = err )
	except Exception as e:
		return render_template('index.html', err = "")


@app.route("/article", methods=['POST'])
def process_article():
	url = request.form['urlInput']
	scanned_pap = scan_paper(url)
	text = scanned_pap[0]
	if text == "":
		return redirect(url_for('home', error = "invalid link"))


	parsed_data = parse_text(text)

	sentence_list = parsed_data[0]

	#json_string = gpt_query(parsed_data[1])


	file = json.loads("./json_test.txt")
	body = display_article(file, sentence_list)
	title_a = file['headline_bias']['analysis']
	author = scanned_pap[1]
	date = scanned_pap[2]
	img = scanned_pap[3]
	selection = file['comment_on_selection_bias']

	return render_template('article.html', url = url, body = body, author = author, date = date, img = img, title_a = title_a, selection=selection)




