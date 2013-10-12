import argparse
import threading
import requests
import time
import os

''' Threaded download accelerator '''
class Downloader:
	def __init__(self):
		''' initialize this object with the number of threads to use to 
		download a given URL '''
		self.num_threads = 1
		self.debug = False
		self.url = ''
		self.out_file = 'index.html'

		# parse the arguments
		self.parse_args()

		# delete the output file (if it already exists)
		if (os.path.isfile(self.out_file)):
			os.remove(self.out_file)

	def parse_args(self):
		''' parse the arguments passed on the command line '''

		# set up the arg-parser
		parser = argparse.ArgumentParser(prog='Download Accelerator',\
			description='A simple script that downloads a file specified by a given URL to the current directory.',\
			add_help=True)

		# add the <num-threads> argument
		parser.add_argument('-n', '--threads', type=str, action='store',\
			help='Specify the number of threads to use to donwload the file specified by the givne URL',\
			default=1)

		# add the <debug> argument
		parser.add_argument('-d', '--debug', type=bool, action='store',\
			help='Turn debug statements on', default=False)

		# add the <URL> argument
		parser.add_argument('url')

		# parse the arguments
		args = parser.parse_args()

		# set the number of threads to use
		self.num_threads = int(args.threads)

		# enable/disable debug mode
		self.debug = args.debug

		# get the URL
		self.url = args.url

		# parse out the name of the destination file
		self.out_file = self.url.split('/')[-1].strip()

		if (self.debug):
			print "Downloader configured to use " + str(self.num_threads) + " threads"
			print "Downloader will download the file located at " + self.url
			print "File will be downloaded as " + self.out_file

	def download(self):
		''' download the file at the given URL '''

		# get the HEADers from the URL
		response = requests.head(self.url)
		if (self.debug):
			print
			print "HTTP Headers:"
			print "============="
			for key in response.headers:
				print key + " = " + response.headers[key]
			print

		# should I check the response status code?

		# get the content length from the headers
		content_length = int(response.headers['content-length'])
		if (self.debug):
			print "Content length: " + str(content_length) + " bytes"

		# compute the number of bytes per thread
		bytes_per_thread = content_length / self.num_threads
		if (self.debug):
			print "Number of bytes per thread: " + str(bytes_per_thread)

		# create the download threads
		try:
			with Timer() as timer:
				threads = []
				for i in range(self.num_threads):
					thread_file = self.out_file + "_part_" + str(i)
					if (self.debug):
						print "Thread %d output file: %s" % (i, thread_file)

					begin_range = i * bytes_per_thread
					if (self.debug):
						print "Thread %d begin range at %d" % (i, begin_range)

					end_range = (i + 1) * bytes_per_thread - 1
					if (self.debug):
						print "Thread %d end range at %d" % (i, end_range)

					remainder = (content_length - 1) - end_range
					if (self.debug):
						print "Thread %d remainder: %d bytes" % (i, remainder)

					if (remainder < bytes_per_thread):
						end_range += remainder
						if (self.debug):
							print "Thread %d end range udpated at %d" % (i, end_range)

					t = DownloaderThread(self.url, begin_range, end_range, thread_file)
					threads.append(t)
					t.start()

				# wait for the threads
				for t in threads:
					t.join()
					with open(self.out_file, 'ab') as final_out_file:
						with open(t.out_file, 'rb') as thread_out_file:
							# read bytes from thread_out_file and write them to final_out_file
							bytes = 'empty'
							while (bytes):
								bytes = thread_out_file.read(512*1024)
								final_out_file.write(bytes)

					# delete the thread's output file
					os.remove(t.out_file)

		finally:
			print "%s %d %d %f" % (self.url, self.num_threads, content_length, timer.interval)

''' Thread class used to download a portion of a file '''
class DownloaderThread(threading.Thread):
	def __init__(self, url, begin_range, end_range, out_file):
		''' initialize the thread with everything it will need to 
		download the data '''
		threading.Thread.__init__(self)
		self.url = url
		self.begin_range = begin_range
		self.end_range = end_range
		self.out_file = out_file

	def run(self):
		''' download the data to the given file '''
		response = requests.get(self.url, headers={'Range' : 'bytes=%s-%s' % (self.begin_range, self.end_range)})
		with open(self.out_file, 'wb') as f:
			f.write(response.content)

''' Timer class for computing execution times '''
class Timer:
	def __enter__(self):
		self.start = time.clock()
		return self

	def __exit__(self, *args):
		self.end = time.clock()
		self.interval = self.end - self.start

if __name__ == '__main__':
	d = Downloader()
	d.download()