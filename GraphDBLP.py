#!/usr/bin/env python
import matplotlib as mpl 
mpl.use('agg')
import json
from py2neo import Graph
from pandas import DataFrame
from tabulate import tabulate
import subprocess
import argparse
import logging
import sys
import time
import datetime
from datetime import timedelta
import statistics as st
from testing import plot
import numpy as np 



graph = Graph("http://127.0.0.1:7474")



parser = argparse.ArgumentParser(description='GraphDBLP',formatter_class=argparse.RawTextHelpFormatter)

#init par
parser.add_argument('-init', nargs=1, help='Specify the dump filename to be used to initialise the GraphDBLP database' , required=False,metavar=('dump-filename'))
#pars for queries
parser.add_argument('-test', nargs='*', help='Perform a random test on the specified query as in described in the paper' , required=False)
parser.add_argument('-q1', nargs=2, help='Execute query number 1 for AUTHOR PROFILING. This requires to specify also the keyword to be used and the limit value for results. Example: -q1 \'multimedia\' 10 will perform query 1 using multimedia as keyword and collecting top 10 results ' , required=False,metavar=('keyword', 'limit'))
parser.add_argument('-q2', nargs=3, help='Execute query number 2 for AUTHOR PUBLICATION RECORDS COMPARISON. This requires to specify also the keyword to be used, the max number of researchers to be considered for each keyword and the similarity threshold value for similar keywords. Example: -q2 \'John von Neumann\' 3 0.4 will perform query 2 profiling the publication record of John Doe and retrieving up to 3 top researchers for each keyword appearing the in profile of John von Neumann. In addition, for each keyword, only keywords with a similarity value grater than 0.4 will be returned' , required=False,metavar=('author-name-surname', 'limit','similarity-threshold'))
parser.add_argument('-q3', nargs=2, help='Execute query number 3 for SNA ON RESEARCH COMMUNITIES. This requires to specify the venue name and a threshold value for computing the similarity. Example: -q3 \'ijcai\' 10 percent will perform query 3 computing the community starting from ijcai and considering venue with a similarity value with at least 10 percent' , required=False,metavar=('venue-name','similarity-threshold'))
parser.add_argument('-q4', nargs=4, help='Execute query number 4 for SHORTEST PATHS BETWEEN RESEARCHERS. This requires to specify the name of two  researchers to be connected, the relationships that can be navigated separated by a pipe | and the max number of paths to be returned. Example: -q4 \'John von Neumann\' \'Moshe Y. Vardi\' \'authored|contains\' 1', required=False,metavar=('author1-name-surname','author2-name-surname','rel-to-be-navigated','limit'))


class ElapsedFormatter():

	def __init__(self):
		self.start_time = time.time()

	def format(self, record):
		elapsed_seconds = record.created - self.start_time
		#using timedelta here for convenient default formatting
		elapsed = timedelta(seconds = elapsed_seconds)
		return "{} {}".format(elapsed, record.getMessage())

def setup_custom_logger(name):
	formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
	handler = logging.FileHandler('log.txt', mode='a')
	handler.setFormatter(ElapsedFormatter())
	screen_handler = logging.StreamHandler(stream=sys.stdout)
	screen_handler.setFormatter(formatter)
	logger = logging.getLogger(name)
	logger.setLevel(logging.DEBUG)
	logger.addHandler(handler)
	logger.addHandler(screen_handler)
	return logger


class GraphDBLP():
	def __init__(self):
		self.Q = {}
		self.Q_test_results = {}
		self.logger = setup_custom_logger('GraphDBLP')
		self.args = parser.parse_args()
		self.init_time = datetime.datetime.now()
	
	def init(self):
		self.logger.warning("Init mode activated: the db will be initialised from scratch in 10 seconds (time for undo)")
		self.countdown(1,"GraphDBLP init starts now")
		filename = self.args.init[0]
		command = "./neo4j-community-3.2.5/bin/neo4j-admin load --from="+filename+" --database=graph.db --force "
		print command
		print subprocess.call(command, shell=True)
		#print subprocess.check_output([command])

	def reconnect(self):
		now = datetime.datetime.now() - self.init_time
		if now.total_seconds > 500:
			#print "reconnecting"
			self.graph = Graph("http://neo4j@149.132.150.72:7474")
			#Graph("http://neo4j@localhost:7474")
	def countdown(self,t,message="bye"):
		while t:
			mins, secs = divmod(t, 60)
			timeformat = '{:02d}:{:02d}'.format(mins, secs)
			print(timeformat)
			time.sleep(1)
			t -= 1
		print(message+'\n')

	def Q1(self, key="multimedia",limit=10):
		assert type(key) == str or type(key) == unicode, "Keyword needs to be a string"
		assert type(limit) == int, "limit value needs to be an integer"
		self.logger.info('GraphDBLP: Running Q1')
		self.Q[1] = "MATCH (k:keyword)-[s:has_research_topic]-(a:author) WHERE k.key = {key} WITH k,a,s ORDER BY s.relevance desc, s.score desc limit {limit} MATCH path=(k)-[:contains]-(p:publication)-[t:authored]-(a)-[:contributed_to]-(v:venue) WHERE t.venue = v.name RETURN k.key,a.name,count(path) as freq,s.score,s.relevance, collect(distinct v.name) as venues ORDER BY s.relevance desc, s.score desc, freq desc limit {limit}"
		pars = {"key":key, "limit":limit}
		self.reconnect()
		return self.exec_query(self.Q[1],pars)

	def Q2(self, author_name="multimedia",limit=10,score_value=0.5):
		assert type(author_name) == str or type(author_name) == unicode, "Keyword needs to be a string"
		assert type(limit) == int, "limit value needs to be an integer"
		assert type(score_value) == (float or int), "limit value needs to be an integer or float"
		self.logger.info('GraphDBLP: Running Q2 for author %s',author_name)
		self.Q[2] = "MATCH (b:author)-[l:has_research_topic]->(k:keyword)<-[r:has_research_topic]-(a:author) WHERE lower(a.name)={author_name} WITH b,k,l.score as sugg_author_score, l.relevance as sugg_author_relevance, r.score as author_score,r.relevance as author_relevance ORDER BY sugg_author_relevance desc, sugg_author_score desc WITH collect([b,author_relevance, author_score, sugg_author_relevance, sugg_author_score]) as researchers_data, k UNWIND researchers_data[0..{limit}] AS r WITH k, (r[0]).name as name, r[3] as sugg_author_relevance, r[4] as sugg_author_score, r[1] as author_relevance, r[2] as author_score OPTIONAL MATCH (k)-[s:similar_to]-(z:keyword_sim)  WHERE toFloat(s.score) >= {score_value} RETURN k.key as keyword, name, sugg_author_relevance, sugg_author_score, author_relevance, author_score,collect(z.key+s.score) as similar ORDER BY author_score desc, author_relevance desc;"
		pars = {"author_name":author_name.lower(), "limit":limit, "score_value":score_value}
		self.reconnect()
		return self.exec_query(self.Q[2],pars)

	def Q3(self,venue_name='ijcai',threshold_value=0.4):
		self.logger.info('GraphDBLP: Running Q3 for venue %s',venue_name)
		self.Q[3] = "match (a:venue)-[s:similarity]-(b:venue) where lower(a.name) = {venue_name} and toFloat(s.jaccard_percent) >= {threshold_value} with a, b as neighbours match (a)-[ll:similarity]-()-[r:similarity]-()-[rr:similarity]-(a) where id(a) <> id(neighbours) and id(neighbours) <> 0 and toFloat(ll.jaccard_percent) >= {threshold_value} and toFloat(rr.jaccard_percent) >= {threshold_value} with count(distinct neighbours) as n , count(distinct r) as r, collect(distinct neighbours.name) as nn return n,r, r/(n*1.0*(n-1)/2) as lcc, nn "
		pars = {"venue_name":venue_name.lower(), "threshold_value":threshold_value}
		self.reconnect()
		resultset = []
		try:
			resultset = self.exec_query(self.Q[3],pars)
		except:
			self.logger.info("No results")
		return resultset
	
	def Q4(self, author_start,author_end,rel_list,limit):
		self.Q[4] = "match p=AllshortestPaths((n:author)-[:"+"|".join(rel_list)+"*]-(n2:author)) where lower(n.name) = \'"+author_start+"\' and lower(n2.name) = \'"+author_end+"\' return nodes(p) limit "+str(limit)

		self.reconnect()
		resultset = self.graph.run(self.Q[4]).data()
		for elem in resultset:
			print elem
		#return DataFrame()
		

	def exec_query(self,q,pars=[]):
		return DataFrame(self.graph.data(q,pars))

	def run(self,tab=True):
		
		q_result = None
		self.logger.info(self.args)
		if self.args.init != None:
			self.init()
		else:
			self.graph = Graph("http://neo4j@149.132.150.72:7474")
			#Graph("http://neo4j@localhost:7474")
		if self.args.q1 != None:
			q_result = g.Q1(self.args.q1[0],int(self.args.q1[1]))
		elif self.args.q2 != None:
			q_result = g.Q2(self.args.q2[0],int(self.args.q2[1]),float(self.args.q2[2]))
		elif self.args.q3 != None:
			q_result = g.Q3(self.args.q3[0],float(self.args.q3[1]))
		elif self.args.q4 != None:
			rel = self.args.q4[2].split("|")
			q_result = g.Q4(self.args.q4[0],self.args.q4[1],rel,self.args.q4[3])
		elif self.args.test != None:
			print self.args.test[0]
			if int(self.args.test[0]) == 1:
				#print g.test_q1(5)
				print g.test_q1()
			if int(self.args.test[0]) == 2:
				print g.test_q2()
			if int(self.args.test[0]) == 3:
				print g.test_q3()
				
		else:
			print "no parameters given. try with -h for help"
		if tab == True:	
			return tabulate(q_result,headers='keys', tablefmt='psql')
		return q_result

	def test_q1(self):
		elapsed_time = []
		iterations = [i for i in self.args.test[1:]]
		data_to_plot = []
		labels_to_plot = []
		for iteration in iterations:
			num_test = int(iteration)
			q = "MATCH (u:keyword) WITH u, rand() AS number RETURN u ORDER BY number LIMIT {num_test}"
			pars = {"num_test":num_test}
			resultSet = self.exec_query(q,pars)
			self.logger.info('GraphDBLP: Start Testing on query number 1 for %s times',str(iteration))
			for index, row in resultSet.iterrows():
				s = datetime.datetime.now()
				key = row['u']['key']
				self.args.q1 =[unicode(key), '10'] #get top 10 of most prolific authors
				g.Q1(self.args.q1[0],int(self.args.q1[1]))
				t = datetime.datetime.now()
				sec = t-s
				#self.logger.info("Performed in %s ",str(sec))
				elapsed_time.append(sec.total_seconds())
			print elapsed_time
			
			self.Q_test_results[1] = {
				'avg':st.mean(elapsed_time),
				'min':min(elapsed_time),
				'max':max(elapsed_time),
				'std':st.variance(elapsed_time),
				'median':st.median(elapsed_time)
				}
			self.logger.warning(self.Q_test_results[1])
			data_to_plot.append(np.asarray(elapsed_time))
			labels_to_plot.append("Q1-"+str(iteration))
		plot(str(self.args.test),data_to_plot,labels_to_plot)
		return self.Q_test_results[1]

	def test_q2(self):
		elapsed_time = []
		iterations = [i for i in self.args.test[1:]]
		data_to_plot = []
		labels_to_plot = []
		for iteration in iterations:
			num_test = int(iteration)
			q = "MATCH (u:author) WITH u, rand() AS number RETURN u ORDER BY number LIMIT {num_test}"
			pars = {"num_test":num_test}
			resultSet = self.exec_query(q,pars)
			self.logger.info('GraphDBLP: Start Testing on query number 2 for %s times',str(iteration))
			for index, row in resultSet.iterrows():
				s = datetime.datetime.now()
				name = row['u']['name']
				self.args.q2 =[unicode(name), '3', '0.7'] #get top 3 researchers
				g.Q2(self.args.q2[0],int(self.args.q2[1]),float(self.args.q2[2]))
				t = datetime.datetime.now()
				sec = t-s
				#self.logger.info("Performed in %s ",str(sec))
				elapsed_time.append(sec.total_seconds())
			print elapsed_time
			
			self.Q_test_results[1] = {
				'avg':st.mean(elapsed_time),
				'min':min(elapsed_time),
				'max':max(elapsed_time),
				'std':st.variance(elapsed_time),
				'median':st.median(elapsed_time)
				}
			self.logger.warning(self.Q_test_results[1])
			data_to_plot.append(np.asarray(elapsed_time))
			labels_to_plot.append("Q2-"+str(iteration))
		plot(str(self.args.test),data_to_plot,labels_to_plot)
		return self.Q_test_results[1]

	def test_q3(self):
		elapsed_time = []
		iterations = [i for i in self.args.test[1:]]
		data_to_plot = []
		labels_to_plot = []
		for iteration in iterations:
			num_test = int(iteration)
			q = "MATCH (u:venue) WITH u, rand() AS number RETURN u ORDER BY number LIMIT {num_test}"
			pars = {"num_test":num_test}
			resultSet = self.exec_query(q,pars)
			self.logger.info('GraphDBLP: Start Testing on query number 3 for %s times',str(iteration))
			for index, row in resultSet.iterrows():
				s = datetime.datetime.now()
				name = row['u']['name']
				self.args.q3 =[unicode(name), '1'] #at least 0.5 sim value 
				g.Q3(self.args.q3[0],float(self.args.q3[1]))
				t = datetime.datetime.now()
				sec = t-s
				#self.logger.info("Performed in %s ",str(sec))
				elapsed_time.append(sec.total_seconds())
			print elapsed_time
			
			self.Q_test_results[1] = {
				'avg':st.mean(elapsed_time),
				'min':min(elapsed_time),
				'max':max(elapsed_time),
				'std':st.variance(elapsed_time),
				'median':st.median(elapsed_time)
				}
			self.logger.warning(self.Q_test_results[1])
			data_to_plot.append(np.asarray(elapsed_time))
			labels_to_plot.append("Q3-"+str(iteration))
		plot(str(self.args.test),data_to_plot,labels_to_plot)
		return self.Q_test_results[1]

if __name__ == "__main__":
	q_result = []
	g = GraphDBLP()
	print g.run(tab=True)
	#print g.test_q2(5)
  
	
